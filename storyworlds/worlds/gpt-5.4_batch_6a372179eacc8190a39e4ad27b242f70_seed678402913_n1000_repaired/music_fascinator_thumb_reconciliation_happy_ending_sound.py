#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/music_fascinator_thumb_reconciliation_happy_ending_sound.py
=======================================================================================

A standalone fairy-tale storyworld about music, a fascinator, and a sore thumb.

Tiny premise
------------
Two children are meant to make music at a little feast. One child wears a lovely
fascinator. A gust and a hurried grab bend the hat and scratch a thumb, so the
music goes wrong and hurt feelings bloom. Then the friend apologizes, helps mend
the fascinator, and finds a gentle way to share the song. The ending proves that
the quarrel has changed into friendship again.

This world keeps its logic small and explicit:

* some instruments truly depend on a thumb, so a sore thumb matters
* some repair materials are gentle enough to mend a delicate fascinator
* a sincere apology plus real help leads to reconciliation
* a rhythm helper can turn a shaky solo into a happy duet

Run it
------
    python storyworlds/worlds/gpt-5.4/music_fascinator_thumb_reconciliation_happy_ending_sound.py
    python storyworlds/worlds/gpt-5.4/music_fascinator_thumb_reconciliation_happy_ending_sound.py --instrument lute --repair ribbon
    python storyworlds/worlds/gpt-5.4/music_fascinator_thumb_reconciliation_happy_ending_sound.py --repair thorn_clip
    python storyworlds/worlds/gpt-5.4/music_fascinator_thumb_reconciliation_happy_ending_sound.py --all
    python storyworlds/worlds/gpt-5.4/music_fascinator_thumb_reconciliation_happy_ending_sound.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/music_fascinator_thumb_reconciliation_happy_ending_sound.py --qa --json
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
GENTLE_MIN = 2
SINCERE_MIN = 2


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
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    thumb_need: int = 1
    music_word: str = "music"
    tags: set[str] = field(default_factory=set)


@dataclass
class Fascinator:
    id: str
    label: str
    phrase: str
    trim: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    gentle: int = 2
    fixes_fragile: bool = True
    method: str = ""
    qa_method: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Rhythm:
    id: str
    label: str
    phrase: str
    sound: str
    soothing: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Apology:
    id: str
    sincerity: int = 2
    words: str = ""
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


def _r_thumb_wobble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    instrument = world.entities.get("instrument")
    if hero is None or instrument is None:
        return out
    if hero.meters["thumb_sore"] < THRESHOLD:
        return out
    if instrument.attrs.get("thumb_need", 0) <= 0:
        return out
    sig = ("thumb_wobble", hero.id, instrument.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    instrument.meters["wobble"] += float(instrument.attrs.get("thumb_need", 1))
    hero.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_mended_pride(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    fascinator = world.entities.get("fascinator")
    friend = world.entities.get("friend")
    if hero is None or fascinator is None or friend is None:
        return out
    if fascinator.meters["mended"] < THRESHOLD:
        return out
    sig = ("mended_pride", fascinator.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    friend.memes["hope"] += 1
    out.append("__mended__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    fascinator = world.entities.get("fascinator")
    if hero is None or friend is None or fascinator is None:
        return out
    if friend.memes["apology"] < THRESHOLD:
        return out
    if friend.meters["helped"] < THRESHOLD:
        return out
    if fascinator.meters["mended"] < THRESHOLD:
        return out
    sig = ("reconcile", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["anger"] = 0.0
    friend.memes["guilt"] = 0.0
    hero.memes["forgiveness"] += 1
    friend.memes["forgiveness"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule(name="thumb_wobble", tag="physical", apply=_r_thumb_wobble),
    Rule(name="mended_pride", tag="emotional", apply=_r_mended_pride),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(x for x in lines if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "moon_garden": Place(
        id="moon_garden",
        name="the Moonlit Garden",
        opening="where pale flowers glowed like tiny lanterns and the fountain whispered nearby",
        ending="under the moonlit roses",
        tags={"garden", "fairy_tale"},
    ),
    "crystal_bridge": Place(
        id="crystal_bridge",
        name="the Crystal Bridge",
        opening="where little lamps shone in the river below and the night air hummed softly",
        ending="above the bright river",
        tags={"river", "fairy_tale"},
    ),
    "sunset_green": Place(
        id="sunset_green",
        name="the Sunset Green",
        opening="where bunting fluttered and the first evening stars blinked awake",
        ending="on the soft village grass",
        tags={"village", "fairy_tale"},
    ),
}

INSTRUMENTS = {
    "lute": Instrument(
        id="lute",
        label="lute",
        phrase="a pearly little lute",
        sound="plink-plink",
        thumb_need=2,
        music_word="music",
        tags={"lute", "string", "music", "thumb"},
    ),
    "harp": Instrument(
        id="harp",
        label="harp",
        phrase="a silver lap harp",
        sound="ting-ting",
        thumb_need=2,
        music_word="music",
        tags={"harp", "string", "music", "thumb"},
    ),
    "thumb_piano": Instrument(
        id="thumb_piano",
        label="thumb piano",
        phrase="a tiny thumb piano with moon-bright keys",
        sound="plink-plink-plink",
        thumb_need=3,
        music_word="music",
        tags={"thumb_piano", "music", "thumb"},
    ),
    "reed_pipe": Instrument(
        id="reed_pipe",
        label="reed pipe",
        phrase="a reed pipe",
        sound="toot-toot",
        thumb_need=0,
        music_word="music",
        tags={"pipe", "music"},
    ),
}

FASCINATORS = {
    "feather": Fascinator(
        id="feather",
        label="fascinator",
        phrase="a blue fascinator with a curled feather",
        trim="the curled feather",
        fragile=True,
        tags={"fascinator", "feather"},
    ),
    "pearl": Fascinator(
        id="pearl",
        label="fascinator",
        phrase="a pearl-dotted fascinator",
        trim="the little pearl spray",
        fragile=True,
        tags={"fascinator", "pearls"},
    ),
    "butterfly": Fascinator(
        id="butterfly",
        label="fascinator",
        phrase="a butterfly fascinator stitched with gold thread",
        trim="the butterfly wings",
        fragile=True,
        tags={"fascinator", "butterfly"},
    ),
}

REPAIRS = {
    "ribbon": Repair(
        id="ribbon",
        label="silk ribbon",
        phrase="a strip of silver silk ribbon",
        gentle=3,
        fixes_fragile=True,
        method="smoothed the trim and tied it in place with a strip of silver silk ribbon",
        qa_method="mended the fascinator with a soft silk ribbon",
        tags={"ribbon", "repair"},
    ),
    "daisy_thread": Repair(
        id="daisy_thread",
        label="daisy thread",
        phrase="a daisy stem twined like thread",
        gentle=2,
        fixes_fragile=True,
        method="set the trim straight and laced it gently with daisy thread",
        qa_method="laced the fascinator back together with daisy thread",
        tags={"flowers", "repair"},
    ),
    "golden_pin": Repair(
        id="golden_pin",
        label="golden pin",
        phrase="a tiny golden pin with a blunt tip",
        gentle=2,
        fixes_fragile=True,
        method="fastened the trim again with a tiny blunt golden pin",
        qa_method="fastened the fascinator with a blunt golden pin",
        tags={"pin", "repair"},
    ),
    "thorn_clip": Repair(
        id="thorn_clip",
        label="thorn clip",
        phrase="a thorn clip",
        gentle=1,
        fixes_fragile=False,
        method="tried to pinch the trim tight with a thorn clip",
        qa_method="tried to pinch the fascinator with a thorn clip",
        tags={"thorn"},
    ),
}

RHYTHMS = {
    "bell": Rhythm(
        id="bell",
        label="silver bell",
        phrase="a silver bell on a blue cord",
        sound="ding-ding",
        soothing=3,
        tags={"bell", "sound"},
    ),
    "tambour": Rhythm(
        id="tambour",
        label="tiny tambour",
        phrase="a tiny tambour with starry jingles",
        sound="jingle-jingle",
        soothing=2,
        tags={"tambour", "sound"},
    ),
    "clap": Rhythm(
        id="clap",
        label="hand-claps",
        phrase="soft hand-claps",
        sound="clap-clap",
        soothing=1,
        tags={"clap", "sound"},
    ),
}

APOLOGIES = {
    "warm": Apology(
        id="warm",
        sincerity=3,
        words=' "I was trying to save it, not spoil it," said the friend. "I am sorry for your hat and your thumb. Let me help."',
        qa_text="gave a warm apology and offered help at once",
        tags={"apology"},
    ),
    "shy": Apology(
        id="shy",
        sincerity=2,
        words=' "I did not mean to hurt you," whispered the friend. "I am sorry. Please let me make it better."',
        qa_text="gave a shy but sincere apology",
        tags={"apology"},
    ),
    "mumble": Apology(
        id="mumble",
        sincerity=1,
        words=' "Oh... sorry," murmured the friend, without really looking up.',
        qa_text="mumbled a weak apology",
        tags={"apology"},
    ),
}


@dataclass
class StoryParams:
    place: str
    instrument: str
    fascinator: str
    repair: str
    rhythm: str
    apology: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    elder: str
    mishap: str = "sharp"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="moon_garden",
        instrument="lute",
        fascinator="feather",
        repair="ribbon",
        rhythm="bell",
        apology="warm",
        hero="Lina",
        hero_gender="girl",
        friend="Milo",
        friend_gender="boy",
        elder="grandmother",
        mishap="sharp",
    ),
    StoryParams(
        place="crystal_bridge",
        instrument="harp",
        fascinator="pearl",
        repair="golden_pin",
        rhythm="tambour",
        apology="shy",
        hero="Nell",
        hero_gender="girl",
        friend="Tobin",
        friend_gender="boy",
        elder="aunt",
        mishap="sharp",
    ),
    StoryParams(
        place="sunset_green",
        instrument="thumb_piano",
        fascinator="butterfly",
        repair="daisy_thread",
        rhythm="bell",
        apology="warm",
        hero="Pip",
        hero_gender="boy",
        friend="Wren",
        friend_gender="girl",
        elder="grandmother",
        mishap="little",
    ),
]


GIRL_NAMES = ["Lina", "Nell", "Mira", "Elsa", "Wren", "Dora", "Ivy", "Faye"]
BOY_NAMES = ["Milo", "Tobin", "Pip", "Ari", "Nico", "Rowan", "Finn", "Jory"]


def valid_combo(instrument: Instrument, repair: Repair) -> bool:
    return instrument.thumb_need > 0 and repair.gentle >= GENTLE_MIN and repair.fixes_fragile


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for instrument_id, instrument in INSTRUMENTS.items():
            for fascinator_id, fascinator in FASCINATORS.items():
                for repair_id, repair in REPAIRS.items():
                    if fascinator.fragile and valid_combo(instrument, repair):
                        combos.append((place_id, instrument_id, fascinator_id, repair_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    instrument = INSTRUMENTS[params.instrument]
    rhythm = RHYTHMS[params.rhythm]
    apology = APOLOGIES[params.apology]
    if apology.sincerity < SINCERE_MIN:
        return "mended_but_cool"
    if params.mishap == "sharp" and instrument.thumb_need >= 2 and rhythm.soothing >= 2:
        return "duet"
    return "soft_solo"


def explain_rejection(instrument: Instrument, repair: Repair) -> str:
    if instrument.thumb_need <= 0:
        return (
            f"(No story: a {instrument.label} does not truly depend on a thumb here, "
            "so the thumb mishap would not shape the music or the turn of the tale.)"
        )
    if repair.gentle < GENTLE_MIN or not repair.fixes_fragile:
        return (
            f"(No story: {repair.label} is too rough for a delicate fascinator. "
            "Pick a gentle repair such as ribbon, daisy_thread, or golden_pin.)"
        )
    return "(No story: this combination does not make a reasonable fairy-tale problem and fix.)"


def explain_apology(apology: Apology) -> str:
    return (
        f"(No story: the '{apology.id}' apology is too weak for reconciliation "
        f"(sincerity={apology.sincerity} < {SINCERE_MIN}). This world only tells happy mending stories.)"
    )


def predict_music(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    instrument = sim.get("instrument")
    hero.meters["thumb_sore"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": instrument.meters["wobble"],
        "needs_help": instrument.meters["wobble"] >= THRESHOLD,
    }


def opening(world: World, place: Place, hero: Entity, friend: Entity,
            elder: Entity, instrument: Instrument, fascinator: Fascinator) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Once, in {place.name}, {place.opening}, {hero.id} was meant to play evening music "
        f"for the lantern feast."
    )
    world.say(
        f"{hero.id} wore {fascinator.phrase}, and carried {instrument.phrase} under "
        f"{hero.pronoun('possessive')} arm. {friend.id} skipped beside {hero.pronoun('object')}, "
        f"for {friend.pronoun()} loved every tune that floated from it."
    )
    world.say(
        f'"Play the first song by the fountain," called {elder.id}. "Let it sound bright enough to wake the stars."'
    )


def admiration(world: World, hero: Entity, friend: Entity, fascinator: Fascinator) -> None:
    world.say(
        f'{friend.id} gazed at the fascinator and smiled. "It looks as light as a butterfly," '
        f'{friend.pronoun()} said. {hero.id} touched {fascinator.trim} with a proud little nod.'
    )


def gust_and_grab(world: World, hero: Entity, friend: Entity, fascinator_ent: Entity,
                  instrument_ent: Entity, instrument: Instrument, mishap: str) -> None:
    fascinator_ent.meters["askew"] += 1
    fascinator_ent.meters["bent"] += 1
    world.say(
        "Just then a playful wind came swish-swish through the leaves and tugged at the fascinator."
    )
    if mishap == "sharp":
        hero.meters["thumb_sore"] += 1
        hero.memes["hurt"] += 1
        friend.memes["guilt"] += 1
        world.say(
            f'{friend.id} reached up too quickly to save it. Snag! The trim bent sideways, and the little pin '
            f'scratched {hero.id} on the thumb.'
        )
    else:
        hero.meters["thumb_sore"] += 0.5
        hero.memes["hurt"] += 0.5
        friend.memes["guilt"] += 1
        world.say(
            f'{friend.id} reached up too quickly to save it. Snip! The trim bent sideways, and the pin nicked '
            f'{hero.id}\'s thumb only a little.'
        )
    propagate(world, narrate=False)
    if hero.meters["thumb_sore"] >= THRESHOLD and instrument.attrs.get("thumb_need", 0) > 0:
        instrument_ent.meters["wobble"] += 0  # keep entity obviously present for trace


def quarrel(world: World, hero: Entity, friend: Entity, instrument: Instrument) -> None:
    pred = predict_music(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    hero.memes["anger"] += 1
    friend.memes["sadness"] += 1
    if pred["needs_help"]:
        world.say(
            f'{hero.id} tried to play, but {instrument.sound} came out thin and wobbly. '
            f'{hero.pronoun("possessive").capitalize()} sore thumb could not guide the strings as it should.'
        )
    else:
        world.say(
            f'{hero.id} lifted the instrument, but the little ache in {hero.pronoun("possessive")} thumb made '
            f'{hero.pronoun("object")} stop and frown.'
        )
    world.say(
        f'"You spoiled my hat and spoiled my song," cried {hero.id}. {friend.id} took one step back, looking smaller than before.'
    )


def apology(world: World, friend: Entity, apology_cfg: Apology) -> None:
    friend.memes["apology"] += float(apology_cfg.sincerity)
    world.say(f"{friend.id}{apology_cfg.words}")
    propagate(world, narrate=False)


def mend(world: World, hero: Entity, friend: Entity, fascinator_ent: Entity,
         fascinator: Fascinator, repair: Repair) -> None:
    fascinator_ent.meters["mended"] += 1
    friend.meters["helped"] += 1
    world.say(
        f"Then {friend.id} took {repair.phrase} and {repair.method}. Little by little, "
        f"{fascinator.trim} stood neat again."
    )
    world.say(
        f"{hero.id} touched the fascinator once more and saw that it was lovely again, though now it looked lovelier for being cared for."
    )
    propagate(world, narrate=False)


def forgive(world: World, hero: Entity, friend: Entity) -> None:
    if hero.memes["forgiveness"] >= THRESHOLD:
        world.say(
            f'{hero.id} looked at {friend.id}, and the hard knot in {hero.pronoun("possessive")} chest loosened. '
            f'"I know you were trying to help," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f"{hero.id} was quieter after that, and no longer looked quite so angry."
        )


def share_music(world: World, hero: Entity, friend: Entity, instrument: Instrument,
                rhythm: Rhythm, outcome: str) -> None:
    friend.meters["helped"] += 1
    if outcome == "duet":
        world.say(
            f'"Then we will not ask your sore thumb to do everything," said {friend.id}. '
            f'{friend.pronoun().capitalize()} lifted {rhythm.phrase} and tried a soft {rhythm.sound}.'
        )
        world.say(
            f'{hero.id} answered with a gentler {instrument.sound}, and soon the two sounds twined together. '
            f'The music no longer asked for a brave solo; it asked for two friends.'
        )
    elif outcome == "soft_solo":
        world.say(
            f'{friend.id} kept a kind little beat with {rhythm.phrase} -- {rhythm.sound} -- while {hero.id} played only the easiest notes.'
        )
        world.say(
            f'Soon {instrument.sound} grew clear again, and the tune floated out smooth as ribbon on water.'
        )
    else:
        world.say(
            f'{friend.id} stood close with {rhythm.phrase} and kept the softest beat of all. '
            f'{hero.id} played carefully, and though the tune was small, it was gentle enough for forgiveness.'
        )
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1


def ending(world: World, place: Place, hero: Entity, friend: Entity, elder: Entity,
           outcome: str) -> None:
    if outcome == "duet":
        world.say(
            f"People turned from the lantern stalls and listened. Even the fountain seemed to hush, and then the feast clapped along."
        )
        world.say(
            f'{elder.id.capitalize()} smiled so warmly that the whole place seemed brighter. '
            f'"Now that is true feast music," {elder.pronoun()} said.'
        )
    elif outcome == "soft_solo":
        world.say(
            f"The tune drifted over the feast like a silver thread, soft and sweet, and everyone smiled because quiet songs can be brave too."
        )
        world.say(
            f'{elder.id.capitalize()} laid a hand over {elder.pronoun("possessive")} heart and bowed a little.'
        )
    else:
        world.say(
            "The song was not grand, yet it was enough to make the lantern flames sway gently in time."
        )
        world.say(
            f'{elder.id.capitalize()} nodded, pleased that the quarrel had grown smaller than the music.'
        )
    world.say(
        f"After that, {hero.id} and {friend.id} sat together {place.ending}, and whenever they remembered the prick and the tears, they remembered the mending too."
    )
    world.say(
        f"So the fascinator was straight, the thumb was resting, the music was shared, and the friends were friends again."
    )


def tell(place: Place, instrument_cfg: Instrument, fascinator_cfg: Fascinator,
         repair_cfg: Repair, rhythm_cfg: Rhythm, apology_cfg: Apology,
         hero_name: str, hero_gender: str, friend_name: str, friend_gender: str,
         elder_name: str, mishap: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, phrase=friend_name, role="friend"))
    elder = world.add(Entity(id="elder", kind="character", type="woman", label=elder_name, phrase=elder_name, role="elder"))
    instrument_ent = world.add(Entity(
        id="instrument",
        type="instrument",
        label=instrument_cfg.label,
        phrase=instrument_cfg.phrase,
        attrs={"thumb_need": instrument_cfg.thumb_need, "sound": instrument_cfg.sound},
        tags=set(instrument_cfg.tags),
    ))
    fascinator_ent = world.add(Entity(
        id="fascinator",
        type="fascinator",
        label=fascinator_cfg.label,
        phrase=fascinator_cfg.phrase,
        attrs={"fragile": fascinator_cfg.fragile, "trim": fascinator_cfg.trim},
        tags=set(fascinator_cfg.tags),
    ))
    rhythm_ent = world.add(Entity(
        id="rhythm",
        type="rhythm",
        label=rhythm_cfg.label,
        phrase=rhythm_cfg.phrase,
        attrs={"sound": rhythm_cfg.sound, "soothing": rhythm_cfg.soothing},
        tags=set(rhythm_cfg.tags),
    ))

    opening(world, place, hero, friend, elder, instrument_cfg, fascinator_cfg)
    admiration(world, hero, friend, fascinator_cfg)

    world.para()
    gust_and_grab(world, hero, friend, fascinator_ent, instrument_ent, instrument_cfg, mishap)
    quarrel(world, hero, friend, instrument_cfg)

    world.para()
    apology(world, friend, apology_cfg)
    mend(world, hero, friend, fascinator_ent, fascinator_cfg, repair_cfg)
    forgive(world, hero, friend)

    world.para()
    outcome = outcome_of(
        StoryParams(
            place=place.id,
            instrument=instrument_cfg.id,
            fascinator=fascinator_cfg.id,
            repair=repair_cfg.id,
            rhythm=rhythm_cfg.id,
            apology=apology_cfg.id,
            hero=hero_name,
            hero_gender=hero_gender,
            friend=friend_name,
            friend_gender=friend_gender,
            elder=elder_name,
            mishap=mishap,
        )
    )
    share_music(world, hero, friend, instrument_cfg, rhythm_cfg, outcome)
    ending(world, place, hero, friend, elder, outcome)

    world.facts.update(
        place=place,
        instrument_cfg=instrument_cfg,
        fascinator_cfg=fascinator_cfg,
        repair_cfg=repair_cfg,
        rhythm_cfg=rhythm_cfg,
        apology_cfg=apology_cfg,
        hero=hero,
        friend=friend,
        elder=elder,
        instrument=instrument_ent,
        fascinator=fascinator_ent,
        rhythm=rhythm_ent,
        thumb_hurt=hero.meters["thumb_sore"] >= THRESHOLD,
        mended=fascinator_ent.meters["mended"] >= THRESHOLD,
        reconciled=hero.memes["forgiveness"] >= THRESHOLD,
        outcome=outcome,
        mishap=mishap,
    )
    return world


KNOWLEDGE = {
    "fascinator": [
        (
            "What is a fascinator?",
            "A fascinator is a small fancy hat or hair piece with pretty trim, like feathers or ribbons. People wear it for dress-up or a special celebration."
        )
    ],
    "thumb": [
        (
            "Why does a sore thumb matter when someone plays string music?",
            "A sore thumb can make it hard to pluck or steady the strings. Then the notes may wobble or come out softly."
        )
    ],
    "lute": [
        (
            "What is a lute?",
            "A lute is a string instrument you pluck with your fingers and thumb. It can make warm, gentle music."
        )
    ],
    "harp": [
        (
            "What is a harp?",
            "A harp is an instrument with many strings that sing when you pluck them. Small harps can sound bright and tinkly."
        )
    ],
    "thumb_piano": [
        (
            "What is a thumb piano?",
            "A thumb piano is a tiny instrument with little metal keys that you pluck with your thumbs. It makes soft, chiming notes."
        )
    ],
    "bell": [
        (
            "Why does a bell fit nicely with music?",
            "A bell can keep a gentle beat and add a clear little ring. It helps other players stay together."
        )
    ],
    "tambour": [
        (
            "What does a tambour do in a song?",
            "A tambour shakes or jingles to mark the rhythm. It can make a tune feel lively without covering it up."
        )
    ],
    "repair": [
        (
            "Why is a gentle repair better for something delicate?",
            "A delicate thing can tear or bend more if you pull it too hard. A gentle repair keeps it safe while you mend it."
        )
    ],
    "apology": [
        (
            "What makes an apology feel real?",
            "A real apology says what went wrong, shows care for the hurt person, and tries to help make things better. It is not only words; it is kindness too."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "fascinator",
    "thumb",
    "lute",
    "harp",
    "thumb_piano",
    "bell",
    "tambour",
    "repair",
    "apology",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"].label
    friend = f["friend"].label
    instrument = f["instrument_cfg"]
    fascinator = f["fascinator_cfg"]
    outcome = f["outcome"]
    if outcome == "duet":
        end_line = "and ends with two children making music together after they make up."
    elif outcome == "soft_solo":
        end_line = "and ends with forgiveness, a mended fascinator, and a soft happy song."
    else:
        end_line = "and ends with hurt feelings cooling into friendship again."
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "music", "fascinator", and "thumb", {end_line}',
        f"Tell a gentle tale where {hero}'s thumb is hurt during a fuss over a fascinator, but {friend} apologizes and helps mend both the hat and the friendship.",
        f'Write a small fairy-tale with sound effects like "{instrument.sound}" and a happy reconciliation at a lantern feast.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    elder = f["elder"]
    instrument = f["instrument_cfg"]
    fascinator = f["fascinator_cfg"]
    repair = f["repair_cfg"]
    rhythm = f["rhythm_cfg"]
    apology_cfg = f["apology_cfg"]
    place = f["place"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who was going to play music at the feast, and {friend.label}, who wanted to help. An older helper named {elder.label} was there too."
        ),
        (
            "What was special about the hero at the beginning?",
            f"{hero.label} wore {fascinator.phrase} and carried {instrument.phrase} to play at the lantern feast. Those two lovely things made {hero.pronoun('object')} feel proud and excited."
        ),
        (
            f"How did the trouble begin?",
            f"A gust of wind tugged at the fascinator, and {friend.label} grabbed too quickly to save it. That bent the trim and scratched {hero.label}'s thumb, which hurt both the hat and the music."
        ),
    ]
    if f["thumb_hurt"]:
        qa.append(
            (
                f"Why did the thumb matter in this story?",
                f"It mattered because {instrument.label} needs a thumb to guide or pluck it well. When {hero.label}'s thumb was sore, the notes came out wobbly instead of smooth."
            )
        )
    qa.append(
        (
            f"How did {friend.label} try to make things better?",
            f"{friend.label} {apology_cfg.qa_text}. Then {friend.pronoun()} used {repair.phrase} and {repair.qa_method}, so the fascinator looked neat again."
        )
    )
    if outcome == "duet":
        qa.append(
            (
                "How did the story end?",
                f"It ended with a happy duet. {friend.label} kept a gentle beat with {rhythm.label}, and {hero.label} answered with careful notes until the whole feast listened."
            )
        )
    elif outcome == "soft_solo":
        qa.append(
            (
                "How did the story end?",
                f"It ended softly and happily. {friend.label} helped keep time while {hero.label} played easy notes, and the gentle song showed that they had forgiven each other."
            )
        )
    else:
        qa.append(
            (
                "Did they become friends again?",
                f"Yes, though the music stayed small. The apology and the mending mattered because they changed the quarrel into kindness again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"fascinator", "thumb", "repair", "apology"}
    instrument = f["instrument_cfg"]
    if instrument.id == "lute":
        tags.add("lute")
    elif instrument.id == "harp":
        tags.add("harp")
    elif instrument.id == "thumb_piano":
        tags.add("thumb_piano")
    rhythm = f["rhythm_cfg"]
    if rhythm.id == "bell":
        tags.add("bell")
    elif rhythm.id == "tambour":
        tags.add("tambour")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
thumb_story(I) :- instrument(I), thumb_need(I, N), N > 0.
gentle_repair(R) :- repair(R), gentle(R, G), gentle_min(M), G >= M, fixes_fragile(R).
valid(P, I, F, R) :- place(P), thumb_story(I), fascinator(F), gentle_repair(R).

reconciles :- chosen_apology(A), sincerity(A, S), sincere_min(M), S >= M.
duet :- reconciles, chosen_mishap(sharp), chosen_instrument(I), thumb_need(I, N), N >= 2,
        chosen_rhythm(R), soothing(R, T), T >= 2.
soft_solo :- reconciles, not duet.
mended_but_cool :- not reconciles.

outcome(duet) :- duet.
outcome(soft_solo) :- soft_solo.
outcome(mended_but_cool) :- mended_but_cool.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, instrument in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        lines.append(asp.fact("thumb_need", iid, instrument.thumb_need))
    for fid in FASCINATORS:
        lines.append(asp.fact("fascinator", fid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("gentle", rid, repair.gentle))
        if repair.fixes_fragile:
            lines.append(asp.fact("fixes_fragile", rid))
    for rid, rhythm in RHYTHMS.items():
        lines.append(asp.fact("rhythm", rid))
        lines.append(asp.fact("soothing", rid, rhythm.soothing))
    for aid, apology in APOLOGIES.items():
        lines.append(asp.fact("apology", aid))
        lines.append(asp.fact("sincerity", aid, apology.sincerity))
    lines.append(asp.fact("gentle_min", GENTLE_MIN))
    lines.append(asp.fact("sincere_min", SINCERE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_instrument", params.instrument),
            asp.fact("chosen_rhythm", params.rhythm),
            asp.fact("chosen_apology", params.apology),
            asp.fact("chosen_mishap", params.mishap),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    scenarios = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(p)

    mismatches = 0
    for params in scenarios:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches Python on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(scenarios)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld about music, a fascinator, a thumb mishap, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--fascinator", choices=FASCINATORS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--rhythm", choices=RHYTHMS)
    ap.add_argument("--apology", choices=APOLOGIES)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "aunt"])
    ap.add_argument("--mishap", choices=["little", "sharp"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [x for x in pool if x != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.instrument and args.repair:
        instrument = INSTRUMENTS[args.instrument]
        repair = REPAIRS[args.repair]
        if not valid_combo(instrument, repair):
            raise StoryError(explain_rejection(instrument, repair))
    if args.instrument and args.instrument not in INSTRUMENTS:
        raise StoryError("(No story: unknown instrument.)")
    if args.repair and args.repair not in REPAIRS:
        raise StoryError("(No story: unknown repair.)")
    if args.apology and APOLOGIES[args.apology].sincerity < SINCERE_MIN:
        raise StoryError(explain_apology(APOLOGIES[args.apology]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.instrument is None or combo[1] == args.instrument)
        and (args.fascinator is None or combo[2] == args.fascinator)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        if args.instrument and args.repair:
            raise StoryError(explain_rejection(INSTRUMENTS[args.instrument], REPAIRS[args.repair]))
        raise StoryError("(No valid combination matches the given options.)")

    place, instrument, fascinator, repair = rng.choice(sorted(combos))
    apology = args.apology or rng.choice([aid for aid, a in APOLOGIES.items() if a.sincerity >= SINCERE_MIN])
    rhythm = args.rhythm or rng.choice(sorted(RHYTHMS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    elder = args.elder or rng.choice(["grandmother", "aunt"])
    mishap = args.mishap or rng.choice(["little", "sharp"])
    return StoryParams(
        place=place,
        instrument=instrument,
        fascinator=fascinator,
        repair=repair,
        rhythm=rhythm,
        apology=apology,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        elder=elder,
        mishap=mishap,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        instrument = INSTRUMENTS[params.instrument]
        fascinator = FASCINATORS[params.fascinator]
        repair = REPAIRS[params.repair]
        rhythm = RHYTHMS[params.rhythm]
        apology = APOLOGIES[params.apology]
    except KeyError as err:
        raise StoryError(f"(No story: invalid parameter key {err!s}.)") from err

    if not valid_combo(instrument, repair):
        raise StoryError(explain_rejection(instrument, repair))
    if apology.sincerity < SINCERE_MIN:
        raise StoryError(explain_apology(apology))

    world = tell(
        place=place,
        instrument_cfg=instrument,
        fascinator_cfg=fascinator,
        repair_cfg=repair,
        rhythm_cfg=rhythm,
        apology_cfg=apology,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        elder_name=params.elder,
        mishap=params.mishap,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, instrument, fascinator, repair) combos:\n")
        for place, instrument, fascinator, repair in combos:
            print(f"  {place:14} {instrument:12} {fascinator:10} {repair}")
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
            header = (
                f"### {p.hero} and {p.friend}: {p.instrument}, {p.fascinator}, "
                f"{p.repair}, {outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
