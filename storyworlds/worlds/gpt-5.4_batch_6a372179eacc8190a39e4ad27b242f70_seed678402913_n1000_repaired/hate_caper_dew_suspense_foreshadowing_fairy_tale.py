#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hate_caper_dew_suspense_foreshadowing_fairy_tale.py
==============================================================================

A standalone story world for a small fairy-tale domain built from the seed
words "hate, caper, dew" with suspense and foreshadowing.

Premise
-------
In a dawn-touched fairy garden, a grumpy creature commits a small caper: it
steals the magical thing that wakes the morning. The theft grows from hate or
hurt feelings. A child-sized hero, helped by a clue-reader, must find the lost
thing before sunrise fails. The story resolves either through a caught thief or
a softened confession, proving that hate can shrink when truth is spoken.

Design notes
------------
This world keeps a tight constraint set:

* Every story includes:
  - the word "hate" as a feeling that causes trouble,
  - the word "caper" as the sneaky theft,
  - the word "dew" as part of the setting and the clue system.
* A guide can only solve a hiding place when its method can honestly reveal it.
* Outcome is state-driven:
  - some guides merely expose the thief,
  - gentler guides can draw out a confession from a soft-hearted trickster.
* The prose deliberately uses foreshadowing and suspense as authored beats:
  bent stems, trembling dew, hushed waiting, and a race against dawn.

Run it
------
python storyworlds/worlds/gpt-5.4/hate_caper_dew_suspense_foreshadowing_fairy_tale.py
python storyworlds/worlds/gpt-5.4/hate_caper_dew_suspense_foreshadowing_fairy_tale.py --all
python storyworlds/worlds/gpt-5.4/hate_caper_dew_suspense_foreshadowing_fairy_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/hate_caper_dew_suspense_foreshadowing_fairy_tale.py --asp
python storyworlds/worlds/gpt-5.4/hate_caper_dew_suspense_foreshadowing_fairy_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CONFESS_KINDNESS_MIN = 2


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "fairy", "queen"}
        male = {"boy", "man", "king", "gnome"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Realm:
    id: str
    place: str
    dawn_image: str
    hush_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DawnThing:
    id: str
    label: str
    phrase: str
    duty: str
    wake_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    clue_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    phrase: str
    method: str
    kindness: int
    reveals: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trickster:
    id: str
    label: str
    phrase: str
    type: str
    grievance: str
    confession_line: str
    softenable: bool = False
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

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


def _r_missing_gloom(world: World) -> list[str]:
    treasure = world.entities.get("treasure")
    realm = world.entities.get("realm")
    hero = world.entities.get("hero")
    if not treasure or not realm or not hero:
        return []
    if treasure.meters["missing"] < THRESHOLD:
        return []
    sig = ("gloom", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    realm.meters["gloom"] += 1
    hero.memes["worry"] += 1
    return ["__gloom__"]


def _r_found_hope(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if not hero:
        return []
    if hero.meters["trail_found"] < THRESHOLD:
        return []
    sig = ("hope", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hope"] += 1
    return []


def _r_confession_melts_hate(world: World) -> list[str]:
    trickster = world.entities.get("trickster")
    hero = world.entities.get("hero")
    if not trickster or not hero:
        return []
    if trickster.memes["confessed"] < THRESHOLD:
        return []
    sig = ("melt_hate", trickster.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if trickster.memes["hate"] >= THRESHOLD:
        trickster.memes["hate"] = max(0.0, trickster.memes["hate"] - 1.0)
    hero.memes["mercy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_gloom", tag="physical", apply=_r_missing_gloom),
    Rule(name="found_hope", tag="emotional", apply=_r_found_hope),
    Rule(name="confession_melts_hate", tag="emotional", apply=_r_confession_melts_hate),
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
        for sent in produced:
            world.say(sent)
    return produced


def reveal_possible(guide: Guide, hideout: Hideout) -> bool:
    return bool(set(guide.reveals) & set(hideout.clue_tags))


def can_confess(trickster: Trickster, guide: Guide) -> bool:
    return trickster.softenable and guide.kindness >= CONFESS_KINDNESS_MIN


def outcome_of(params: "StoryParams") -> str:
    if not reveal_possible(GUIDES[params.guide], HIDEOUTS[params.hideout]):
        return "invalid"
    return "confessed" if can_confess(TRICKSTERS[params.trickster], GUIDES[params.guide]) else "caught"


def predict_gloom(world: World) -> dict:
    sim = world.copy()
    treasure = sim.get("treasure")
    treasure.meters["missing"] += 1
    propagate(sim, narrate=False)
    return {
        "gloom": sim.get("realm").meters["gloom"],
        "worry": sim.get("hero").memes["worry"],
    }


def introduce(world: World, hero: Entity, realm: Realm, treasure: DawnThing) -> None:
    hero.memes["care"] += 1
    world.say(
        f"In {realm.place}, where {realm.dawn_image}, lived {hero.id}, a small keeper of dawn."
    )
    world.say(
        f"Each morning, {hero.pronoun()} carried {treasure.phrase}, and {treasure.duty}."
    )


def foreshadow(world: World, realm: Realm) -> None:
    world.say(
        f"On the night this tale began, {realm.hush_image}. Silver dew held to every blade of grass "
        f"so tightly that it seemed to be listening."
    )
    world.say(
        "A bent fern near the path should have warned someone that a secret had already passed that way."
    )


def grievance(world: World, trickster: Entity, cfg: Trickster) -> None:
    trickster.memes["hate"] += 1
    world.say(
        f"But not every heart in the garden was light. {trickster.id}, {cfg.phrase}, "
        f"let hate grow in silence because {cfg.grievance}."
    )


def caper(world: World, trickster: Entity, treasure: Entity, hideout: Hideout) -> None:
    trickster.memes["cunning"] += 1
    treasure.meters["missing"] += 1
    treasure.attrs["hideout"] = hideout.id
    propagate(world, narrate=False)
    world.say(
        f"Before moonset, {trickster.id} crept to the crystal stand, snatched the {treasure.label}, "
        f"and tucked it away {hideout.phrase}. It was a caper so small and quick that even the moths "
        f"went on sleeping."
    )


def discover(world: World, hero: Entity, treasure: Entity, realm: Realm) -> None:
    pred = predict_gloom(world)
    world.facts["predicted_gloom"] = pred["gloom"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"When the east was only a pale seam in the dark, {hero.id} reached for the {treasure.label} and found "
        f"the stand empty."
    )
    if pred["gloom"] >= THRESHOLD:
        world.say(
            f"At once the garden felt wrong. {realm.place.capitalize()} waited in a hush, as if dawn itself were "
            f"holding its breath."
        )


def ask_guide(world: World, hero: Entity, guide: Entity, cfg: Guide, hideout: Hideout) -> None:
    hero.memes["trust"] += 1
    world.say(
        f'"Something has stolen the morning," whispered {hero.id}. "{cfg.label.capitalize()}, will you help me?"'
    )
    world.say(
        f"{guide.id.capitalize()} nodded and used {cfg.method}. For a long moment, nothing moved except the dew."
    )
    if reveal_possible(cfg, hideout):
        hero.meters["trail_found"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Then {guide.id} found the sign: a true clue leading toward {hideout.label}. "
            f"The smallest sparkle became the surest path."
        )
    else:
        world.say(
            f"But {guide.id} found no honest clue at all. This guide could not read that hiding place."
        )


def recover_caught(world: World, hero: Entity, trickster: Entity, treasure: Entity,
                   hideout: Hideout, treasure_cfg: DawnThing) -> None:
    trickster.memes["shame"] += 1
    treasure.meters["missing"] = 0.0
    treasure.meters["restored"] += 1
    world.say(
        f"Behind {hideout.phrase}, {hero.id} found {trickster.id} crouched over the {treasure.label}. "
        f'"Stop!" cried {hero.id}. The word rang louder than a trumpet in the still place.'
    )
    world.say(
        f"{trickster.id.capitalize()} froze. Under the cold dew, the caper no longer looked clever at all."
    )
    world.say(
        f"{hero.id} lifted the {treasure.label} high and hurried back before the last star could fade. "
        f"Soon {treasure_cfg.wake_line}"
    )


def recover_confessed(world: World, hero: Entity, trickster: Entity, treasure: Entity,
                      treasure_cfg: DawnThing, hideout: Hideout, cfg: Trickster) -> None:
    trickster.memes["confessed"] += 1
    trickster.memes["shame"] += 1
    treasure.meters["missing"] = 0.0
    treasure.meters["restored"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At {hideout.label}, {hero.id} found {trickster.id} with the {treasure.label} clasped tight."
    )
    world.say(
        f"Before {hero.id} could speak, {trickster.id} lowered {trickster.pronoun('possessive')} head. "
        f'"{cfg.confession_line}"'
    )
    world.say(
        f"The words came out shaky, but once they were spoken, the hate in {trickster.id}'s chest seemed smaller. "
        f"{hero.id} held out {hero.pronoun('possessive')} hands, and together they carried the {treasure.label} back."
    )
    world.say(
        f"Soon {treasure_cfg.wake_line}"
    )


def resolution_caught(world: World, hero: Entity, trickster: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["courage"] += 1
    trickster.memes["lesson"] += 1
    world.say(
        f'"Why would you do such a thing?" asked {hero.id}.'
    )
    world.say(
        f'{trickster.id.capitalize()} would not meet {hero.pronoun("possessive")} eyes. '
        f'"I thought if morning stumbled, everyone would finally notice me," {trickster.pronoun()} muttered.'
    )
    world.say(
        f'"Then let them notice a kinder deed next time," said {hero.id}. {trickster.id.capitalize()} nodded, '
        f"looking smaller than before."
    )


def resolution_confessed(world: World, hero: Entity, trickster: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["courage"] += 1
    trickster.memes["lesson"] += 1
    trickster.memes["hope"] += 1
    world.say(
        f'{hero.id} did not pretend the caper was harmless. "Hate nearly kept the whole garden in darkness," '
        f'{hero.pronoun()} said. "But telling the truth is how light comes back."'
    )
    world.say(
        f"{trickster.id.capitalize()} promised to help at dawn instead of stealing from it again."
    )


def ending_image(world: World, realm: Realm, hero: Entity, trickster: Entity,
                 treasure_cfg: DawnThing, outcome: str) -> None:
    if outcome == "confessed":
        world.say(
            f"After that, when dew shone on the grass in {realm.place}, {hero.id} sometimes saw {trickster.id} "
            f"working quietly beside the path. The morning came bright, and the bright part reached further than "
            f"{treasure_cfg.label} alone."
        )
    else:
        world.say(
            f"After that, when dew shone on the grass in {realm.place}, {trickster.id} remembered how a mean thought "
            f"had led to a foolish caper. The morning came bright, and {hero.id} kept watch with a steadier heart."
        )


def tell(realm: Realm, treasure_cfg: DawnThing, hideout: Hideout, guide_cfg: Guide,
         trickster_cfg: Trickster, hero_name: str = "Lina", hero_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["brave", "small"],
    ))
    trickster = world.add(Entity(
        id=trickster_cfg.label,
        kind="character",
        type=trickster_cfg.type,
        label=trickster_cfg.label,
        role="trickster",
        traits=["sly"],
        tags=set(trickster_cfg.tags),
    ))
    guide = world.add(Entity(
        id=guide_cfg.label,
        kind="character",
        type="creature",
        label=guide_cfg.label,
        role="guide",
        traits=["watchful"],
        tags=set(guide_cfg.tags),
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        tags=set(treasure_cfg.tags),
    ))
    realm_ent = world.add(Entity(
        id="realm",
        kind="thing",
        type="realm",
        label=realm.place,
        tags=set(realm.tags),
    ))

    introduce(world, hero, realm, treasure_cfg)
    foreshadow(world, realm)

    world.para()
    grievance(world, trickster, trickster_cfg)
    caper(world, trickster, treasure, hideout)

    world.para()
    discover(world, hero, treasure, realm)
    ask_guide(world, hero, guide, guide_cfg, hideout)

    if not reveal_possible(guide_cfg, hideout):
        raise StoryError(
            f"(No story: {guide_cfg.label} cannot honestly reveal something hidden {hideout.phrase}.)"
        )

    outcome = "confessed" if can_confess(trickster_cfg, guide_cfg) else "caught"

    world.para()
    if outcome == "confessed":
        recover_confessed(world, hero, trickster, treasure, treasure_cfg, hideout, trickster_cfg)
        resolution_confessed(world, hero, trickster)
    else:
        recover_caught(world, hero, trickster, treasure, hideout, treasure_cfg)
        resolution_caught(world, hero, trickster)

    world.para()
    ending_image(world, realm, hero, trickster, treasure_cfg, outcome)

    world.facts.update(
        hero=hero,
        trickster=trickster,
        guide=guide,
        treasure=treasure,
        realm=realm,
        treasure_cfg=treasure_cfg,
        hideout=hideout,
        guide_cfg=guide_cfg,
        trickster_cfg=trickster_cfg,
        outcome=outcome,
        clue_found=hero.meters["trail_found"] >= THRESHOLD,
        gloom=realm_ent.meters["gloom"] >= THRESHOLD,
    )
    return world


REALMS = {
    "rose_garden": Realm(
        id="rose_garden",
        place="the Rose Garden of First Light",
        dawn_image="dew pearls clung to the roses like tiny glass lanterns",
        hush_image="the thorn arches stood as still as sleeping guards",
        tags={"garden", "dew"},
    ),
    "fern_hollow": Realm(
        id="fern_hollow",
        place="the Fern Hollow",
        dawn_image="dew trembled on the fern tips like little stars waiting to fall",
        hush_image="the round stones beside the brook listened in green silence",
        tags={"forest", "dew"},
    ),
    "silver_meadow": Realm(
        id="silver_meadow",
        place="the Silver Meadow",
        dawn_image="dew shone over the meadow as if the moon had dropped a necklace there",
        hush_image="the tall grass swayed so softly it seemed to whisper secrets",
        tags={"meadow", "dew"},
    ),
}

TREASURES = {
    "dew_bell": DawnThing(
        id="dew_bell",
        label="dew bell",
        phrase="the dew bell of morning",
        duty="its clear note woke the roses and told the sun where to pour the first gold",
        wake_line="the dew bell sang, and the roses opened one by one",
        tags={"bell", "dawn"},
    ),
    "sun_key": DawnThing(
        id="sun_key",
        label="sun key",
        phrase="the sun key of the eastern gate",
        duty="it turned the little lock that let the morning over the hill",
        wake_line="the sun key turned, and the east gate opened to a wash of honey light",
        tags={"key", "dawn"},
    ),
    "lark_flute": DawnThing(
        id="lark_flute",
        label="lark flute",
        phrase="the lark flute of daybreak",
        duty="its first note called the birds to stitch the sky with song",
        wake_line="the lark flute trilled, and birdsong lifted all at once into the brightening air",
        tags={"music", "dawn"},
    ),
}

HIDEOUTS = {
    "briar_arch": Hideout(
        id="briar_arch",
        label="the briar arch",
        phrase="behind the briar arch",
        clue_tags={"dew_sparkle"},
        tags={"briar"},
    ),
    "hollow_log": Hideout(
        id="hollow_log",
        label="the hollow log",
        phrase="inside the hollow log",
        clue_tags={"birdsong", "snail_gloss"},
        tags={"log"},
    ),
    "toadstool_ring": Hideout(
        id="toadstool_ring",
        label="the toadstool ring",
        phrase="under the toadstool ring",
        clue_tags={"dew_sparkle", "snail_gloss"},
        tags={"mushroom"},
    ),
}

GUIDES = {
    "dew_mouse": Guide(
        id="dew_mouse",
        label="Moss-Mouse",
        phrase="a silver-whiskered mouse",
        method="the bright beads of dew on bent grass",
        kindness=1,
        reveals={"dew_sparkle"},
        tags={"mouse", "dew"},
    ),
    "robin": Guide(
        id="robin",
        label="Red Robin",
        phrase="a robin with a red breast",
        method="the tale hidden in rustled bark and worried birdsong",
        kindness=2,
        reveals={"birdsong"},
        tags={"bird"},
    ),
    "snail": Guide(
        id="snail",
        label="Old Snail",
        phrase="an old snail with a shell like a spiral moon",
        method="the glossy silver ribbon left by a slow night traveler",
        kindness=3,
        reveals={"snail_gloss"},
        tags={"snail"},
    ),
}

TRICKSTERS = {
    "boggart": Trickster(
        id="boggart",
        label="Bramble Boggart",
        phrase="the little bramble boggart of the hedge",
        type="creature",
        grievance="the fair folk had laughed when he boasted too loudly at supper",
        confession_line="I hated their laughter, and I wanted morning to miss me when I was gone.",
        softenable=True,
        tags={"boggart"},
    ),
    "crow": Trickster(
        id="crow",
        label="Black Crow",
        phrase="the black crow from the thorn gate",
        type="creature",
        grievance="he could not bear that the whole garden praised dawn and not his own cleverness",
        confession_line="I wanted the song for myself.",
        softenable=False,
        tags={"crow"},
    ),
    "weasel": Trickster(
        id="weasel",
        label="Sable Weasel",
        phrase="the sable weasel under the roots",
        type="creature",
        grievance="she hated being left out whenever the dawn keepers danced",
        confession_line="I thought if I spoiled the dance, nobody would forget me again.",
        softenable=True,
        tags={"weasel"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for realm_id in REALMS:
        for treasure_id in TREASURES:
            for hideout_id, hideout in HIDEOUTS.items():
                for guide_id, guide in GUIDES.items():
                    if not reveal_possible(guide, hideout):
                        continue
                    for trickster_id in TRICKSTERS:
                        combos.append((realm_id, treasure_id, hideout_id, guide_id, trickster_id))
    return combos


@dataclass
class StoryParams:
    realm: str
    treasure: str
    hideout: str
    guide: str
    trickster: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "dew": [
        (
            "What is dew?",
            "Dew is tiny drops of water that gather on grass and leaves when the air turns cool at night. In the morning it can sparkle like little jewels."
        )
    ],
    "bell": [
        (
            "What does a bell do in a fairy tale?",
            "A bell can call, warn, or wake things with its sound. In fairy tales, one clear ring can matter to a whole garden or kingdom."
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key opens something that is shut. In stories, a special key can let in light, unlock a gate, or start an important change."
        )
    ],
    "music": [
        (
            "Why do stories use music at dawn?",
            "Music can show that a new day has begun. A bright note makes the world feel awake and ready."
        )
    ],
    "briar": [
        (
            "What is a briar?",
            "A briar is a thorny plant with tangled stems. It can hide things well because it is prickly and thick."
        )
    ],
    "log": [
        (
            "What is a hollow log?",
            "A hollow log is a fallen tree trunk with an empty space inside. Small animals sometimes hide or nest there."
        )
    ],
    "mushroom": [
        (
            "What is a toadstool ring?",
            "A toadstool ring is a circle of mushrooms. Fairy tales often treat such circles as strange and magical places."
        )
    ],
    "bird": [
        (
            "How can a bird help in a story?",
            "A bird can notice things from above and hear sounds from far away. That makes it a good watcher and messenger."
        )
    ],
    "mouse": [
        (
            "Why might a mouse notice clues in grass?",
            "A mouse is close to the ground, so bent stems and tiny tracks are easy for it to see. Small clues can look big from a mouse's height."
        )
    ],
    "snail": [
        (
            "What kind of trail does a snail leave?",
            "A snail leaves a thin shiny trail. In morning light it can glimmer and show where the snail has gone."
        )
    ],
    "forgive": [
        (
            "What does it mean to forgive someone?",
            "Forgiving means letting go of the wish to stay angry after someone truly admits a wrong and tries to do better. It does not mean pretending the wrong never happened."
        )
    ],
}
KNOWLEDGE_ORDER = ["dew", "bell", "key", "music", "briar", "log", "mushroom", "bird", "mouse", "snail", "forgive"]

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Tansy", "Nella", "Poppy", "Iris", "Wren"]
BOY_NAMES = ["Rowan", "Finn", "Alder", "Milo", "Pip", "Robin", "Elm", "Nico"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    guide_cfg = f["guide_cfg"]
    treasure_cfg = f["treasure_cfg"]
    trickster_cfg = f["trickster_cfg"]
    hideout = f["hideout"]
    outcome = f["outcome"]
    out = [
        'Write a fairy tale for a 3-to-5-year-old that includes the words "hate", "caper", and "dew".',
        f"Tell a suspenseful fairy tale where {hero.id} must find a stolen {treasure_cfg.label} before morning fully wakes.",
        f"Write a gentle story with foreshadowing: bent grass, listening dew, and a clue that leads to {hideout.label}.",
    ]
    if outcome == "confessed":
        out.append(
            f"Include a soft-hearted ending where {trickster_cfg.label} admits the caper after {guide_cfg.label} helps uncover the truth."
        )
    else:
        out.append(
            f"Include a tense ending where {guide_cfg.label} helps catch {trickster_cfg.label} after the caper."
        )
    return out


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    trickster = f["trickster"]
    guide = f["guide"]
    treasure = f["treasure"]
    realm = f["realm"]
    treasure_cfg = f["treasure_cfg"]
    hideout = f["hideout"]
    trickster_cfg = f["trickster_cfg"]
    guide_cfg = f["guide_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a small keeper of dawn, and {trickster.id}, who steals the {treasure.label}. {guide.id} helps {hero.id} search before morning is lost."
        ),
        (
            f"What was stolen in the story?",
            f"The stolen thing was the {treasure.label}. It mattered because {treasure_cfg.duty}."
        ),
        (
            "Why did the garden feel so tense after the theft?",
            f"The {treasure.label} was missing just before dawn, so the whole place seemed to wait in silence. That suspense came from not knowing whether morning would wake in time."
        ),
        (
            "What was the foreshadowing at the start?",
            "The story showed listening dew and a bent fern before anyone knew about the theft. Those details quietly warned that someone had already slipped through the garden."
        ),
        (
            f"How did {guide.id} help find the thief?",
            f"{guide.id} used {guide_cfg.method} to read the garden carefully. That clue led {hero.id} toward {hideout.label}."
        ),
        (
            f"Why did {trickster.id} steal the {treasure.label}?",
            f"{trickster.id} acted out of hate and hurt feelings because {trickster_cfg.grievance}. The caper began as a mean idea inside the heart before it became a real theft."
        ),
    ]
    if outcome == "confessed":
        qa.append(
            (
                f"How was the problem solved?",
                f"{trickster.id} confessed and gave back the {treasure.label}, and then {hero.id} helped carry it home. The truth made room for mercy, so morning could return."
            )
        )
        qa.append(
            (
                f"What changed in {trickster.id} by the end?",
                f"{trickster.id} stopped hiding behind the caper and spoke the truth aloud. Once the confession came, the hate in {trickster.pronoun('possessive')} heart grew smaller."
            )
        )
    else:
        qa.append(
            (
                "How was the problem solved?",
                f"{hero.id} found {trickster.id} with the {treasure.label} and took it back before dawn failed. Being caught made the caper look foolish instead of clever."
            )
        )
        qa.append(
            (
                f"What lesson did {trickster.id} learn?",
                f"{trickster.id} learned that trying to be noticed through spite only brings shame. A kinder deed would have worked better than stealing from the morning."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"dew"}
    tags |= set(f["treasure_cfg"].tags)
    tags |= set(f["hideout"].tags)
    tags |= set(f["guide_cfg"].tags)
    if f["outcome"] == "confessed":
        tags.add("forgive")
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="rose_garden",
        treasure="dew_bell",
        hideout="briar_arch",
        guide="dew_mouse",
        trickster="crow",
        hero_name="Lina",
        hero_type="girl",
    ),
    StoryParams(
        realm="fern_hollow",
        treasure="sun_key",
        hideout="hollow_log",
        guide="robin",
        trickster="boggart",
        hero_name="Rowan",
        hero_type="boy",
    ),
    StoryParams(
        realm="silver_meadow",
        treasure="lark_flute",
        hideout="toadstool_ring",
        guide="snail",
        trickster="weasel",
        hero_name="Mira",
        hero_type="girl",
    ),
    StoryParams(
        realm="rose_garden",
        treasure="sun_key",
        hideout="toadstool_ring",
        guide="dew_mouse",
        trickster="crow",
        hero_name="Finn",
        hero_type="boy",
    ),
]


def explain_rejection(guide: Guide, hideout: Hideout) -> str:
    return (
        f"(No story: {guide.label} uses {guide.method}, but that cannot honestly reveal something hidden "
        f"{hideout.phrase}. Choose a guide whose clue fits the hiding place.)"
    )


ASP_RULES = r"""
reveal_possible(G, H) :- guide(G), hideout(H), reveals(G, C), needs_clue(H, C).
valid(R, T, H, G, X) :- realm(R), treasure(T), hideout(H), guide(G), trickster(X), reveal_possible(G, H).

confessed :- chosen_trickster(X), softenable(X), chosen_guide(G), kindness(G, K), confess_kindness_min(M), K >= M.
caught    :- not confessed.

outcome(confessed) :- confessed.
outcome(caught)    :- caught.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id in REALMS:
        lines.append(asp.fact("realm", realm_id))
    for treasure_id in TREASURES:
        lines.append(asp.fact("treasure", treasure_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        for clue in sorted(hideout.clue_tags):
            lines.append(asp.fact("needs_clue", hideout_id, clue))
    for guide_id, guide in GUIDES.items():
        lines.append(asp.fact("guide", guide_id))
        lines.append(asp.fact("kindness", guide_id, guide.kindness))
        for clue in sorted(guide.reveals):
            lines.append(asp.fact("reveals", guide_id, clue))
    for trickster_id, trickster in TRICKSTERS.items():
        lines.append(asp.fact("trickster", trickster_id))
        if trickster.softenable:
            lines.append(asp.fact("softenable", trickster_id))
    lines.append(asp.fact("confess_kindness_min", CONFESS_KINDNESS_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_guide", params.guide),
        asp.fact("chosen_trickster", params.trickster),
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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fairy-tale dawn theft with dew clues, suspense, and foreshadowing."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--trickster", choices=TRICKSTERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.guide and args.hideout:
        if not reveal_possible(GUIDES[args.guide], HIDEOUTS[args.hideout]):
            raise StoryError(explain_rejection(GUIDES[args.guide], HIDEOUTS[args.hideout]))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.guide is None or combo[3] == args.guide)
        and (args.trickster is None or combo[4] == args.trickster)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, treasure_id, hideout_id, guide_id, trickster_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    return StoryParams(
        realm=realm_id,
        treasure=treasure_id,
        hideout=hideout_id,
        guide=guide_id,
        trickster=trickster_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(No story: unknown realm '{params.realm}'.)")
    if params.treasure not in TREASURES:
        raise StoryError(f"(No story: unknown treasure '{params.treasure}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{params.hideout}'.)")
    if params.guide not in GUIDES:
        raise StoryError(f"(No story: unknown guide '{params.guide}'.)")
    if params.trickster not in TRICKSTERS:
        raise StoryError(f"(No story: unknown trickster '{params.trickster}'.)")
    if not reveal_possible(GUIDES[params.guide], HIDEOUTS[params.hideout]):
        raise StoryError(explain_rejection(GUIDES[params.guide], HIDEOUTS[params.hideout]))

    world = tell(
        realm=REALMS[params.realm],
        treasure_cfg=TREASURES[params.treasure],
        hideout=HIDEOUTS[params.hideout],
        guide_cfg=GUIDES[params.guide],
        trickster_cfg=TRICKSTERS[params.trickster],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, treasure, hideout, guide, trickster) combos:\n")
        for realm_id, treasure_id, hideout_id, guide_id, trickster_id in combos:
            print(f"  {realm_id:13} {treasure_id:10} {hideout_id:14} {guide_id:9} {trickster_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.treasure} hidden at {p.hideout} "
                f"({p.realm}, {p.guide}, {p.trickster}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
