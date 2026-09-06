#!/usr/bin/env python3
"""A varied fable world about challenged labels, musical chords, and friendship.

Seed tale used to build the world:
---
A small crow feared playing in public. Another animal called that fear cowardice,
but the crow's friend challenged the label and helped him act with care.

One day, his friend the rabbit stayed beside him and said that a true friend does
not laugh at a trembling wing. The rabbit helped the crow practice one note, then
two notes, and finally the whole chord. The crow tried again, found his courage,
and played the chord for everyone.

The meadow cheered. As a bonus, the fox brought a basket of sweet berries for both
friends, who learned that one frightened moment does not define anyone.

Causal state updates:
---
    fear + spotlight + mistake risk  -> fear rises
    friendship support               -> fear falls, courage rises
    successful chord                 -> pride rises, group joy rises
    group joy + kindness             -> bonus gift appears
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["fear", "courage", "joy", "pride", "friendship", "kindness", "stress"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "fox", "crow", "rabbit"}
        female = {"girl", "woman", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the meadow"
    stage: str = "the mossy stump"
    audience: str = "the little animals"
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Instrument:
    id: str
    label: str
    sound: str
    risk: str
    can_make_chord: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class BonusGift:
    label: str
    phrase: str
    cheer: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def apply_rules(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []

    hero = world.facts.get("hero")
    friend = world.facts.get("friend")
    instrument = world.facts.get("instrument")
    if not hero or not friend or not instrument:
        return out

    h = world.get(hero.id)
    f = world.get(friend.id)

    # Fear rises when the timid friend thinks about the stage.
    sig = ("fear", h.id)
    if h.memes["fear"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        h.memes["stress"] += 1
        out.append(f"{h.id} trembled near {world.setting.stage}.")

    # Friendship support lowers fear and raises courage.
    sig = ("support", h.id, f.id)
    if h.memes["friendship"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        h.memes["fear"] = max(0.0, h.memes["fear"] - 1.0)
        h.memes["courage"] += 1
        f.memes["kindness"] += 1
        out.append(f"{f.id} stayed close, and {h.id} felt braver.")

    # Successful chord raises joy/pride.
    sig = ("chord", h.id)
    if h.memes["courage"] >= THRESHOLD and h.memes["fear"] < THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        h.memes["joy"] += 1
        h.memes["pride"] += 1
        f.memes["joy"] += 1
        out.append(f"{h.id} made the full chord, and the meadow brightened.")

    # Bonus gift appears when the music and kindness have both happened.
    sig = ("bonus", h.id)
    if h.memes["joy"] >= THRESHOLD and f.memes["kindness"] >= THRESHOLD and sig not in world.fired:
        world.fired.add(sig)
        gift = _safe_fact(world, world.facts, "gift")
        world.facts["bonus_ready"] = True
        out.append(f"As a bonus, {gift.label} was brought to both friends.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_success(world: World, hero: Entity, friend: Entity, instrument: Instrument) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] += 1
    sim.get(hero.id).memes["friendship"] += 1
    apply_rules(sim, narrate=False)
    h = sim.get(hero.id)
    return h.memes["pride"] >= THRESHOLD


SETTINGS = {
    "meadow": Setting(place="the meadow", stage="the mossy stump", audience="the little animals"),
}

INSTRUMENTS = {
    "harp": Instrument(
        id="harp",
        label="harp",
        sound="clear notes",
        risk="a trembling mistake",
        can_make_chord=True,
    ),
}

GIFTS = {
    "berries": BonusGift(
        label="a bonus basket of sweet berries",
        phrase="a basket of sweet berries",
        cheer="sweet and shiny",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Mira", "Pia"]
BOY_NAMES = ["Pip", "Cody", "Tobin", "Nell", "Hugo"]


@dataclass(frozen=True)
class Incident:
    id: str
    premise: str
    conflict: str
    false_start: str
    clue: str
    plan: str
    chord: str
    result: str
    bonus_reason: str
    ending_image: str


INCIDENTS = {
    incident.id: incident
    for incident in [
        Incident(
            id="echo_cave",
            premise="The evening concert was moved beneath a stone arch after rain soaked the outdoor stage.",
            conflict="Every practice chord bounced back twice, and the overlapping echoes made the melody sound wrong.",
            false_start="The crow tried to overpower the echo, but louder notes only made a muddier roar.",
            clue="The rabbit clapped once, counted the two returning taps, and noticed a quiet pause between them.",
            plan="They marked that pause with three pebbles and practiced leaving room for the arch to answer.",
            chord="a slow, spacious chord that let each echo finish",
            result="The arch returned the notes like a gentle round instead of a jumble.",
            bonus_reason="the careful listening turned a troublesome echo into part of the music",
            ending_image="Three pebbles gleamed beside the harp while the last echo floated out under the stars.",
        ),
        Incident(
            id="lost_note",
            premise="At dawn, the meadow choir discovered that its opening song had one note missing from the music card.",
            conflict="The blank space came just before the chord the crow had agreed to play.",
            false_start="The crow guessed a bright high note, but it made the sleepy song sound like an alarm.",
            clue="The rabbit hummed the line before and after the gap, and a nearby wren answered with a low call.",
            plan="They tested three notes softly, wrote the wren's low note into the space, and asked the choir to check it.",
            chord="a warm low chord that completed the dawn song",
            result="The choir entered together, and even the waking flowers seemed to lean toward the sound.",
            bonus_reason="the friends solved the missing-note mystery instead of hiding it",
            ending_image="The repaired music card rested beneath a yellow feather as sunrise filled the meadow.",
        ),
        Incident(
            id="sleeping_fawn",
            premise="The spring concert began while a tired fawn slept behind the fern nearest the harp.",
            conflict="The planned opening chord was too sharp for a listener who needed rest.",
            false_start="The crow almost skipped the performance without telling anyone why.",
            clue="The rabbit saw the fern tremble with each tuning note and found the curled, sleeping fawn.",
            plan="They asked the audience to move back, wrapped the harp post with felt, and chose a gentler voicing.",
            chord="a soft, rounded chord no louder than leaves brushing",
            result="The audience heard every note, and the fawn slept peacefully through the song.",
            bonus_reason="the music succeeded without pushing aside someone else's need",
            ending_image="A berry leaf lay beside the quiet strings while the fawn's ears twitched in a dream.",
        ),
        Incident(
            id="windy_pages",
            premise="A gusty afternoon sent the orchestra's music pages skating across the meadow.",
            conflict="The crow caught the chord page, but the measure numbers had been hidden under muddy pawprints.",
            false_start="He arranged the pages by size, which put the ending before the beginning.",
            clue="The rabbit noticed that a blue thread continued from the edge of one page onto the next.",
            plan="They matched every thread, wiped the corners clean, and tied the finished score to a flat board.",
            chord="the returning chord at the true end of the wind-tossed song",
            result="The players followed the restored order and landed on the final beat together.",
            bonus_reason="patient teamwork rescued the whole orchestra's score",
            ending_image="Blue threads held the pages still as one last breeze rang the smallest harp string.",
        ),
        Incident(
            id="frayed_string",
            premise="Minutes before a lantern concert, the crow spotted a pale fuzz along one harp string.",
            conflict="Playing the full chord could snap the frayed string and startle everyone.",
            false_start="He considered pretending not to see it so the concert would begin on time.",
            clue="The rabbit held a lantern behind the string, making the broken fibers cast a crooked shadow.",
            plan="They stopped the rehearsal, told the conductor, and helped fetch the spare string for an adult badger to fit.",
            chord="a clear tested chord on the safely replaced string",
            result="The repaired harp stayed steady through every verse.",
            bonus_reason="speaking up protected both the instrument and the audience",
            ending_image="The old string curled safely in a repair box beneath a row of glowing lanterns.",
        ),
        Incident(
            id="duet_dispute",
            premise="Two young finches both wanted the solo that would lead into the crow's chord.",
            conflict="Their argument grew so loud that neither could hear the starting pitch.",
            false_start="The crow offered to erase the solo entirely, which left both finches feeling ignored.",
            clue="The rabbit noticed that one finch could hold a note while the other could decorate it with quick trills.",
            plan="The friends proposed a shared eight-beat duet and tapped the turns on the music stand.",
            chord="a bright chord that joined the held note and the final trill",
            result="Each finch had a real part, and their different voices made the entrance richer.",
            bonus_reason="the group changed a contest into a fair collaboration",
            ending_image="Two finch feathers crossed above the score while the chord shimmered through the dusk.",
        ),
        Incident(
            id="bees_in_harp",
            premise="Before the berry-blossom festival, a tiny bee colony began resting inside the hollow harp frame.",
            conflict="The instrument could not be played safely while the bees were sheltering there.",
            false_start="The crow waved a leafy branch near the opening, and the worried buzzing grew louder.",
            clue="The rabbit saw the bees repeatedly flying toward an empty hive box beside the orchard keeper.",
            plan="They backed away, called the keeper, and waited while the keeper moved the bees gently into the proper box.",
            chord="a lively chord played only after the keeper declared the harp clear",
            result="The bees settled by the blossoms, and the festival opened without frightening them.",
            bonus_reason="the friends paused the show and chose expert, gentle help",
            ending_image="Bees circled their new hive as golden pollen dusted the harp's polished frame.",
        ),
        Incident(
            id="bridge_signal",
            premise="A footbridge repair crew needed a musical signal when each new plank was safe to cross.",
            conflict="Hammering swallowed the crow's single-note signal, so waiting animals stepped forward too soon.",
            false_start="The crow played higher and faster, but the signal became harder to recognize.",
            clue="The rabbit heard that three notes together carried above the hammering without sounding like the work bell.",
            plan="They taught everyone one stop rhythm and one safe-to-cross chord, then rehearsed both before work resumed.",
            chord="a broad three-note chord reserved for the all-clear",
            result="The crowd waited behind the rope until the unmistakable chord announced each safe crossing.",
            bonus_reason="the music became a useful promise that kept neighbors safe",
            ending_image="The final chord crossed the stream as the repaired planks shone with clean rainwater.",
        ),
        Incident(
            id="night_moths",
            premise="For a moonlit recital, moths gathered around the lantern clipped above the harp strings.",
            conflict="Their wings hid the music and brushed dangerously close to the warm lantern glass.",
            false_start="The crow shook the music stand, scattering pages but not the circling moths.",
            clue="The rabbit noticed the moths preferred a cool white flower glowing several steps away.",
            plan="They asked an adult to remove the warm lantern, placed a cool covered light by the flowers, and reset the score.",
            chord="a moon-soft chord played from the newly darkened stage",
            result="The moths rested safely near the flowers while the audience watched by cool reflected light.",
            bonus_reason="curiosity led to a safer concert for even the smallest guests",
            ending_image="Silver moth wings opened over white petals as the harp fell quiet beneath the moon.",
        ),
        Incident(
            id="parade_tempo",
            premise="The harvest parade asked the crow to play a marching chord from a rolling flower cart.",
            conflict="The cart wheels bumped at a different beat from the marching animals.",
            false_start="He followed every wheel bump, making the musicians speed up and slow down.",
            clue="The rabbit spotted the flag bearer taking one steady step for every two shakes of the cart.",
            plan="They faced the harp inward, counted the flag bearer's steps, and practiced the chord while the cart stood still first.",
            chord="a firm marching chord locked to the flag bearer's pace",
            result="The band and walkers reached the square on the same joyful final beat.",
            bonus_reason="the friends found a dependable rhythm instead of chasing every bump",
            ending_image="A red leaf landed on the last harp string as the flower cart rolled into the square.",
        ),
        Incident(
            id="quiet_member",
            premise="A shy mole joined the meadow ensemble with a tiny wooden tapping block.",
            conflict="The louder players kept beginning before the mole could give the agreed count.",
            false_start="The crow suggested that the mole simply tap harder, but the little block could not compete.",
            clue="The rabbit saw the mole raise one paw clearly even when the tap could not be heard.",
            plan="They made the raised paw the visual count and had every player watch before sounding a note.",
            chord="a patient chord begun exactly on the mole's lifted-paw signal",
            result="The smallest instrument guided the largest sound, and nobody was left behind.",
            bonus_reason="the ensemble learned to notice a quiet friend's contribution",
            ending_image="The mole's wooden block sat at the center of a ring of instruments after the applause.",
        ),
        Incident(
            id="storm_shelter",
            premise="A sudden storm moved the meadow gathering into the old oak's roomy ground-level shelter.",
            conflict="Thunder made the crow freeze just as the sheltering youngsters needed a calming song.",
            false_start="He plucked random strings quickly to cover the thunder, creating a nervous clatter.",
            clue="The rabbit matched a slow breath to the fading space between each rumble.",
            plan="Together they counted four quiet breaths, chose the harp's lowest safe notes, and invited everyone to hum.",
            chord="a deep, steady chord supported by the whole shelter's hum",
            result="The song did not stop the storm, but it helped the youngsters wait calmly until it passed.",
            bonus_reason="honest fear became a chance to steady the whole group",
            ending_image="Raindrops slid from the oak leaves while the final low chord warmed the dry shelter.",
        ),
    ]
}

OPENINGS = [
    "The first sign of trouble appeared before anyone played a note.",
    "Everyone expected music, but the day brought an unexpected test.",
    "The trouble began before anyone could applaud.",
    "Near the gathering, two friends discovered that the plan had to change.",
    "While the instruments were being tuned, a problem demanded attention.",
    "One important concert almost went unheard.",
    "The meadow's next song began with a puzzle.",
    "Music was waiting, but so was a problem.",
]

SUPPORT_LINES = [
    '"Being afraid is a feeling, not your name," said {friend}.',
    '"That word does not get to decide what you do next," {friend} replied.',
    '"Courage can start with one honest question," said {friend}.',
    '"We can be careful and still continue," {friend} told {hero}.',
    '"Let us learn what the problem needs," said {friend}.',
    '"A frightened moment cannot tell your whole story," {friend} said.',
    '"You may pause, look, and choose," {friend} reminded {hero}.',
    '"I will stay while we test a safe idea," said {friend}.',
]

REFLECTIONS = [
    "Bravery had not erased fear; it had given fear a careful next step.",
    "The useful choice was not the loudest one, but the one based on what they had noticed.",
    "Friendship had supplied patience, not a shortcut.",
    "The solved problem mattered more than proving anything to a teasing voice.",
    "A good chord depended on listening before playing.",
    "They had changed the plan instead of pretending the trouble was small.",
    "Courage looked like asking for help and then doing a fair share.",
    "The meadow had heard more than music: it had heard two friends think together.",
]


@dataclass
class StoryParams:
    place: str = "meadow"
    instrument: str = "harp"
    gift: str = "berries"
    name: str = "Pip"
    friend_name: str = "Ria"
    incident: str = "echo_cave"
    opening: int = 0
    support: int = 0
    reflection: int = 0
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about friendship and a brave chord.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
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
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES + GIRL_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in BOY_NAMES + GIRL_NAMES if n != name])
    return StoryParams(
        place=getattr(args, "place", None) or "meadow",
        instrument=getattr(args, "instrument", None) or "harp",
        gift=getattr(args, "gift", None) or "berries",
        name=name,
        friend_name=friend_name,
        incident=rng.choice(list(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        support=rng.randrange(len(SUPPORT_LINES)),
        reflection=rng.randrange(len(REFLECTIONS)),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="crow", traits=["musical", "thoughtful"]))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="rabbit", traits=["kind", "steady"]))
    instrument = _safe_lookup(INSTRUMENTS, params.instrument)
    gift = _safe_lookup(GIFTS, params.gift)
    incident = _safe_lookup(INCIDENTS, params.incident)
    opening = OPENINGS[params.opening % len(OPENINGS)]
    support = SUPPORT_LINES[params.support % len(SUPPORT_LINES)].format(
        hero=hero.id, friend=friend.id
    )
    reflection = REFLECTIONS[params.reflection % len(REFLECTIONS)]
    world.facts.update(
        hero=hero,
        friend=friend,
        instrument=instrument,
        gift=gift,
        incident=incident,
        challenged_label="coward",
        clue=incident.clue,
        chosen_plan=incident.plan,
        played_chord=incident.chord,
        bonus_reason=incident.bonus_reason,
    )

    world.say(
        f"{opening} {incident.premise} {hero.id}, a young crow who loved the {instrument.label}, "
        f"had once frozen during a rehearsal. A teasing jay had called {hero.id} a coward. "
        f"{friend.id}, the crow's steady rabbit friend, said that judging a whole person by one frightened moment was unfair."
    )
    world.para()
    hero.memes["fear"] += 1
    world.say(f"{incident.conflict} {incident.false_start}")
    world.say(f'{hero.id} whispered, "What if the jay was right about me?" {support}')
    world.para()
    hero.memes["friendship"] += 1
    friend.memes["kindness"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 0.5)
    hero.memes["courage"] += 1
    world.say(f"Instead of rushing, the friends investigated. {incident.clue}")
    world.say(f'"That gives us something real to try," said {hero.id}. {incident.plan}')
    world.para()
    hero.memes["fear"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    friend.memes["joy"] += 1
    world.facts["bonus_ready"] = True
    world.say(
        f"When the moment came, {hero.id} played {incident.chord}. {incident.result} "
        f"No one needed to call the crow fearless. The brave part was noticing the risk, accepting help, and acting wisely."
    )
    world.say(
        f"As a bonus, the friends received {gift.phrase}, because {incident.bonus_reason}. {reflection}"
    )
    world.para()
    world.say(
        f"The happy ending was not that {hero.id} never felt afraid again. It was that the word coward no longer "
        f"controlled the next choice. {incident.ending_image}"
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, instrument, incident = f["hero"], f["friend"], f["instrument"], f["incident"]
    return [
        "Write a child-friendly fable that rejects coward as a fixed label and shows courage through a wise action.",
        f"Tell how {hero.id} and {friend.id} solve the {incident.id.replace('_', ' ')} problem before playing a {instrument.label} chord.",
        f"Write a happy-ending friendship fable using coward, chord, and bonus, grounded in this clue: {incident.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, instrument, incident = f["hero"], f["friend"], f["instrument"], f["incident"]
    return [
        QAItem(
            question=f"Why was it unfair to call {hero.id} a coward?",
            answer=f"It was unfair because one frightened rehearsal did not define {hero.id}. The crow examined a real problem, accepted friendship, and made a careful choice.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} and {friend.id} understand the problem?",
            answer=incident.clue,
        ),
        QAItem(
            question=f"What did the friends do before {hero.id} played the chord?",
            answer=incident.plan,
        ),
        QAItem(
            question=f"What was the bonus at the end of the story?",
            answer=f"The bonus was {f['gift'].phrase}. They received it because {incident.bonus_reason}.",
        ),
        QAItem(
            question="What image closes this version of the fable?",
            answer=incident.ending_image,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chord in music?",
            answer="A chord is two or more notes played together so they sound like one musical shape.",
        ),
        QAItem(
            question="What does coward mean?",
            answer="Coward is a harsh label for someone judged as lacking courage. A frightened moment does not define a person, and it is kinder to discuss the feeling and the choice instead.",
        ),
        QAItem(
            question="What does bonus mean?",
            answer="A bonus is something extra that is given in addition to the main thing, like a small gift or treat.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people or animals care about each other, help each other, and stay kind.",
        ),
    ]


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
    for e in list(world.entities.values()):
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        if memes:
            lines.append(f"  {e.id:10} ({e.type:8}) memes={memes}")
        else:
            lines.append(f"  {e.id:10} ({e.type:8})")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
challenged_coward_label(H) :- hero(H), fear(H), friend(F), helps(F,H).
friendship_support(H) :- friend(F), helps(F,H).
brave(H) :- hero(H), friendship_support(H), chord_played(H).
bonus_ready(H) :- brave(H), friend(F), kindness(F).
#show challenged_coward_label/1.
#show brave/1.
#show bonus_ready/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("friend", "friend"),
        asp.fact("fear", "hero"),
        asp.fact("helps", "friend", "hero"),
        asp.fact("chord_played", "hero"),
        asp.fact("kindness", "friend"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show challenged_coward_label/1. #show brave/1. #show bonus_ready/1."))
    atoms = set((a.name, tuple(arg.name if arg.type == a.arguments[0].type else arg.number for arg in a.arguments)) for a in model)
    expected = {("challenged_coward_label", ("hero",)), ("brave", ("hero",)), ("bonus_ready", ("hero",))}
    if atoms == expected:
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("  asp:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show challenged_coward_label/1. #show brave/1. #show bonus_ready/1."))
        return
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show challenged_coward_label/1. #show brave/1. #show bonus_ready/1."))
        print("\n".join(sorted(str(a) for a in model)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(name="Pip", friend_name="Ria"))]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
