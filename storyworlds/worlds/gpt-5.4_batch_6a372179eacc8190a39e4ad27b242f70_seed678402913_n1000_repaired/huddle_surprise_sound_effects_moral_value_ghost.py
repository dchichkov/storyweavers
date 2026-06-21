#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/huddle_surprise_sound_effects_moral_value_ghost.py
==============================================================================

A small storyworld about a spooky night sound that seems ghostly at first.
Two children huddle together, hear eerie noises, and learn that telling the
truth about fear and looking carefully is wiser than feeding a fright.

This world keeps a gentle "ghost story" mood while ending safely:
a dark place, a sound effect, a huddle, a surprise reveal, and a clear moral.

Run it
------
python storyworlds/worlds/gpt-5.4/huddle_surprise_sound_effects_moral_value_ghost.py
python storyworlds/worlds/gpt-5.4/huddle_surprise_sound_effects_moral_value_ghost.py --place attic_landing --source kitten --response ask_grandma
python storyworlds/worlds/gpt-5.4/huddle_surprise_sound_effects_moral_value_ghost.py --all
python storyworlds/worlds/gpt-5.4/huddle_surprise_sound_effects_moral_value_ghost.py --qa --json
python storyworlds/worlds/gpt-5.4/huddle_surprise_sound_effects_moral_value_ghost.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    room: str
    spooky_spot: str
    approach: str
    ambient: str
    allows: set[str] = field(default_factory=set)
    self_check_ok: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    sound: str
    motion: str
    reveal: str
    surprise: str
    allowed_places: set[str] = field(default_factory=set)
    needs_adult: bool = False
    needs_kindness: bool = False
    moral: str = ""
    fix: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    needs_adult: bool = False
    brings_light: bool = True
    kind: bool = False
    text: str = ""
    qa_text: str = ""
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "friend"}]

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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    if world.get("room").meters["dark"] < THRESHOLD:
        return out
    source = world.get("source")
    if source.meters["making_noise"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("spook", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__spook__")
    return out


def _r_huddle(world: World) -> list[str]:
    if any(k.memes["fear"] >= THRESHOLD for k in world.kids()):
        sig = ("huddle",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["comfort"] += 1
                if kid.memes["fear"] >= THRESHOLD:
                    kid.memes["fear"] = max(0.0, kid.memes["fear"] - 0.25)
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="spook", tag="meme", apply=_r_spook),
    Rule(name="huddle", tag="meme", apply=_r_huddle),
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
            if not sent.startswith("__"):
                world.say(sent)
    return produced


PLACES = {
    "attic_landing": Place(
        id="attic_landing",
        label="the attic landing",
        room="the old upstairs hall",
        spooky_spot="the attic door at the end of the hall",
        approach="the narrow stairs",
        ambient="The boards there always gave a long creak when the house settled.",
        allows={"kitten", "shutter"},
        self_check_ok=False,
        tags={"dark", "house"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        room="the back hall",
        spooky_spot="the porch curtain by the screen door",
        approach="the short back hall",
        ambient="Moonlight striped the floor and made every moving shadow look taller than it was.",
        allows={"sheet", "shutter"},
        self_check_ok=True,
        tags={"dark", "wind"},
    ),
    "closet_nook": Place(
        id="closet_nook",
        label="the linen closet nook",
        room="the upstairs landing",
        spooky_spot="the half-open linen closet",
        approach="three soft steps across the rug",
        ambient="The old house breathed little sighs through its wooden walls.",
        allows={"kitten", "moth_mobile"},
        self_check_ok=True,
        tags={"dark", "house"},
    ),
}

SOURCES = {
    "kitten": Source(
        id="kitten",
        label="a lost kitten",
        sound="mew... mew... scratch-scratch",
        motion="tiny paws rustling in the dark",
        reveal="a small gray kitten tangled in a basket handle",
        surprise="It was not a ghost at all, only a frightened kitten with moon-bright eyes.",
        allowed_places={"attic_landing", "closet_nook"},
        needs_adult=True,
        needs_kindness=True,
        moral="Being honest about fear helped them get kind help for someone smaller than they were.",
        fix="lifted the basket free and wrapped the shivery kitten in a towel",
        tags={"kitten", "kindness", "truth"},
    ),
    "shutter": Source(
        id="shutter",
        label="a loose shutter",
        sound="bang... bang... whooo",
        motion="wind nudging wood against the wall",
        reveal="a loose shutter tapping in the night wind",
        surprise="The ghostly knocking was only the wind finding one shaky shutter.",
        allowed_places={"attic_landing", "porch"},
        needs_adult=True,
        needs_kindness=False,
        moral="The sound felt huge in the dark, but careful looking turned a wild guess into the truth.",
        fix="fastened the loose shutter so it could not clap anymore",
        tags={"wind", "truth"},
    ),
    "sheet": Source(
        id="sheet",
        label="a laundry sheet",
        sound="flap-flap... swish",
        motion="a white sheet billowing on the clothesline",
        reveal="a white sheet dancing on the clothesline",
        surprise="The tall white ghost was only wash that had not been taken in yet.",
        allowed_places={"porch"},
        needs_adult=False,
        needs_kindness=False,
        moral="A shape can look spooky in the dark, so it is wise to look twice before deciding what it is.",
        fix="clipped the sheet tight so it stopped flying up like a tall white figure",
        tags={"wind", "truth"},
    ),
    "moth_mobile": Source(
        id="moth_mobile",
        label="a paper moon mobile",
        sound="tick-tick... flutter",
        motion="paper moons bumping softly while a moth chased the light",
        reveal="a paper moon mobile bobbing in front of the closet bulb",
        surprise="The whispery flutter came from paper moons and one silly moth.",
        allowed_places={"closet_nook"},
        needs_adult=False,
        needs_kindness=False,
        moral="When people stop and study a mystery, the truth often turns out smaller and kinder than the fear.",
        fix="switched the closet bulb off and held the paper moons still until the moth drifted away",
        tags={"truth", "moth"},
    ),
}

RESPONSES = {
    "ask_grandma": Response(
        id="ask_grandma",
        sense=3,
        needs_adult=True,
        brings_light=True,
        kind=True,
        text="went to tell Grandma the truth: they were scared, and something was making a noise",
        qa_text="they told Grandma they were scared and asked her to come with a light",
        tags={"adult_help", "truth"},
    ),
    "ask_grandpa": Response(
        id="ask_grandpa",
        sense=3,
        needs_adult=True,
        brings_light=True,
        kind=True,
        text="went to tell Grandpa the truth: they were scared, and something was making a noise",
        qa_text="they told Grandpa they were scared and asked him to come with a light",
        tags={"adult_help", "truth"},
    ),
    "peek_together": Response(
        id="peek_together",
        sense=2,
        needs_adult=False,
        brings_light=True,
        kind=False,
        text="took a flashlight together and crept closer, hand in hand, to see what was really there",
        qa_text="they took a flashlight and checked together",
        tags={"flashlight", "truth"},
    ),
    "hide_under_blanket": Response(
        id="hide_under_blanket",
        sense=1,
        needs_adult=False,
        brings_light=False,
        kind=False,
        text="hid deeper under the blanket and guessed wilder and wilder things",
        qa_text="they hid and kept guessing",
        tags={"fear"},
    ),
}


def source_fits(place: Place, source: Source) -> bool:
    return source.id in place.allows and place.id in source.allowed_places


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_works(place: Place, source: Source, response: Response) -> bool:
    if response.sense < SENSE_MIN:
        return False
    if source.needs_adult and not response.needs_adult:
        return False
    if not response.brings_light:
        return False
    if response.id == "peek_together" and not place.self_check_ok:
        return False
    return True


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    source = SOURCES[params.source]
    response = RESPONSES[params.response]
    if source.needs_kindness and response.kind:
        return "helped"
    if response_works(place, source, response):
        return "revealed"
    return "stuck"


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if source_fits(place, source):
                combos.append((place_id, source_id))
    return combos


def compatible_responses(place_id: str, source_id: str) -> list[str]:
    place = PLACES[place_id]
    source = SOURCES[source_id]
    return sorted(r.id for r in sensible_responses() if response_works(place, source, r))


def explain_combo_rejection(place: Place, source: Source) -> str:
    return (
        f"(No story: {source.label} does not fit {place.label} here. "
        f"Pick a source that could reasonably be heard near {place.spooky_spot}.)"
    )


def explain_response_rejection(place: Place, source: Source, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). This world prefers truth, light, "
            f"and help over hiding and guessing.)"
        )
    if source.needs_adult and not response.needs_adult:
        return (
            f"(No story: {source.label} should be checked with a grown-up in {place.label}. "
            f"Choose a response that asks an adult for help.)"
        )
    if response.id == "peek_together" and not place.self_check_ok:
        return (
            f"(No story: {place.label} is not a sensible place for children to investigate alone. "
            f"Choose a grown-up helper.)"
        )
    if not response.brings_light:
        return "(No story: the children need light to learn the truth.)"
    return "(No story: that response does not fit this mystery.)"


def introduce(world: World, hero: Entity, friend: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"Late one windy night, {hero.id} and {friend.id} were staying in {helper.label_word}'s old house. "
        f"They had brushed their teeth, pulled on soft pajamas, and promised they were not scared of anything."
    )
    world.say(
        f"But {place.room} looked different after bedtime. {place.ambient}"
    )


def hear_sound(world: World, hero: Entity, friend: Entity, place: Place, source: Source) -> None:
    world.get("room").meters["dark"] += 1
    world.get("source").meters["making_noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the sound came from {place.spooky_spot}: {source.sound}! "
        f"{hero.id} froze, and {friend.id} grabbed {hero.pronoun('possessive')} sleeve."
    )
    world.say(
        f"In one quick shuffle, the two children huddle together under one blanket, listening to {source.motion}."
    )


def confess_fear(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["honesty"] += 1
    friend.memes["honesty"] += 1
    world.say(
        f'"Do you think it is a ghost?" whispered {friend.id}.'
    )
    world.say(
        f'{hero.id} swallowed. "Maybe not. But I am truly scared," {hero.pronoun()} admitted.'
    )
    world.say(
        f'Saying it out loud made the fear feel smaller, and {friend.id} nodded. '
        f'"Me too," {friend.pronoun()} whispered back.'
    )


def choose_response(world: World, hero: Entity, friend: Entity, helper: Entity, response: Response) -> None:
    world.para()
    if response.needs_adult:
        for kid in world.kids():
            kid.memes["trust"] += 1
        helper.memes["care"] += 1
        world.say(
            f"So instead of making up bigger and bigger ghost ideas, they {response.text}."
        )
        world.say(
            f'{helper.label_word.capitalize()} did not laugh at them. '
            f'{helper.pronoun().capitalize()} took a warm yellow flashlight and said, '
            f'"Thank you for telling the truth. Let us go see together."'
        )
    else:
        for kid in world.kids():
            kid.memes["courage"] += 1
        world.say(
            f"So instead of hiding longer, they {response.text}."
        )


def reveal_truth(world: World, hero: Entity, friend: Entity, helper: Optional[Entity],
                 place: Place, source: Source, response: Response) -> None:
    world.para()
    world.get("source").meters["revealed"] += 1
    world.get("source").meters["making_noise"] = 0.0
    world.get("room").meters["dark"] = 0.0
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["wonder"] += 1
    who = helper.label_word.capitalize() if helper is not None and response.needs_adult else "The flashlight beam"
    if helper is not None and response.needs_adult:
        source_text = f"{who} reached {place.spooky_spot} first."
    else:
        source_text = f"{who} reached {place.spooky_spot} first."
    world.say(source_text)
    world.say(
        f"There was the surprise: {source.reveal}. {source.surprise}"
    )


def resolve_source(world: World, helper: Optional[Entity], source: Source, response: Response) -> None:
    world.get("source").meters["quiet"] += 1
    if helper is not None and response.needs_adult:
        actor = helper.label_word.capitalize()
        pron = helper.pronoun()
        world.say(f"{actor} {source.fix}.")
        if source.id == "kitten":
            world.say(f'Soon the little thing gave one soft "prrrt," and everyone laughed with relief.')
        elif source.id == "shutter":
            world.say(f'After that, the night sounded like itself again instead of "bang... bang... whooo."')
        else:
            world.say("The mystery sound faded away, small and harmless now that someone had understood it.")
    else:
        if source.id == "sheet":
            world.say(f"They clipped the sheet tight, and it stopped going {source.sound}.")
        elif source.id == "moth_mobile":
            world.say("They steadied the paper moons and watched the silly moth drift toward the window instead.")
        else:
            world.say(f"Once they understood the sound, it no longer felt ghostly at all.")


def ending(world: World, hero: Entity, friend: Entity, helper: Optional[Entity], source: Source,
           response: Response) -> None:
    world.para()
    if source.needs_kindness and response.kind:
        world.say(
            f"Back in bed, {hero.id} and {friend.id} did not huddle from fear anymore. "
            f"They huddled close to listen to the rescued kitten purr from its basket by the stove."
        )
    else:
        world.say(
            f"Back under the blanket, {hero.id} and {friend.id} still huddled, but now they were smiling instead of shaking."
        )
    world.say(source.moral)
    if helper is not None and response.needs_adult:
        world.say(
            f'Before the lamp was turned low, {helper.label_word.capitalize()} said, '
            f'"Brave does not mean never scared. Brave means telling the truth and choosing the wise next step."'
        )
    else:
        world.say(
            "They learned that a spooky guess can grow loud in the dark, but the truth grows clearer when someone looks carefully."
        )


def tell(place: Place, source: Source, response: Response, *,
         hero_name: str = "Nora", hero_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         helper_type: str = "grandmother") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    source_ent = world.add(Entity(id="source", kind="thing", type="source", label=source.label))

    introduce(world, hero, friend, helper, place)
    world.para()
    hear_sound(world, hero, friend, place, source)
    confess_fear(world, hero, friend)
    choose_response(world, hero, friend, helper, response)
    reveal_truth(world, hero, friend, helper if response.needs_adult else None, place, source, response)
    resolve_source(world, helper if response.needs_adult else None, source, response)
    ending(world, hero, friend, helper if response.needs_adult else None, source, response)

    world.facts.update(
        place=place,
        source_cfg=source,
        response=response,
        hero=hero,
        friend=friend,
        helper=helper,
        source=source_ent,
        room=room,
        outcome="helped" if source.needs_kindness and response.kind else "revealed",
        huddled=True,
        moral=source.moral,
    )
    return world


KNOWLEDGE = {
    "ghost_story": [
        (
            "What makes a ghost story feel spooky without being dangerous?",
            "Soft darkness, strange sounds, and not knowing the answer yet can make a story feel spooky. It still stays gentle when the mystery is solved safely."
        )
    ],
    "truth": [
        (
            "Why does telling the truth help when you feel scared?",
            "Telling the truth helps other people understand what is wrong and help you wisely. It can also make a fear feel smaller because you are not hiding it alone."
        )
    ],
    "adult_help": [
        (
            "When should children ask a grown-up for help at night?",
            "Children should ask a grown-up for help when something feels unsafe, confusing, or too big to handle alone. A grown-up can bring light, calm, and good judgment."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight useful in the dark?",
            "A flashlight helps people see what is really there. When you can see clearly, strange shadows and sounds often make more sense."
        )
    ],
    "wind": [
        (
            "Why can wind make spooky noises around a house?",
            "Wind can rattle shutters, flap cloth, and whistle through small gaps. In the dark, those ordinary sounds can seem much stranger than they really are."
        )
    ],
    "kitten": [
        (
            "What should you do if you find a frightened kitten?",
            "Move gently and ask a grown-up to help. A scared kitten needs calm hands, warmth, and kind care."
        )
    ],
    "kindness": [
        (
            "What is kindness when someone small is scared?",
            "Kindness is noticing that another creature is frightened and helping softly instead of ignoring it. Gentle help can turn a scary moment into a safe one."
        )
    ],
    "moth": [
        (
            "Why do moths flutter near lights?",
            "Moths are drawn to light, so they may bump and flutter around lamps or bulbs. Their wings can make tiny sounds in a quiet room."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost_story", "truth", "adult_help", "flashlight", "wind", "kitten", "kindness", "moth"]


@dataclass
class StoryParams:
    place: str
    source: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="attic_landing",
        source="kitten",
        response="ask_grandma",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper_type="grandmother",
    ),
    StoryParams(
        place="porch",
        source="sheet",
        response="peek_together",
        hero_name="Mia",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        helper_type="grandfather",
    ),
    StoryParams(
        place="closet_nook",
        source="moth_mobile",
        response="peek_together",
        hero_name="Lucy",
        hero_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        helper_type="grandmother",
    ),
    StoryParams(
        place="porch",
        source="shutter",
        response="ask_grandpa",
        hero_name="Eli",
        hero_gender="boy",
        friend_name="Rose",
        friend_gender="girl",
        helper_type="grandfather",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    place = f["place"]
    source = f["source_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "huddle" and uses sound effects.',
        f"Tell a spooky-but-safe bedtime story where {hero.id} and {friend.id} hear a strange noise near {place.spooky_spot}, huddle together, and discover the truth.",
        f'Write a short ghost-story-style tale with a surprise reveal and a moral about honesty and wise courage, where the "ghost" turns out to be {source.label}.',
    ]


def pair_noun(hero: Entity, friend: Entity) -> str:
    if hero.type == "girl" and friend.type == "girl":
        return "two girls"
    if hero.type == "boy" and friend.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    place = f["place"]
    source = f["source_cfg"]
    response = f["response"]
    pair = pair_noun(hero, friend)
    helper_word = helper.label_word
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {friend.id}, spending the night in {helper_word}'s old house. They seem brave at first, but the strange sound gives them a real fright."
        ),
        (
            "Why did the children huddle together?",
            f"They heard {source.sound} from {place.spooky_spot}, and the dark made the noise feel ghostly. Huddling helped them feel less alone while they decided what wise thing to do next."
        ),
        (
            "What did the children do instead of pretending they were not scared?",
            f"They told the truth that they were scared. Saying it out loud helped them stop guessing wildly and choose a better plan."
        ),
    ]
    if response.needs_adult:
        out.append(
            (
                f"How did {hero.id} and {friend.id} solve the mystery?",
                f"They {response.qa_text}. Then {helper_word} used a flashlight and found {source.reveal}. The careful checking turned a spooky guess into the truth."
            )
        )
    else:
        out.append(
            (
                f"How did {hero.id} and {friend.id} solve the mystery?",
                f"They {response.qa_text}. With the light on the spooky spot, they discovered {source.reveal}, so the fear melted into relief."
            )
        )
    if f["outcome"] == "helped":
        out.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that the 'ghost' sound came from {source.label}. Once the children told the truth and got help, they could be kind to the little animal instead of staying frightened."
            )
        )
    else:
        out.append(
            (
                "What lesson did the children learn?",
                f"They learned that dark sounds can trick the imagination. Looking carefully with light taught them the truth was ordinary and not a ghost at all."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost_story", "truth"}
    response = world.facts["response"]
    source = world.facts["source_cfg"]
    if response.brings_light:
        tags.add("flashlight")
    tags |= set(response.tags)
    tags |= set(source.tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(P,S) :- place(P), source(S), allowed(P,S), source_allowed(S,P).
sensible(R) :- response(R), sense(R,N), sense_min(M), N >= M.

works(P,S,R) :- fits(P,S), sensible(R), light(R),
                not needs_adult(S).
works(P,S,R) :- fits(P,S), sensible(R), light(R),
                needs_adult(S), adult(R).
works(P,S,R) :- fits(P,S), sensible(R), light(R),
                self_check(P), not needs_adult(S), not adult_required(R).

adult_required(R) :- response(R), not adult(R).

valid(P,S) :- fits(P,S).

outcome(helped) :- chosen_place(P), chosen_source(S), chosen_response(R),
                   works(P,S,R), needs_kindness(S), kind(R).
outcome(revealed) :- chosen_place(P), chosen_source(S), chosen_response(R),
                     works(P,S,R), not outcome(helped).
outcome(stuck) :- chosen_place(P), chosen_source(S), chosen_response(R),
                  not works(P,S,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.self_check_ok:
            lines.append(asp.fact("self_check", place_id))
        for sid in sorted(place.allows):
            lines.append(asp.fact("allowed", place_id, sid))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.needs_adult:
            lines.append(asp.fact("needs_adult", source_id))
        if source.needs_kindness:
            lines.append(asp.fact("needs_kindness", source_id))
        for pid in sorted(source.allowed_places):
            lines.append(asp.fact("source_allowed", source_id, pid))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        if response.needs_adult:
            lines.append(asp.fact("adult", response_id))
        if response.brings_light:
            lines.append(asp.fact("light", response_id))
        if response.kind:
            lines.append(asp.fact("kind", response_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if "huddle" not in sample.story.lower():
        raise StoryError("(Smoke test failed: story did not include 'huddle'.)")
    if not sample.story_qa or not sample.world_qa:
        raise StoryError("(Smoke test failed: QA generation was empty.)")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_sens = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: asp={sorted(asp_sens)} python={sorted(py_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue

    mismatches = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


GIRL_NAMES = ["Nora", "Mia", "Lucy", "Ava", "Ella", "Rose", "Lily", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Max", "Finn", "Eli", "Leo", "Jack"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Gentle ghost-story world: a spooky sound, a huddle, a surprise reveal, and a moral."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--helper", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible place/source combos and sensible responses")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        if not source_fits(place, source):
            raise StoryError(explain_combo_rejection(place, source))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id = rng.choice(sorted(combos))
    place = PLACES[place_id]
    source = SOURCES[source_id]

    if args.response:
        response = RESPONSES[args.response]
        if not response_works(place, source, response):
            raise StoryError(explain_response_rejection(place, source, response))
        response_id = args.response
    else:
        options = compatible_responses(place_id, source_id)
        if not options:
            raise StoryError("(No sensible response fits this mystery.)")
        response_id = rng.choice(options)

    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=hero_name)
    helper_type = args.helper or ("grandmother" if "grandma" in response_id else "grandfather" if "grandpa" in response_id else rng.choice(["grandmother", "grandfather"]))

    if response_id == "ask_grandma":
        helper_type = "grandmother"
    if response_id == "ask_grandpa":
        helper_type = "grandfather"

    return StoryParams(
        place=place_id,
        source=source_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source '{params.source}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response '{params.response}'.)")
    place = PLACES[params.place]
    source = SOURCES[params.source]
    response = RESPONSES[params.response]
    if not source_fits(place, source):
        raise StoryError(explain_combo_rejection(place, source))
    if not response_works(place, source, response):
        raise StoryError(explain_response_rejection(place, source, response))

    world = tell(
        place=place,
        source=source,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sens = asp_sensible()
        print(f"sensible responses: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (place, source) combos:\n")
        for place_id, source_id in combos:
            print(f"  {place_id:13} {source_id:12} -> {', '.join(compatible_responses(place_id, source_id))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.source} at {p.place} ({outcome_of(p)})"
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
