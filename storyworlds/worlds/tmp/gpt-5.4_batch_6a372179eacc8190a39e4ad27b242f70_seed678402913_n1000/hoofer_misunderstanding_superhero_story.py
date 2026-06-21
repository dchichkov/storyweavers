#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hoofer_misunderstanding_superhero_story.py
=====================================================================

A standalone storyworld for a tiny superhero-style misunderstanding tale.

Premise
-------
A child in a superhero costume hears an announcer ask for "the hoofer" at a
show. Because there is a nearby hoof-related clue -- a pony ring, parade horses,
or a box of hobby horses -- the child misunderstands the word and thinks the
grown-ups need an animal. A friend or adult notices the mistake, gives a better
clue, and the hero helps the real performer reach the stage just in time.

The domain is deliberately narrow. The world model only allows combinations
where the misunderstanding is plausible and where there is also a sensible way
to clear it up. The story's middle turn comes from world state: a partial
hearing, a wrong search, a delay, a clarifying clue, and a redirected rescue.

Run it
------
    python storyworlds/worlds/gpt-5.4/hoofer_misunderstanding_superhero_story.py
    python storyworlds/worlds/gpt-5.4/hoofer_misunderstanding_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/hoofer_misunderstanding_superhero_story.py --qa
    python storyworlds/worlds/gpt-5.4/hoofer_misunderstanding_superhero_story.py --trace
    python storyworlds/worlds/gpt-5.4/hoofer_misunderstanding_superhero_story.py --asp
    python storyworlds/worlds/gpt-5.4/hoofer_misunderstanding_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly:
# add the package dir (storyworlds/) to sys.path even from worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    hero_spot: str
    announcer_place: str
    hoof_clues: set[str] = field(default_factory=set)
    clarifiers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    title: str
    dancer_label: str
    costume: str
    shoe_phrase: str
    entry_line: str
    finale: str
    clarifiers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class HoofClue:
    id: str
    label: str
    place: str
    mistaken_noun: str
    reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clarifier:
    id: str
    label: str
    clue_text: str
    correction: str
    redirect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    act: str
    hoof_clue: str
    clarifier: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    adult_type: str
    hero_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_delay(world: World) -> list[str]:
    hero = world.get("hero")
    stage = world.get("stage")
    crowd = world.get("crowd")
    if hero.meters["wrong_search"] < THRESHOLD or stage.meters["missing_dancer"] < THRESHOLD:
        return []
    sig = ("delay",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stage.meters["delay"] += 1
    crowd.memes["worry"] += 1
    return ["__delay__"]


def _r_clear(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.meters["saw_clue"] < THRESHOLD or hero.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("clear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["misunderstanding"] = 0.0
    hero.memes["understanding"] += 1
    hero.memes["embarrassment"] += 1
    friend.memes["relief"] += 1
    return ["__clear__"]


def _r_ready(world: World) -> list[str]:
    dancer = world.get("dancer")
    stage = world.get("stage")
    crowd = world.get("crowd")
    hero = world.get("hero")
    if dancer.meters["guided"] < THRESHOLD or stage.meters["missing_dancer"] < THRESHOLD:
        return []
    sig = ("ready",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    stage.meters["missing_dancer"] = 0.0
    stage.meters["ready"] += 1
    crowd.memes["joy"] += 1
    hero.memes["pride"] += 1
    return ["__ready__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="delay", tag="social", apply=_r_delay),
    Rule(name="clear", tag="social", apply=_r_clear),
    Rule(name="ready", tag="physical", apply=_r_ready),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "moonlight_fair": Setting(
        id="moonlight_fair",
        label="the Moonlight Fair",
        scene="colored lanterns, snack booths, and a bright little stage",
        hero_spot="by the ticket table",
        announcer_place="the crackly loudspeaker",
        hoof_clues={"pony_ring", "petting_gate"},
        clarifiers={"tap_shoes", "poster"},
        tags={"fair", "stage"},
    ),
    "river_parade": Setting(
        id="river_parade",
        label="the River Parade",
        scene="streamers, wagons, and a music stand near the curb",
        hero_spot="beside the candy cart",
        announcer_place="the silver parade microphone",
        hoof_clues={"wagon_team", "pony_ring"},
        clarifiers={"tap_shoes", "count_in"},
        tags={"parade", "stage"},
    ),
    "hero_school_show": Setting(
        id="hero_school_show",
        label="the Hero Helper Show at school",
        scene="paper stars, a painted moon, and folding chairs in neat rows",
        hero_spot="by the costume rack",
        announcer_place="the gym microphone",
        hoof_clues={"hobby_horses", "petting_gate"},
        clarifiers={"poster", "count_in"},
        tags={"school", "stage"},
    ),
}

ACTS = {
    "thunder_tap": Act(
        id="thunder_tap",
        title="Thunder Tap",
        dancer_label="the Thunder Tap dancer",
        costume="a silver cape with bright blue boots",
        shoe_phrase="shiny tap shoes that clicked like tiny drums",
        entry_line="The band was waiting for Thunder Tap to start the first brave stomp.",
        finale="Soon the blue boots were clacking across the stage like friendly thunder.",
        clarifiers={"tap_shoes", "count_in", "poster"},
        tags={"dance", "tap_shoes"},
    ),
    "comet_boots": Act(
        id="comet_boots",
        title="Comet Boots",
        dancer_label="the Comet Boots dancer",
        costume="a gold mask and red lightning boots",
        shoe_phrase="red rhythm boots with little metal plates on the soles",
        entry_line="Everyone was ready for Comet Boots to burst out in a shower of stomps.",
        finale="In a blink, the red boots flashed, stomped, and spun under the lights.",
        clarifiers={"tap_shoes", "poster"},
        tags={"dance", "tap_shoes"},
    ),
    "galaxy_stomp": Act(
        id="galaxy_stomp",
        title="Galaxy Stomp",
        dancer_label="the Galaxy Stomp dancer",
        costume="a purple suit sprinkled with paper stars",
        shoe_phrase="black stage shoes made for loud, proud steps",
        entry_line="The drummer kept lifting the sticks, waiting for Galaxy Stomp to answer the beat.",
        finale="Then the stage boomed with proud steps, like stars knocking at the night.",
        clarifiers={"count_in", "poster"},
        tags={"dance", "drum"},
    ),
}

HOOF_CLUES = {
    "pony_ring": HoofClue(
        id="pony_ring",
        label="the pony ring",
        place="the pony ring",
        mistaken_noun="pony",
        reason="small ponies were circling there with ribbons in their manes",
        tags={"pony"},
    ),
    "petting_gate": HoofClue(
        id="petting_gate",
        label="the petting-yard gate",
        place="the petting-yard gate",
        mistaken_noun="goat",
        reason="a goat inside kept clopping its little hooves on the wooden ramp",
        tags={"goat"},
    ),
    "wagon_team": HoofClue(
        id="wagon_team",
        label="the wagon team",
        place="the wagon team",
        mistaken_noun="parade horse",
        reason="two parade horses were stamping beside a flowered wagon",
        tags={"horse", "parade"},
    ),
    "hobby_horses": HoofClue(
        id="hobby_horses",
        label="the box of hobby horses",
        place="the box of hobby horses",
        mistaken_noun="horse prop",
        reason="painted hobby horses were sticking out of a cardboard box",
        tags={"horse", "school"},
    ),
}

CLARIFIERS = {
    "tap_shoes": Clarifier(
        id="tap_shoes",
        label="the tapping shoes",
        clue_text="a pair of stage shoes clicking on the floor",
        correction='A hoofer is a dancer with lively feet, not an animal.',
        redirect="The real helper was the dancer, not something with hooves.",
        tags={"tap_shoes"},
    ),
    "poster": Clarifier(
        id="poster",
        label="the show poster",
        clue_text='a poster with the word "hoofer" printed under a picture of a dancing hero',
        correction='The poster showed that the hoofer was the dancer in the act.',
        redirect="The word was about a performer, not a pony or goat.",
        tags={"poster"},
    ),
    "count_in": Clarifier(
        id="count_in",
        label="the drummer's count",
        clue_text='the drummer calling, "One, two, three, four!" for a dance entrance',
        correction='That count was for stepping onto the stage, so the hoofer had to be a dancer.',
        redirect="The missing person was the one who would answer the beat with dancing feet.",
        tags={"drum"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Ava", "Zoe", "Nora", "Ruby", "Ella", "Ivy", "June", "Skye"]
BOY_NAMES = ["Max", "Leo", "Finn", "Theo", "Eli", "Sam", "Jack", "Noah", "Ben", "Owen"]
TRAITS = ["brave", "eager", "quick", "cheerful", "curious", "helpful"]


def misunderstanding_possible(setting: Setting, clue: HoofClue) -> bool:
    return clue.id in setting.hoof_clues


def clarification_possible(setting: Setting, act: Act, clarifier: Clarifier) -> bool:
    return clarifier.id in setting.clarifiers and clarifier.id in act.clarifiers


def valid_combo(setting: Setting, act: Act, clue: HoofClue, clarifier: Clarifier) -> bool:
    return misunderstanding_possible(setting, clue) and clarification_possible(setting, act, clarifier)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for aid, act in ACTS.items():
            for cid, clue in HOOF_CLUES.items():
                for lid, clarifier in CLARIFIERS.items():
                    if valid_combo(setting, act, clue, clarifier):
                        combos.append((sid, aid, cid, lid))
    return combos


def _do_wrong_search(world: World) -> None:
    hero = world.get("hero")
    hero.meters["wrong_search"] += 1
    hero.memes["misunderstanding"] += 1
    propagate(world, narrate=False)


def _do_clarify(world: World) -> None:
    hero = world.get("hero")
    hero.meters["saw_clue"] += 1
    propagate(world, narrate=False)


def _do_guide_dancer(world: World) -> None:
    dancer = world.get("dancer")
    dancer.meters["guided"] += 1
    propagate(world, narrate=False)


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} wore a paper cape and called {hero.pronoun('object')}self Spark Sprint, "
        f"the fastest helper in {setting.label}. {friend.id} stayed close beside "
        f"{hero.pronoun('object')}, ready to be the team's calm sidekick."
    )
    world.say(
        f"At {setting.label}, there were {setting.scene}. From {setting.hero_spot}, "
        f"the whole evening looked like a superhero mission waiting to happen."
    )


def announce(world: World, adult: Entity, act: Act, setting: Setting) -> None:
    stage = world.get("stage")
    stage.meters["missing_dancer"] += 1
    hero = world.get("hero")
    hero.meters["heard_call"] += 1
    world.say(
        f"Then {setting.announcer_place} crackled. "
        f'"Calling for the hoofer for {act.title}!" said the {adult.label_word}. '
        f"{act.entry_line}"
    )


def misread(world: World, hero: Entity, friend: Entity, clue: HoofClue) -> None:
    _do_wrong_search(world)
    world.facts["mistaken_noun"] = clue.mistaken_noun
    world.say(
        f"{hero.id}'s eyes grew wide. Nearby, {clue.reason}. "
        f'"A hoofer!" {hero.pronoun().capitalize()} gasped. '
        f'"They must need a {clue.mistaken_noun} for the rescue act!"'
    )
    if world.get("stage").meters["delay"] >= THRESHOLD:
        world.say(
            f"Before {friend.id} could ask what {hero.pronoun()} meant, "
            f"{hero.id} dashed toward {clue.place}, with {friend.id} hurrying after "
            f"{hero.pronoun('object')}."
        )


def worry(world: World, friend: Entity, hero: Entity, clue: HoofClue) -> None:
    friend.memes["worry"] += 1
    world.say(
        f'"Wait!" called {friend.id}. "Maybe they do not mean something with hooves." '
        f"But {hero.id} was already peering around {clue.place}, certain the mission "
        f"was to find the missing {clue.mistaken_noun}."
    )


def clarify(world: World, friend: Entity, hero: Entity, act: Act, clarifier: Clarifier) -> None:
    _do_clarify(world)
    world.say(
        f"Then they heard {clarifier.clue_text}. {friend.id} pointed at it and said, "
        f'"Look, {hero.id} -- {clarifier.correction}"'
    )
    if hero.memes["understanding"] >= THRESHOLD:
        world.say(
            f"{hero.id} stopped so fast that {hero.pronoun('possessive')} cape gave a tiny flap. "
            f"{hero.pronoun().capitalize()} felt heat in {hero.pronoun('possessive')} cheeks. "
            f'"Oh," {hero.pronoun()} said. "{clarifier.redirect}"'
        )
    world.facts["clarified_by"] = clarifier.label


def redirect(world: World, hero: Entity, friend: Entity, act: Act) -> None:
    _do_guide_dancer(world)
    dancer = world.get("dancer")
    hero.memes["helpfulness"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"At once, {hero.id} spun around and spotted {dancer.label} behind the curtain, "
        f"still tugging straight {act.costume}. "
        f'"This way!" {hero.id} cried. "{friend.id} and I can clear the path!"'
    )
    if world.get("stage").meters["ready"] >= THRESHOLD:
        world.say(
            f"They raced back together. {hero.id} held the curtain wide, "
            f"{friend.id} waved everyone aside, and the dancer reached the stage "
            f"just in time."
        )


def finale(world: World, hero: Entity, friend: Entity, adult: Entity, act: Act) -> None:
    hero.memes["relief"] += 1
    friend.memes["joy"] += 1
    adult.memes["gratitude"] += 1
    world.say(
        f"The {adult.label_word} smiled down at them. "
        f'"That was real superhero helping," {adult.pronoun()} said. '
        f'"You listened, you learned, and then you saved the entrance."'
    )
    world.say(
        f"{act.finale} The crowd clapped, and {hero.id}'s cape no longer felt like a costume. "
        f"It felt like a promise to listen before leaping."
    )


def tell(
    setting: Setting,
    act: Act,
    clue: HoofClue,
    clarifier: Clarifier,
    hero_name: str = "Luna",
    hero_gender: str = "girl",
    friend_name: str = "Max",
    friend_gender: str = "boy",
    adult_type: str = "mother",
    hero_trait: str = "brave",
) -> World:
    world = World(setting=setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait],
        attrs={"name": hero_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=["steady"],
        attrs={"name": friend_name},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label="the announcer",
        role="adult",
    ))
    dancer = world.add(Entity(
        id="dancer",
        kind="character",
        type="person",
        label=act.dancer_label,
        role="dancer",
    ))
    stage = world.add(Entity(
        id="stage",
        kind="thing",
        type="stage",
        label="the stage",
        role="stage",
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="thing",
        type="crowd",
        label="the crowd",
        role="crowd",
    ))

    introduce(world, hero, friend, setting)
    world.para()
    announce(world, adult, act, setting)
    misread(world, hero, friend, clue)
    worry(world, friend, hero, clue)
    world.para()
    clarify(world, friend, hero, act, clarifier)
    redirect(world, hero, friend, act)
    world.para()
    finale(world, hero, friend, adult, act)

    world.facts.update(
        setting=setting,
        act=act,
        hoof_clue=clue,
        clarifier=clarifier,
        hero=hero,
        friend=friend,
        adult=adult,
        dancer=dancer,
        stage=stage,
        crowd=crowd,
        mistaken=clue.mistaken_noun,
        misunderstood=hero.memes["understanding"] >= THRESHOLD,
        resolved=stage.meters["ready"] >= THRESHOLD,
        delay=stage.meters["delay"] >= THRESHOLD,
        learning="listen before leaping",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    act = f["act"]
    clue = f["hoof_clue"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the word "hoofer" and turns on a misunderstanding.',
        f"Tell a gentle superhero-style story where {hero.label} hears that someone needs a hoofer at {setting.label}, mistakes it for a {clue.mistaken_noun}, and then fixes the mix-up in time for {act.title}.",
        f"Write a child-facing story with a bold helper, a careful friend named {friend.label}, a funny misunderstanding, and an ending that teaches listening before rushing ahead.",
    ]


KNOWLEDGE = {
    "hoofer": [(
        "What can the word hoofer mean?",
        "Hoofer is an old word for a dancer with lively feet. It sounds like it should mean something with hooves, so it can be easy to misunderstand."
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone hears or understands something the wrong way. The best fix is to slow down, ask a question, and listen again."
    )],
    "tap_shoes": [(
        "Why do tap shoes make clicking sounds?",
        "Tap shoes have hard pieces on the bottom that strike the floor. That makes bright clicking sounds that match a dance beat."
    )],
    "poster": [(
        "How can a poster help someone understand something?",
        "A poster can show pictures and words together. That can make the meaning clearer when a spoken word is confusing."
    )],
    "drum": [(
        "Why does a drummer count before a dance?",
        "The count helps everyone start together. It tells the dancer exactly when to step in."
    )],
    "pony": [(
        "What is a pony?",
        "A pony is a small kind of horse. It has hooves, but it is not the same thing as a stage dancer."
    )],
    "goat": [(
        "What are hooves?",
        "Hooves are the hard feet that some animals have, like goats and horses. They make clopping sounds on wood or stone."
    )],
    "horse": [(
        "What is special about a parade horse?",
        "A parade horse is trained to stay calm around people, music, and wagons. Even so, it is still an animal, not a performer in every act."
    )],
    "parade": [(
        "What happens in a parade?",
        "People and floats move along a route while others watch and cheer. There can be music, costumes, and careful helpers all along the way."
    )],
}
KNOWLEDGE_ORDER = ["hoofer", "misunderstanding", "tap_shoes", "poster", "drum", "pony", "goat", "horse", "parade"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    setting = f["setting"]
    act = f["act"]
    clue = f["hoof_clue"]
    clarifier = f["clarifier"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who was pretending to be a superhero, and {friend.label}, the sidekick who stayed close. They were at {setting.label}, where a stage show was about to begin."
        ),
        (
            f"Why did {hero.label} make a mistake about the word hoofer?",
            f"{hero.label} only heard the call quickly and then noticed {clue.reason}. Because of that hoof clue, {hero.pronoun().capitalize()} guessed that hoofer meant a {clue.mistaken_noun} instead of a dancer."
        ),
        (
            "What was the misunderstanding in the story?",
            f"The misunderstanding was that the grown-ups needed a dancer for {act.title}, but {hero.label} thought they needed a {clue.mistaken_noun}. The mix-up happened because the word hoofer sounded like it should be about hooves."
        ),
    ]
    if f.get("delay"):
        qa.append((
            "What problem did the misunderstanding cause?",
            f"It sent {hero.label} running to the wrong place, so the stage had to wait a moment longer. The crowd began to worry because the dancer had not come out yet."
        ))
    qa.append((
        f"How did {friend.label} help fix the mistake?",
        f"{friend.label} pointed out {clarifier.clue_text} and explained the real meaning. That clue helped {hero.label} understand that the hoofer was the dancer, not an animal."
    ))
    if f.get("resolved"):
        qa.append((
            f"What did {hero.label} do after understanding the mistake?",
            f"{hero.pronoun().capitalize()} turned around at once and helped guide {act.dancer_label} to the stage. By changing direction quickly, {hero.label} still became a real helper."
        ))
        qa.append((
            "How did the story end?",
            f"The dance began, the crowd clapped, and {hero.label} learned to listen before leaping. The ending shows that being heroic means fixing mistakes kindly and fast."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"hoofer", "misunderstanding"}
    clue = world.facts["hoof_clue"]
    clarifier = world.facts["clarifier"]
    setting = world.facts["setting"]
    tags |= clue.tags
    tags |= clarifier.tags
    tags |= setting.tags
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        bits = [f'label="{e.label}"']
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moonlight_fair",
        act="thunder_tap",
        hoof_clue="pony_ring",
        clarifier="tap_shoes",
        hero_name="Luna",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        adult_type="mother",
        hero_trait="brave",
    ),
    StoryParams(
        setting="river_parade",
        act="comet_boots",
        hoof_clue="wagon_team",
        clarifier="tap_shoes",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        adult_type="father",
        hero_trait="eager",
    ),
    StoryParams(
        setting="hero_school_show",
        act="galaxy_stomp",
        hoof_clue="hobby_horses",
        clarifier="count_in",
        hero_name="Ivy",
        hero_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        adult_type="mother",
        hero_trait="quick",
    ),
    StoryParams(
        setting="moonlight_fair",
        act="comet_boots",
        hoof_clue="petting_gate",
        clarifier="poster",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="June",
        friend_gender="girl",
        adult_type="father",
        hero_trait="helpful",
    ),
    StoryParams(
        setting="river_parade",
        act="galaxy_stomp",
        hoof_clue="pony_ring",
        clarifier="count_in",
        hero_name="Skye",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        adult_type="mother",
        hero_trait="cheerful",
    ),
]


def explain_rejection(setting: Setting, act: Act, clue: HoofClue, clarifier: Clarifier) -> str:
    if not misunderstanding_possible(setting, clue):
        return (
            f"(No story: at {setting.label}, {clue.label} is not nearby enough to make "
            f'the word "hoofer" sound honestly confusing. Pick a setting with a clearer hoof clue.)'
        )
    if not clarification_possible(setting, act, clarifier):
        return (
            f"(No story: {clarifier.label} does not fit both {setting.label} and the act "
            f"{act.title}. The misunderstanding needs a believable clue that can clear it up.)"
        )
    return "(No story: this combination does not make a reasonable misunderstanding.)"


ASP_RULES = r"""
supports_misunderstanding(S, C) :- setting(S), hoof_clue(C), has_hoof_clue(S, C).
supports_clarification(S, A, L) :- setting(S), act(A), clarifier(L),
                                   setting_has_clarifier(S, L),
                                   act_has_clarifier(A, L).

valid(S, A, C, L) :- supports_misunderstanding(S, C),
                     supports_clarification(S, A, L).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cid in sorted(setting.hoof_clues):
            lines.append(asp.fact("has_hoof_clue", sid, cid))
        for lid in sorted(setting.clarifiers):
            lines.append(asp.fact("setting_has_clarifier", sid, lid))
    for aid, act in ACTS.items():
        lines.append(asp.fact("act", aid))
        for lid in sorted(act.clarifiers):
            lines.append(asp.fact("act_has_clarifier", aid, lid))
    for cid in HOOF_CLUES:
        lines.append(asp.fact("hoof_clue", cid))
    for lid in CLARIFIERS:
        lines.append(asp.fact("clarifier", lid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases: list[StoryParams] = [CURATED[0]]
    try:
        default_args = build_parser().parse_args([])
        smoke_cases.append(resolve_params(default_args, random.Random(7)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE setup failed: {err}")

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=False, qa=True, header=f"smoke {i}")
            print(f"OK: smoke story {i} generated and emitted.")
        except Exception as err:
            rc = 1
            print(f"SMOKE generation failed for case {i}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero misunderstanding about the word 'hoofer'. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--hoof-clue", dest="hoof_clue", choices=HOOF_CLUES)
    ap.add_argument("--clarifier", choices=CLARIFIERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", dest="adult_type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.act and args.hoof_clue and args.clarifier:
        setting = SETTINGS[args.setting]
        act = ACTS[args.act]
        clue = HOOF_CLUES[args.hoof_clue]
        clarifier = CLARIFIERS[args.clarifier]
        if not valid_combo(setting, act, clue, clarifier):
            raise StoryError(explain_rejection(setting, act, clue, clarifier))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.act is None or combo[1] == args.act)
        and (args.hoof_clue is None or combo[2] == args.hoof_clue)
        and (args.clarifier is None or combo[3] == args.clarifier)
    ]
    if not combos:
        if args.setting and args.act and args.hoof_clue and args.clarifier:
            raise StoryError(explain_rejection(
                SETTINGS[args.setting],
                ACTS[args.act],
                HOOF_CLUES[args.hoof_clue],
                CLARIFIERS[args.clarifier],
            ))
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, act_id, clue_id, clarifier_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    adult_type = args.adult_type or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        act=act_id,
        hoof_clue=clue_id,
        clarifier=clarifier_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_type=adult_type,
        hero_trait=hero_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.act not in ACTS:
        raise StoryError(f"(Unknown act: {params.act})")
    if params.hoof_clue not in HOOF_CLUES:
        raise StoryError(f"(Unknown hoof clue: {params.hoof_clue})")
    if params.clarifier not in CLARIFIERS:
        raise StoryError(f"(Unknown clarifier: {params.clarifier})")

    setting = SETTINGS[params.setting]
    act = ACTS[params.act]
    clue = HOOF_CLUES[params.hoof_clue]
    clarifier = CLARIFIERS[params.clarifier]
    if not valid_combo(setting, act, clue, clarifier):
        raise StoryError(explain_rejection(setting, act, clue, clarifier))

    world = tell(
        setting=setting,
        act=act,
        clue=clue,
        clarifier=clarifier,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult_type,
        hero_trait=params.hero_trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, act, hoof_clue, clarifier) combos:\n")
        for setting, act, clue, clarifier in combos:
            print(f"  {setting:16} {act:13} {clue:13} {clarifier}")
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
                f"### {p.hero_name} & {p.friend_name}: {p.act} at {p.setting} "
                f"({p.hoof_clue}, {p.clarifier})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
