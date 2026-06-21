#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/analyze_suspense_repetition_kindness_myth.py
=======================================================================

A standalone storyworld for a small myth-shaped tale built from the seed words
and features:

    Word: analyze
    Features: suspense, repetition, kindness
    Style: myth

This world tells close variations of one domain: on a dusk path, a child hears
a mysterious cry three times, stops to analyze the signs, and finds a small
mythic creature in trouble. The tension comes from the unknown voice and the
darkening world; the repetition comes from the call returning again and again;
the turn comes when the child reads the signs correctly or blunders once before
understanding them; the ending proves that kindness changes the night itself.

Run it
------
    python storyworlds/worlds/gpt-5.4/analyze_suspense_repetition_kindness_myth.py
    python storyworlds/worlds/gpt-5.4/analyze_suspense_repetition_kindness_myth.py --setting moon_pond --creature reed_crane
    python storyworlds/worlds/gpt-5.4/analyze_suspense_repetition_kindness_myth.py --aid wrong_song
    python storyworlds/worlds/gpt-5.4/analyze_suspense_repetition_kindness_myth.py --all
    python storyworlds/worlds/gpt-5.4/analyze_suspense_repetition_kindness_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/analyze_suspense_repetition_kindness_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so the package directory is
# three parents up: storyworlds/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
ANALYTIC_TRAITS = {"thoughtful", "careful", "patient"}


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
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    path: str
    sky: str
    landmark: str
    habitat: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    title: str
    habitat: str
    sign_sound: str
    sign_light: str
    hidden_place: str
    opening_image: str
    thanks: str
    blessing: str
    trouble_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    severity: int
    fix_tag: str
    cause_text: str
    found_text: str
    clue_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear_from_call(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    calls = int(hero.meters["calls_heard"])
    if calls < 2:
        return []
    sig = ("fear", calls)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["wonder"] += 1
    if calls >= 3:
        hero.memes["fear"] += 1
    return []


def _r_analysis_from_repetition(world: World) -> list[str]:
    hero = world.entities.get("hero")
    elder = world.entities.get("elder")
    if hero is None or elder is None:
        return []
    if hero.meters["calls_heard"] < 3 or hero.memes["paused"] < THRESHOLD:
        return []
    sig = ("analysis", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["understanding"] += 1
    elder.memes["trust"] += 1
    return []


def _r_relief_after_help(world: World) -> list[str]:
    hero = world.entities.get("hero")
    creature = world.entities.get("creature")
    if hero is None or creature is None:
        return []
    if creature.meters["helped"] < THRESHOLD:
        return []
    sig = ("relief", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    creature.memes["relief"] += 1
    hero.memes["kindness"] += 1
    hero.memes["fear"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="fear_from_call", tag="meme", apply=_r_fear_from_call),
    Rule(name="analysis_from_repetition", tag="meme", apply=_r_analysis_from_repetition),
    Rule(name="relief_after_help", tag="meme", apply=_r_relief_after_help),
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
            world.say(sent)
    return produced


def trouble_fits(creature: Creature, trouble: Trouble) -> bool:
    return trouble.id in creature.trouble_ids


def aid_can_help(aid: Aid, trouble: Trouble) -> bool:
    return trouble.fix_tag in aid.tags


def sensible_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.sense >= SENSE_MIN]


def outcome_of(params: "StoryParams") -> str:
    trouble = TROUBLES[params.trouble]
    aid = AIDS[params.aid]
    if aid.power < trouble.severity:
        return "waiting_moon"
    if params.trait in ANALYTIC_TRAITS:
        return "great_blessing"
    return "gentle_blessing"


def predict_success(trait: str, trouble: Trouble, aid: Aid) -> dict:
    return {
        "can_help": aid.power >= trouble.severity and aid_can_help(aid, trouble),
        "clear_reading": trait in ANALYTIC_TRAITS,
    }


def opening(world: World, hero: Entity, elder: Entity, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"In the old days, when stories still walked beside the road, {hero.id} "
        f"followed {setting.path} near {setting.place}. Above, {setting.sky}."
    )
    world.say(
        f"{hero.id}'s {elder.label_word} had once said, "
        f'"If the dusk calls to you three times, do not hurry. Stop and analyze the signs."'
    )


def first_signs(world: World, hero: Entity, creature: Creature, trouble: Trouble) -> None:
    for _ in range(3):
        hero.meters["calls_heard"] += 1
        propagate(world, narrate=False)
    world.say(
        f"Then a small sound came from the dark: {creature.sign_sound}. "
        f"{hero.id} stopped and listened."
    )
    world.say(
        f"Again it came -- {creature.sign_sound} -- and {creature.sign_light}."
    )
    world.say(
        f"A third time it came -- {creature.sign_sound} -- and now even the path "
        f"seemed to hold its breath. {trouble.clue_text}"
    )


def choose_path(world: World, hero: Entity, setting: Setting, creature: Creature, trouble: Trouble,
                trait: str) -> None:
    hero.memes["paused"] += 1
    propagate(world, narrate=False)
    if trait in ANALYTIC_TRAITS:
        hero.meters["analyzed"] += 1
        world.say(
            f"{hero.id} did not run. {hero.pronoun().capitalize()} remembered the old advice, "
            f"looked at the bent grass, the dim light, and the little marks by {setting.landmark}, "
            f"and began to analyze what they meant."
        )
        world.say(
            f"At last {hero.pronoun()} understood: the signs pointed toward {creature.hidden_place}, "
            f"and something gentle was in pain there."
        )
        world.facts["false_turn"] = False
    else:
        hero.meters["mistake"] += 1
        hero.memes["fear"] += 1
        world.say(
            f"{hero.id} hurried at first, because the night felt larger with every echo. "
            f"But the shadows led {hero.pronoun('object')} toward the wrong stones, and nothing was there."
        )
        world.say(
            f"Then the cry came again -- {creature.sign_sound} -- soft and thin. "
            f"{hero.id} made {hero.pronoun('object')}self be still, took one slow breath, "
            f"and tried to analyze the signs properly."
        )
        hero.memes["paused"] += 1
        hero.meters["analyzed"] += 1
        propagate(world, narrate=False)
        world.say(
            f"Only then did {hero.pronoun()} notice the true clue: {trouble.clue_text.lower()} "
            f"It led toward {creature.hidden_place}."
        )
        world.facts["false_turn"] = True


def discovery(world: World, hero: Entity, creature_ent: Entity, creature: Creature,
              trouble: Trouble) -> None:
    creature_ent.meters["troubled"] += 1
    world.say(
        f"There, tucked near {creature.hidden_place}, was {creature.opening_image}. "
        f"It was {creature.label}, and {trouble.found_text}"
    )
    world.say(
        f"For a moment {hero.id} felt fear and wonder together, because everyone knew "
        f"that a {creature.title} belonged to the oldest tales."
    )


def help_creature(world: World, hero: Entity, creature_ent: Entity, trouble: Trouble, aid: Aid) -> None:
    creature_ent.meters["helped"] += 1
    creature_ent.meters["troubled"] = 0.0
    world.facts["help_success"] = True
    propagate(world, narrate=False)
    world.say(
        f"But kindness was stronger than fear. {hero.id} took {aid.phrase} and "
        f"{aid.action_text}"
    )
    world.say(
        f"{creature_ent.label.capitalize()} grew still. Then {trouble.cause_text} was over."
    )


def fail_to_help(world: World, hero: Entity, creature_ent: Entity, trouble: Trouble, aid: Aid) -> None:
    world.facts["help_success"] = False
    hero.memes["sorrow"] += 1
    world.say(
        f"{hero.id} tried with {aid.phrase}, but it was the wrong kind of help. "
        f"The trouble would not yield, and the little creature trembled in the reeds."
    )
    world.say(
        f"So {hero.pronoun()} sat beside it instead and promised, "
        f'"I will bring a wiser grown-up before the moon is high."'
    )


def ending(world: World, hero: Entity, elder: Entity, creature_ent: Entity, creature: Creature,
           outcome: str, setting: Setting) -> None:
    if outcome == "great_blessing":
        hero.memes["awe"] += 1
        creature_ent.memes["gratitude"] += 1
        world.say(
            f"The {creature.label} rose, circled {hero.id} once, and {creature.thanks}."
        )
        world.say(
            f'"Because you were kind, and because you stopped to think, {creature.blessing}," '
            f"it whispered."
        )
        world.say(
            f"After that night, people said {setting.place} never looked quite so dark again. "
            f"When {hero.id} walked there, the path always found a little silver of its own."
        )
    elif outcome == "gentle_blessing":
        hero.memes["awe"] += 1
        creature_ent.memes["gratitude"] += 1
        world.say(
            f"The {creature.label} bowed its small head and {creature.thanks}."
        )
        world.say(
            f'"You were frightened, yet you stayed kind," it said. '
            f'"That is why the road will remember your steps."'
        )
        world.say(
            f"From then on, whenever dusk gathered around {hero.id}, a soft glimmer "
            f"would appear ahead, as if the old stories were walking with {hero.pronoun('object')}."
        )
    else:
        elder.memes["care"] += 1
        world.say(
            f"The creature gave a weak little nod, and {hero.id} ran back along {setting.path} "
            f"to fetch {hero.pronoun('possessive')} {elder.label_word}."
        )
        world.say(
            f"Together they returned with wiser hands. By moonrise the trouble was ended, "
            f"and {hero.id} learned that kindness also means knowing when to ask for help."
        )
        world.say(
            f"After that, whenever a strange call came from the dark, {hero.id} listened first "
            f"and never felt ashamed to seek a wiser voice."
        )


def tell(setting: Setting, creature: Creature, trouble: Trouble, aid: Aid,
         hero_name: str = "Nia", hero_type: str = "girl", trait: str = "thoughtful",
         elder_type: str = "grandmother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=[trait],
        attrs={"trait": trait},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    creature_ent = world.add(Entity(
        id="creature",
        kind="character",
        type="spirit",
        label=creature.label,
        phrase=creature.title,
        role="creature",
        tags=set(creature.tags),
    ))
    tool = world.add(Entity(
        id="aid",
        kind="thing",
        type="aid",
        label=aid.label,
        phrase=aid.phrase,
        tags=set(aid.tags),
    ))

    opening(world, hero, elder, setting)
    world.para()
    first_signs(world, hero, creature, trouble)
    choose_path(world, hero, setting, creature, trouble, trait)
    world.para()
    discovery(world, hero, creature_ent, creature, trouble)

    predicted = predict_success(trait, trouble, aid)
    world.facts["predicted"] = predicted

    world.para()
    if predicted["can_help"]:
        help_creature(world, hero, creature_ent, trouble, aid)
    else:
        fail_to_help(world, hero, creature_ent, trouble, aid)

    world.para()
    result = outcome_of(StoryParams(
        setting=setting.id,
        creature=creature.id,
        trouble=trouble.id,
        aid=aid.id,
        name=hero_name,
        gender=hero_type,
        elder=elder_type,
        trait=trait,
        seed=None,
    ))
    ending(world, hero, elder, creature_ent, creature, result, setting)

    world.facts.update(
        hero=hero,
        elder=elder,
        creature_cfg=creature,
        creature=creature_ent,
        trouble=trouble,
        aid=aid,
        setting=setting,
        outcome=result,
        repeated_calls=int(hero.meters["calls_heard"]),
        analyzed=hero.meters["analyzed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moon_pond": Setting(
        id="moon_pond",
        place="Moon Pond",
        path="the willow path",
        sky="the first stars floated like seeds on dark water",
        landmark="the reed gate",
        habitat="reeds",
        tags={"pond", "night"},
    ),
    "cedar_hill": Setting(
        id="cedar_hill",
        place="Cedar Hill",
        path="the root-wound path",
        sky="the moon climbed slowly behind the cedar branches",
        landmark="the old shrine stone",
        habitat="bramble",
        tags={"hill", "cedar"},
    ),
    "moss_cave": Setting(
        id="moss_cave",
        place="Moss Cave",
        path="the dripping stone path",
        sky="the cave mouth held one stripe of evening gold",
        landmark="the green rock arch",
        habitat="moss",
        tags={"cave", "moss"},
    ),
}

CREATURES = {
    "reed_crane": Creature(
        id="reed_crane",
        label="reed crane",
        title="Reed Crane of Moon Pond",
        habitat="reeds",
        sign_sound="a thin, silver peep",
        sign_light="a pale feather-shine blinked low over the water",
        hidden_place="the folded reeds at the pond's edge",
        opening_image="a small white crane-spirit with one wing pinned by a knotted ribbon",
        thanks="brushed the air with its bright wings",
        blessing="the pond will show you safe crossings and true reflections",
        trouble_ids={"tangle"},
        tags={"crane", "reeds"},
    ),
    "moon_fox": Creature(
        id="moon_fox",
        label="moon fox",
        title="Moon Fox of Cedar Hill",
        habitat="bramble",
        sign_sound="a tiny crying bark",
        sign_light="a pearl glow shivered under the thorns",
        hidden_place="the blackberry roots beneath the shrine stone",
        opening_image="a little fox-spirit with moonlit fur, holding one paw tight against its chest",
        thanks="touched its shining nose to the child's hand",
        blessing="the hill will never hide its paths from you",
        trouble_ids={"thorn"},
        tags={"fox", "bramble"},
    ),
    "moss_turtle": Creature(
        id="moss_turtle",
        label="moss turtle",
        title="Moss Turtle of the Cave Spring",
        habitat="moss",
        sign_sound="a hollow tapping like a bead on stone",
        sign_light="a green light trembled and went out, then trembled again",
        hidden_place="the wet moss beside the spring bowl",
        opening_image="a moss-backed turtle-spirit tilted helplessly in a patch of sucking mud",
        thanks="blinked slow bright eyes and let the spring ring once",
        blessing="patient hearts will hear the spring before danger does",
        trouble_ids={"mud"},
        tags={"turtle", "spring"},
    ),
}

TROUBLES = {
    "thorn": Trouble(
        id="thorn",
        label="thorn in a paw",
        severity=1,
        fix_tag="lift",
        cause_text="the thorn slipped free",
        found_text="a black thorn was caught deep in its paw",
        clue_text="A thread of silver fur clung to the thorn-bush there.",
        tags={"thorn", "injury"},
    ),
    "tangle": Trouble(
        id="tangle",
        label="wing tangled in ribbon",
        severity=2,
        fix_tag="untie",
        cause_text="the knot loosened and fell away",
        found_text="a faded red ribbon had twisted around one wing",
        clue_text="A red thread fluttered from the reeds like a tiny flag.",
        tags={"ribbon", "tangle"},
    ),
    "mud": Trouble(
        id="mud",
        label="shell stuck in mud",
        severity=2,
        fix_tag="pull",
        cause_text="the shell came free with a wet sigh",
        found_text="its shell was sunk crooked in a clutch of cold mud",
        clue_text="The stone beside the path was streaked with fresh green mud.",
        tags={"mud", "stuck"},
    ),
}

AIDS = {
    "silver_tongs": Aid(
        id="silver_tongs",
        label="silver tongs",
        phrase="the little silver tongs from a berry pouch",
        power=1,
        sense=3,
        tags={"lift"},
        action_text="gently lifted the thorn away without hurting the small foot.",
        qa_text="used silver tongs to lift the thorn away",
    ),
    "patient_fingers": Aid(
        id="patient_fingers",
        label="patient fingers",
        phrase="patient fingers and a slow breath",
        power=2,
        sense=3,
        tags={"lift", "untie"},
        action_text="worked at the knot little by little until the ribbon came loose.",
        qa_text="used patient fingers to loosen the knot",
    ),
    "reed_staff": Aid(
        id="reed_staff",
        label="reed staff",
        phrase="a smooth reed staff",
        power=2,
        sense=3,
        tags={"pull"},
        action_text="slid the staff beneath the shell and levered it up with careful strength.",
        qa_text="used a reed staff to lift the shell free",
    ),
    "wrong_song": Aid(
        id="wrong_song",
        label="a loud song",
        phrase="a loud song",
        power=0,
        sense=1,
        tags={"comfort"},
        action_text="sang loudly into the reeds, but the trouble only tightened.",
        qa_text="sang loudly, which did not fix the trouble",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for creature_id, creature in CREATURES.items():
            if creature.habitat != setting.habitat:
                continue
            for trouble_id, trouble in TROUBLES.items():
                if trouble_fits(creature, trouble):
                    combos.append((setting_id, creature_id, trouble_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    creature: str
    trouble: str
    aid: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "analyze": [(
        "What does it mean to analyze signs?",
        "To analyze signs means to stop, look closely, and think about what each clue means. "
        "It helps you understand what is really happening instead of guessing too fast."
    )],
    "myth": [(
        "What is a myth?",
        "A myth is an old kind of story that explains a place, a creature, or a custom with wonder. "
        "Myths often make the world feel alive and meaningful."
    )],
    "repetition": [(
        "Why do stories sometimes repeat a sound three times?",
        "Repetition helps a listener notice that something matters. "
        "In myths, hearing something three times can make the moment feel magical and important."
    )],
    "kindness": [(
        "Why can kindness matter in a myth?",
        "Kindness changes how characters treat one another, and in a myth it can even change the world. "
        "A kind action often earns trust, help, or a blessing."
    )],
    "thorn": [(
        "Why does a thorn hurt so much?",
        "A thorn is sharp, so it pokes into skin and makes it hard to walk or rest. "
        "Removing it carefully can bring quick relief."
    )],
    "ribbon": [(
        "Why can a tangled ribbon be a problem?",
        "A ribbon can wrap around a wing or foot and keep it from moving properly. "
        "Untying it slowly is safer than yanking it hard."
    )],
    "mud": [(
        "Why is deep mud hard to escape from?",
        "Deep mud grips and sucks at feet or shells, so moving can be hard. "
        "A steady pull or a lever can help someone come free."
    )],
    "reeds": [(
        "What are reeds?",
        "Reeds are tall water plants with long stems. "
        "They grow near ponds and marshes and can rustle in the wind."
    )],
    "blessing": [(
        "What is a blessing in a myth?",
        "A blessing is a gift of safety, luck, wisdom, or peace. "
        "In myths, blessings often come after a brave or kind deed."
    )],
}
KNOWLEDGE_ORDER = ["analyze", "myth", "repetition", "kindness", "thorn", "ribbon", "mud", "reeds", "blessing"]

GIRL_NAMES = ["Nia", "Mira", "Lila", "Asha", "Tala", "Suri", "Rina", "Mina"]
BOY_NAMES = ["Tarin", "Niko", "Aren", "Kavi", "Remi", "Ilan", "Soren", "Milo"]
TRAITS = ["thoughtful", "careful", "patient", "curious", "bold"]
ELDERS = ["grandmother", "grandfather"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    creature = f["creature_cfg"]
    trouble = f["trouble"]
    setting = f["setting"]
    outcome = f["outcome"]
    close = "with a strong blessing at the end" if outcome == "great_blessing" else "with a gentle blessing at the end"
    return [
        f'Write a short myth for a 3-to-5-year-old that uses the word "analyze" and takes place near {setting.place}.',
        f"Tell a suspenseful myth where a child hears the same mysterious cry three times, stops to analyze the signs, and finds a {creature.label} in trouble.",
        f"Write a child-facing myth about kindness in the dark: {hero.id} follows repeated clues, helps with {trouble.label}, and ends {close}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    creature = f["creature_cfg"]
    trouble = f["trouble"]
    aid = f["aid"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child walking near {setting.place}, and a hidden {creature.label} from an old myth. "
            f"{hero.id}'s {elder.label_word} also matters because the old advice about stopping to analyze the signs guided the choice."
        ),
        (
            "What made the story feel suspenseful?",
            f"The cry came again and again from the dark, and at first {hero.id} could not see who was calling. "
            f"Hearing it three times made the night feel mysterious and urgent."
        ),
        (
            f"Why did {hero.id} stop to analyze the signs?",
            f"{hero.id} had been taught not to rush when dusk called three times. "
            f"By looking closely at the clues instead of guessing, {hero.pronoun()} could find where the trouble really was."
        ),
        (
            f"What trouble did {hero.id} find?",
            f"{hero.id} found the {creature.label}, and {trouble.found_text}. "
            f"That is why the repeated cry sounded so thin and worried."
        ),
    ]
    if f.get("help_success"):
        qa.append((
            f"How did {hero.id} help the creature?",
            f"{hero.id} {aid.qa_text}. The help worked because it matched the trouble instead of making it worse."
        ))
    else:
        qa.append((
            f"Did {hero.id} solve the problem alone?",
            f"No. {hero.id} tried, but the help was not strong or wise enough for that trouble. "
            f"So {hero.pronoun()} promised to bring {hero.pronoun('possessive')} {elder.label_word}, which was also a kind choice."
        ))

    if outcome == "great_blessing":
        qa.append((
            "How did the story end?",
            f"It ended with a bright blessing: the {creature.label} thanked {hero.id}, and {setting.place} seemed less dark afterward. "
            f"The ending shows that careful thought and kindness changed the world around the child."
        ))
    elif outcome == "gentle_blessing":
        qa.append((
            "How did the story end?",
            f"It ended gently: the {creature.label} remembered {hero.id}'s kindness and left a soft guiding glimmer on future evenings. "
            f"The child was frightened for a while, but kindness still turned the dark path into a friend."
        ))
    else:
        qa.append((
            "What did the child learn at the end?",
            f"{hero.id} learned that kindness does not always mean doing everything alone. "
            f"Sometimes the wisest kind act is to fetch someone with better tools or stronger hands."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"analyze", "myth", "repetition", "kindness", "blessing"}
    tags |= set(f["trouble"].tags)
    tags |= set(f["creature_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_pond",
        creature="reed_crane",
        trouble="tangle",
        aid="patient_fingers",
        name="Nia",
        gender="girl",
        elder="grandmother",
        trait="thoughtful",
        seed=None,
    ),
    StoryParams(
        setting="cedar_hill",
        creature="moon_fox",
        trouble="thorn",
        aid="silver_tongs",
        name="Aren",
        gender="boy",
        elder="grandfather",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        setting="moss_cave",
        creature="moss_turtle",
        trouble="mud",
        aid="reed_staff",
        name="Mira",
        gender="girl",
        elder="grandmother",
        trait="bold",
        seed=None,
    ),
    StoryParams(
        setting="moon_pond",
        creature="reed_crane",
        trouble="tangle",
        aid="patient_fingers",
        name="Kavi",
        gender="boy",
        elder="grandfather",
        trait="curious",
        seed=None,
    ),
]


def explain_combo(setting: Setting, creature: Creature, trouble: Trouble) -> str:
    if creature.habitat != setting.habitat:
        return (
            f"(No story: {creature.label} belongs to {creature.habitat}, but {setting.place} is a "
            f"{setting.habitat} place. The repeated clues would point to the wrong kind of world.)"
        )
    return (
        f"(No story: {trouble.label} does not fit the nature of the {creature.label}. "
        f"This myth only tells troubles that the creature could really have.)"
    )


def explain_aid(aid: Aid, trouble: Trouble) -> str:
    if aid.sense < SENSE_MIN:
        return (
            f"(Refusing aid '{aid.id}': it scores too low on common sense "
            f"(sense={aid.sense} < {SENSE_MIN}). The storyworld prefers a wiser form of help.)"
        )
    return (
        f"(No story: {aid.label} does not solve {trouble.label}. The child can be kind, "
        f"but the chosen help must fit the trouble.)"
    )


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(S, C, T) :- setting(S), creature(C), trouble(T),
                  habitat_of(S, H), habitat_of_creature(C, H),
                  creature_trouble(C, T).

sensible_aid(A) :- aid(A), sense(A, N), sense_min(M), N >= M.
usable_aid(A, T) :- sensible_aid(A), aid_tag(A, Tag), needs(T, Tag).

% --- outcome model ---------------------------------------------------------
clear_reading :- trait(T), analytic_trait(T).
can_help      :- chosen_aid(A), chosen_trouble(T), usable_aid(A, T), power(A, P), severity(T, S), P >= S.

outcome(great_blessing)  :- can_help, clear_reading.
outcome(gentle_blessing) :- can_help, not clear_reading.
outcome(waiting_moon)    :- not can_help.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("habitat_of", setting_id, setting.habitat))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("habitat_of_creature", creature_id, creature.habitat))
        for trouble_id in sorted(creature.trouble_ids):
            lines.append(asp.fact("creature_trouble", creature_id, trouble_id))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("needs", trouble_id, trouble.fix_tag))
        lines.append(asp.fact("severity", trouble_id, trouble.severity))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        lines.append(asp.fact("power", aid_id, aid.power))
        for tag in sorted(aid.tags):
            lines.append(asp.fact("aid_tag", aid_id, tag))
    for trait in sorted(ANALYTIC_TRAITS):
        lines.append(asp.fact("analytic_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_aids() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_aid/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible_aid"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_aid", params.aid),
        asp.fact("chosen_trouble", params.trouble),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child hears a mythic cry three times, analyzes the signs, and chooses kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.creature:
        setting = SETTINGS[args.setting]
        creature = CREATURES[args.creature]
        if creature.habitat != setting.habitat:
            trouble = TROUBLES[args.trouble] if args.trouble else TROUBLES[next(iter(sorted(creature.trouble_ids)))]
            raise StoryError(explain_combo(setting, creature, trouble))
    if args.creature and args.trouble:
        creature = CREATURES[args.creature]
        trouble = TROUBLES[args.trouble]
        if not trouble_fits(creature, trouble):
            setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
            raise StoryError(explain_combo(setting, creature, trouble))
    if args.aid:
        aid = AIDS[args.aid]
        if aid.sense < SENSE_MIN:
            trouble = TROUBLES[args.trouble] if args.trouble else next(iter(TROUBLES.values()))
            raise StoryError(explain_aid(aid, trouble))
        if args.trouble and not aid_can_help(aid, TROUBLES[args.trouble]):
            raise StoryError(explain_aid(aid, TROUBLES[args.trouble]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.creature is None or combo[1] == args.creature)
        and (args.trouble is None or combo[2] == args.trouble)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, creature_id, trouble_id = rng.choice(sorted(combos))
    trouble = TROUBLES[trouble_id]
    possible_aids = [aid.id for aid in sensible_aids() if aid_can_help(aid, trouble)]
    if args.aid:
        if args.aid not in possible_aids:
            raise StoryError(explain_aid(AIDS[args.aid], trouble))
        aid_id = args.aid
    else:
        aid_id = rng.choice(sorted(possible_aids))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        creature=creature_id,
        trouble=trouble_id,
        aid=aid_id,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        creature = CREATURES[params.creature]
        trouble = TROUBLES[params.trouble]
        aid = AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if creature.habitat != setting.habitat or not trouble_fits(creature, trouble):
        raise StoryError(explain_combo(setting, creature, trouble))
    if aid.sense < SENSE_MIN or not aid_can_help(aid, trouble):
        raise StoryError(explain_aid(aid, trouble))

    world = tell(
        setting=setting,
        creature=creature,
        trouble=trouble,
        aid=aid,
        hero_name=params.name,
        hero_type=params.gender,
        trait=params.trait,
        elder_type=params.elder,
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

    clingo_aids = set(asp_sensible_aids())
    python_aids = {aid.id for aid in sensible_aids()}
    if clingo_aids == python_aids:
        print(f"OK: sensible aids match ({sorted(clingo_aids)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible aids: clingo={sorted(clingo_aids)} python={sorted(python_aids)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_aid/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible aids: {', '.join(asp_sensible_aids())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, creature, trouble) combos:\n")
        for setting_id, creature_id, trouble_id in combos:
            print(f"  {setting_id:11} {creature_id:12} {trouble_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.name}: {p.creature} with {p.trouble} at {p.setting} "
                f"({p.aid}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
