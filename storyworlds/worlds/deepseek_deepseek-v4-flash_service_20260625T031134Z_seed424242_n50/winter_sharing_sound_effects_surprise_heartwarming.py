#!/usr/bin/env python3
"""
storyworlds/worlds/winter_sharing_sound_effects_surprise_heartwarming.py
========================================================================

A standalone story world sketch for a heartwarming winter tale about sharing
sound effects and surprises.  The world simulates: a cold winter day, a child
who discovers a special sound-making gift, a friend who shares something
unexpected, and a warm surprise that follows.

Initial story (used to build a world model):
---
Once upon a time, there was a little cheerful boy named Leo. He loved playing
outside in the snow. One winter morning, Leo's grandma sent him a special gift
wrapped in sparkly paper. Leo opened it and found a set of jingle bells that
made the most wonderful sound when you shook them.

Leo ran outside to play in the snow with his bells. He shook them and they
went "jingle jingle jingle!" The sound made the whole snowy yard feel like a
music box. Leo's friend Mia came over and heard the bells. "Those sound
lovely!" she said. Leo smiled and shared his bells with Mia.

They shook the bells together and laughed. But then Leo noticed that Mia
looked a little sad. "What's wrong?" Leo asked. Mia shrugged. "I don't have
anything that makes such a pretty sound," she said.

Leo thought for a moment. Then he had an idea. He ran inside and came back
with a cardboard tube. "Try this!" he said. Mia put it to her ear and heard
the wind whistle through it. She smiled. Then Leo showed her how to tap the
tube on the snow, making a soft "thump thump" sound. Mia's face lit up.

"Now we have two sounds!" Mia said. They spent the whole afternoon making
snow music together: jingle bells and cardboard tubes and clapping snow. When
they went inside for hot cocoa, Leo's grandma called on the phone. "Did you
like your surprise?" she asked. Leo told her all about their snow orchestra,
and grandma laughed with joy.

Causal state updates:
---
    share item                   -> owner.joy += 1, receiver.joy += 1, owner.memes["generosity"] += 1
    make sound effect            -> maker.joy += 1, listener.joy += 0.5
    receive surprise             -> receiver.joy += 2, receiver.memes["surprise"] += 1
    warm drink after cold play   -> actor.meters["warmth"] += 1, actor.memes["comfort"] += 1
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

SOUND_KINDS = {"jingle", "thump", "whistle", "crunch", "tap"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    held_by: Optional[str] = None
    sound: Optional[str] = None
    warm: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandma", "woman"}
        male = {"boy", "father", "grandpa", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"grandma": "grandma", "grandpa": "grandpa"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the snowy yard"
    indoor: bool = False
    weather: str = "snowy"
    affords: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    verb: str
    gerund: str
    onomatopoeia: str
    maker: str
    warmth: float = 0.0


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    kind: str
    sound: Optional[str] = None
    warm: bool = False


@dataclass
class SharingItem:
    id: str
    label: str
    phrase: str
    sound: Optional[str] = None
    plural: bool = False
    shareable: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = setting.weather
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def held_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sharing_joy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["shared"] < THRESHOLD:
            continue
        for item in world.held_items(actor):
            if item.owner and item.owner != actor.id:
                sig = ("shared_joy", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                actor.memes["joy"] += 1
                owner = world.get(item.owner)
                owner.memes["joy"] += 1
                owner.memes["generosity"] += 1
                out.append(f"Sharing the {item.label} made both of them smile.")
    return out


def _r_sound_joy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["made_sound"] < THRESHOLD:
            continue
        sig = ("sound_joy", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        for other in world.characters():
            if other.id != actor.id:
                other.memes["joy"] += 0.5
        out.append("The sound made everyone feel cheerful.")
    return out


def _r_surprise_joy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["surprise"] < THRESHOLD:
            continue
        sig = ("surprise_joy", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 2
        out.append(f"{actor.id} felt so happy about the surprise!")
    return out


def _r_warmth_comfort(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["warmth"] < THRESHOLD:
            continue
        sig = ("warmth", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["comfort"] += 1
        out.append(f"Warmth spread through {actor.id}'s whole body.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sharing_joy", tag="social", apply=_r_sharing_joy),
    Rule(name="sound_joy", tag="social", apply=_r_sound_joy),
    Rule(name="surprise_joy", tag="emotional", apply=_r_surprise_joy),
    Rule(name="warmth_comfort", tag="physical", apply=_r_warmth_comfort),
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
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _make_sound(world: World, actor: Entity, sound: str, item: Entity) -> None:
    actor.memes["made_sound"] += 1
    item.meters["sound_made"] += 1
    propagate(world, narrate=True)


def _share_item(world: World, giver: Entity, receiver: Entity, item: Entity) -> None:
    giver.memes["shared"] += 1
    item.held_by = receiver.id
    propagate(world, narrate=True)


def _receive_surprise(world: World, receiver: Entity, item: Entity) -> None:
    receiver.memes["surprise"] += 1
    item.held_by = receiver.id
    propagate(world, narrate=True)


def _drink_warm(world: World, actor: Entity) -> None:
    actor.meters["warmth"] += 1
    propagate(world, narrate=True)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved winter mornings.")


def loves_snow(world: World, hero: Entity) -> None:
    hero.memes["love_snow"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved playing outside in the snow; the crunch underfoot was like music.")


def receive_gift(world: World, hero: Entity, giver: Entity, gift: Entity) -> None:
    world.say(f"One winter morning, {hero.id}'s {giver.label_word} sent {hero.pronoun('object')} a special gift wrapped in sparkly paper.")
    world.say(f"{hero.id} opened it and found {gift.phrase}.")


def love_gift(world: World, hero: Entity, gift: Entity) -> None:
    gift.held_by = hero.id
    hero.memes["joy"] += 1
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {gift.label} and held {gift.it()} tight.")


def go_outside(world: World, hero: Entity, friend: Entity) -> None:
    world.say(f"{hero.id} ran outside to play in the snow with {hero.pronoun('possessive')} {gift.label}.")
    world.say(f"The cold air made {hero.pronoun('possessive')} cheeks rosy.")


def make_sound(world: World, hero: Entity, gift: Entity, sound_effect: SoundEffect) -> None:
    _make_sound(world, hero, sound_effect.id, gift)
    world.say(f"{hero.pronoun().capitalize()} {sound_effect.verb} and it went '{sound_effect.onomatopoeia}!'")
    world.say(f"The sound made the whole {world.setting.place} feel like a music box.")


def meet_friend(world: World, hero: Entity, friend: Entity, gift: Entity) -> None:
    friend.memes["joy"] += 0.5
    world.say(f"{hero.id}'s friend {friend.id} came over and heard the {gift.label}.")
    world.say(f'"Those sound lovely!" {friend.id} said.')


def share(world: World, giver: Entity, receiver: Entity, item: Entity) -> None:
    _share_item(world, giver, receiver, item)
    world.say(f"{giver.id} smiled and shared {giver.pronoun('possessive')} {item.label} with {receiver.id}.")
    world.say(f"They {item.sound} together and laughed.")


def notice_sad(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["sad"] += 1
    world.say(f"But then {hero.id} noticed that {friend.id} looked a little sad.")
    world.say(f'"What\'s wrong?" {hero.id} asked.')
    world.say(f'{friend.id} shrugged. "I don\'t have anything that makes such a pretty sound," {friend.pronoun()} said.')


def have_idea(world: World, hero: Entity) -> None:
    hero.memes["idea"] += 1
    world.say(f"{hero.id} thought for a moment. Then {hero.pronoun()} had an idea.")


def make_improvised_sound(world: World, maker: Entity, item: Entity, sound_effect: SoundEffect) -> None:
    _make_sound(world, maker, sound_effect.id, item)
    world.say(f'{maker.pronoun().capitalize()} ran inside and came back with {item.phrase}.')
    world.say(f'"Try this!" {maker.pronoun()} said.')
    world.say(f'{maker.id} showed {maker.pronoun('possessive')} friend how to {sound_effect.verb}, making a soft "{sound_effect.onomatopoeia}" sound.')


def friend_happy(world: World, friend: Entity) -> None:
    friend.memes["joy"] += 1
    friend.memes["sad"] = 0.0
    world.say(f"{friend.id}'s face lit up.")


def play_together(world: World, hero: Entity, friend: Entity, gift: Entity, improvised: Entity) -> None:
    world.say(f'"Now we have two sounds!" {friend.id} said.')
    world.say(f"They spent the whole afternoon making snow music together: {gift.sound} and {improvised.sound} and clapping snow.")


def go_inside(world: Entity, hero: Entity, friend: Entity) -> None:
    world.say(f"When they went inside for hot cocoa, {hero.id}'s grandma called on the phone.")
    world.say(f'"Did you like your surprise?" she asked.')
    world.say(f"{hero.id} told her all about their snow orchestra, and grandma laughed with joy.")
    _drink_warm(world, hero)
    _drink_warm(world, friend)


def tell(setting: Setting, sounds: list[SoundEffect], surprises: list[Surprise],
         sharing_items: list[SharingItem],
         hero_name: str = "Leo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         friend_name: str = "Mia", friend_type: str = "girl",
         giver_type: str = "grandma") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "kind"]),
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        traits=["little", "curious"],
    ))
    giver = world.add(Entity(
        id=giver_type.capitalize(), kind="character", type=giver_type,
        label=f"the {giver_type}",
    ))

    gift_item = sharing_items[0]
    gift = world.add(Entity(
        id="gift", kind="thing", type="gift", label=gift_item.label,
        phrase=gift_item.phrase, owner=hero.id,
        sound=gift_item.sound, plural=gift_item.plural,
    ))

    improvised_item = sharing_items[1] if len(sharing_items) > 1 else sharing_items[0]
    improvised = world.add(Entity(
        id="improvised", kind="thing", type="toy", label=improvised_item.label,
        phrase=improvised_item.phrase, sound=improvised_item.sound,
        plural=improvised_item.plural,
    ))

    main_sound = next(s for s in sounds if s.id == gift_item.sound)
    improvised_sound = next(s for s in sounds if s.id == improvised_item.sound)

    # Act 1: Setup
    introduce(world, hero)
    loves_snow(world, hero)
    receive_gift(world, hero, giver, gift)
    love_gift(world, hero, gift)

    # Act 2: Conflict and sharing
    world.para()
    go_outside(world, hero, friend)
    make_sound(world, hero, gift, main_sound)
    meet_friend(world, hero, friend, gift)
    share(world, hero, friend, gift)
    notice_sad(world, hero, friend)

    # Act 3: Resolution
    world.para()
    have_idea(world, hero)
    make_improvised_sound(world, hero, improvised, improvised_sound)
    friend_happy(world, friend)
    play_together(world, hero, friend, gift, improvised)
    go_inside(world, hero, friend)

    world.facts.update(hero=hero, friend=friend, giver=giver, gift=gift,
                       improvised=improvised, main_sound=main_sound,
                       improvised_sound=improvised_sound,
                       setting=setting, sounds=sounds,
                       sharing_items=sharing_items)
    return world


SETTINGS = {
    "snowy_yard": Setting(place="the snowy yard", weather="snowy", affords={"jingle", "thump", "crunch"}),
    "snowy_park": Setting(place="the snowy park", weather="snowy", affords={"jingle", "whistle", "crunch"}),
    "winter_garden": Setting(place="the winter garden", weather="snowy", affords={"jingle", "tap", "crunch"}),
    "snowy_hill": Setting(place="the snowy hill", weather="snowy", affords={"jingle", "thump", "whistle"}),
}

SOUND_EFFECTS = {
    "jingle": SoundEffect(id="jingle", verb="shook the bells", gerund="shaking bells",
                          onomatopoeia="jingle jingle jingle", maker="bells"),
    "thump": SoundEffect(id="thump", verb="tapped the tube", gerund="tapping tubes",
                         onomatopoeia="thump thump", maker="tube"),
    "whistle": SoundEffect(id="whistle", verb="blew through the tube", gerund="whistling",
                           onomatopoeia="woooosh", maker="tube"),
    "crunch": SoundEffect(id="crunch", verb="stepped on the snow", gerund="crunching snow",
                          onomatopoeia="crunch crunch", maker="snow"),
    "tap": SoundEffect(id="tap", verb="tapped the ice", gerund="tapping ice",
                       onomatopoeia="tap tap tap", maker="ice"),
}

SURPRISES = {
    "gift_bells": Surprise(id="gift_bells", label="jingle bells",
                           phrase="a set of jingle bells that made the most wonderful sound",
                           kind="gift", sound="jingle"),
    "phone_call": Surprise(id="phone_call", label="phone call",
                           phrase="a phone call from grandma", kind="call"),
}

SHARING_ITEMS = {
    "bells": SharingItem(id="bells", label="jingle bells",
                         phrase="a set of jingle bells that made the most wonderful sound",
                         sound="jingle", plural=True, shareable=True),
    "tube": SharingItem(id="tube", label="cardboard tube",
                        phrase="a cardboard tube", sound="whistle",
                        plural=False, shareable=True),
    "drum": SharingItem(id="drum", label="snow drum",
                        phrase="an old pot that made a drum sound",
                        sound="thump", plural=False, shareable=True),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Tim", "Ben", "Max", "Sam", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["playful", "curious", "kind", "cheerful", "spirited", "generous"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for sound_id in setting.affords:
            sound = SOUND_EFFECTS[sound_id]
            for item_id, item in SHARING_ITEMS.items():
                if item.sound == sound_id:
                    for surprise_id in SURPRISES:
                        combos.append((place, sound_id, item_id, surprise_id))
    return combos


@dataclass
class StoryParams:
    place: str
    sound_effect: str
    sharing_item: str
    surprise: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    giver: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "snow": [("What is snow?",
              "Snow is frozen water that falls from clouds in tiny white flakes when it is cold outside.")],
    "jingle": [("What makes a jingle sound?",
                "Jingle bells are small metal bells that ring when you shake them, making a bright jingling sound.")],
    "whistle": [("How does a cardboard tube make sound?",
                 "When you blow through a cardboard tube, the air vibrates inside and makes a whistling or whooshing sound.")],
    "sharing": [("Why is sharing nice?",
                 "When you share something, both people can enjoy it together, and it makes everyone feel happy.")],
    "surprise": [("What is a surprise?",
                  "A surprise is something nice that you do not expect to happen, like a gift or a phone call.")],
    "warmth": [("Why does hot cocoa feel good after playing in the snow?",
                "Hot cocoa warms your body from the inside after you have been cold outside, and it tastes yummy too.")],
    "sound": [("How do you make sounds with snow?",
               "You can make sounds with snow by stepping on it to crunch, patting it to thump, or shaking it gently.")],
}
KNOWLEDGE_ORDER = ["snow", "jingle", "whistle", "sharing", "surprise", "warmth", "sound"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    gift = f["gift"]
    improvised = f["improvised"]
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "sharing sound effects in winter" that includes the word "snow".',
        f"Tell a gentle story where {hero.id} shares {gift.sound} with {friend.id} and they discover a surprising new sound together.",
        f'Write a simple story that uses the words "surprise" and "sharing" and ends with a warm drink after playing in the snow.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    giver = f["giver"]
    gift = f["gift"]
    improvised = f["improvised"]
    main_sound = f["main_sound"]
    improvised_sound = f["improvised_sound"]
    place = world.setting.place
    pos = hero.pronoun("possessive")
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")
    f_pos = friend.pronoun("possessive")
    f_sub = friend.pronoun("subject")

    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {hero.id} plays in {place} with {gift.label}?",
            answer=f"It is about a little {hero.type} named {hero.id} and {pos} friend {friend.id}. They play in {place} on a snowy winter day.",
        ),
        QAItem(
            question=f"What did {hero.id} receive that could make a sound?",
            answer=f"{hero.id} received {gift.phrase} from {pos} {giver.label_word}. When {sub} shook them, they went '{main_sound.onomatopoeia}.'",
        ),
        QAItem(
            question=f"Why did {friend.id} feel sad at first?",
            answer=f"{friend.id} felt sad because {f_sub} did not have anything that made such a pretty sound like {hero.id}'s {gift.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} cheer up {friend.id}?",
            answer=f"{hero.id} found {improvised.phrase} and showed {friend.id} how to make a '{improvised_sound.onomatopoeia}' sound. Then they played together.",
        ),
        QAItem(
            question=f"What surprise happened at the end of the story?",
            answer=f"When they went inside for hot cocoa, {pos} {giver.label_word} called on the phone to ask if {sub} liked the surprise. {hero.id} told {obj} about their snow orchestra.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"snow", "sharing", "surprise", "warmth", "sound"}
    if world.facts["gift"].sound:
        tags.add(world.facts["gift"].sound)
    if world.facts["improvised"].sound:
        tags.add(world.facts["improvised"].sound)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.sound:
            bits.append(f"sound={e.sound}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="snowy_yard", sound_effect="jingle", sharing_item="bells",
        surprise="gift_bells", hero_name="Leo", hero_type="boy",
        friend_name="Mia", friend_type="girl", giver="grandma", trait="playful",
    ),
    StoryParams(
        place="snowy_park", sound_effect="whistle", sharing_item="tube",
        surprise="phone_call", hero_name="Lily", hero_type="girl",
        friend_name="Sam", friend_type="boy", giver="grandpa", trait="curious",
    ),
    StoryParams(
        place="winter_garden", sound_effect="thump", sharing_item="drum",
        surprise="gift_bells", hero_name="Max", hero_type="boy",
        friend_name="Zoe", friend_type="girl", giver="grandma", trait="kind",
    ),
]


ASP_RULES = r"""
sound_in_place(P, S) :- affords(P, S).
item_makes_sound(I, S) :- item(I), sound_of(I, S).
place_has_sound_item(P, I, S) :- sound_in_place(P, S), item_makes_sound(I, S).
valid_story(P, S, I, U) :- place_has_sound_item(P, I, S), surprise(U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SOUND_EFFECTS.items():
        lines.append(asp.fact("sound", sid))
    for iid, i in SHARING_ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.sound:
            lines.append(asp.fact("sound_of", iid, i.sound))
        if i.shareable:
            lines.append(asp.fact("shareable", iid))
    for suid in SURPRISES:
        lines.append(asp.fact("surprise", suid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: winter sharing, sound effects, and surprises.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound-effect", choices=SOUND_EFFECTS)
    ap.add_argument("--sharing-item", choices=SHARING_ITEMS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--giver", choices=["grandma", "grandpa"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.sound_effect is None or c[1] == args.sound_effect)
              and (args.sharing_item is None or c[2] == args.sharing_item)
              and (args.surprise is None or c[3] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, sound_effect, sharing_item, surprise = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    friend_type = args.friend_type or ("girl" if hero_type == "boy" else "boy")
    hero_name = args.hero_name or rng.choice(BOY_NAMES if hero_type == "boy" else GIRL_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_type == "girl" else BOY_NAMES)
    giver = args.giver or rng.choice(["grandma", "grandpa"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, sound_effect=sound_effect, sharing_item=sharing_item,
        surprise=surprise, hero_name=hero_name, hero_type=hero_type,
        friend_name=friend_name, friend_type=friend_type,
        giver=giver, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    sounds_list = [SOUND_EFFECTS[params.sound_effect]]
    sounds_list.append(next(s for s in SOUND_EFFECTS.values() if s.id != params.sound_effect))
    surprises_list = [SURPRISES[params.surprise]]
    items_list = [SHARING_ITEMS[params.sharing_item]]
    other_item = next(i for i in SHARING_ITEMS.values() if i.id != params.sharing_item)
    items_list.append(other_item)

    world = tell(SETTINGS[params.place], sounds_list, surprises_list, items_list,
                 params.hero_name, params.hero_type, [params.trait],
                 params.friend_name, params.friend_type, params.giver)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, sound, item, surprise) combos:\n")
        for place, sound, item, surprise in stories:
            print(f"  {place:12} {sound:8} {item:8} {surprise:8}")
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
            header = f"### {p.hero_name}: {p.sound_effect} at {p.place} (item: {p.sharing_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
