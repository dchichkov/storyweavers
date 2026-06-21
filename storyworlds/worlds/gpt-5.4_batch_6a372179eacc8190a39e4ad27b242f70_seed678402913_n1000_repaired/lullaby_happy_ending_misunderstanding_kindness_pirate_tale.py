#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lullaby_happy_ending_misunderstanding_kindness_pirate_tale.py
=========================================================================================

A standalone storyworld about a pirate-child misunderstanding a lullaby on a
boat. The misunderstanding creates a small nighttime problem, and kindness
solves it. The domain stays narrow on purpose: a caregiver sings a lullaby to
help a baby or tired crewmate sleep; another child mistakes the soft song for a
distress or command signal and causes a harmless stir; then the group explains,
forgives, and ends together under calm night light.

Contract highlights:
- stdlib only
- imports shared QAItem / StoryError / StorySample eagerly
- includes Python reasonableness checks and inline ASP twin
- supports: default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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
        female = {"girl", "woman", "mother", "captain_female", "singer_female"}
        male = {"boy", "man", "father", "captain_male", "singer_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "captain_female": "captain",
            "captain_male": "captain",
        }.get(self.type, self.type)


@dataclass
class VoyageTheme:
    id: str
    opening: str
    deck_image: str
    game_name: str
    goal: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ListenerKind:
    id: str
    label: str
    phrase: str
    role_noun: str
    sleepy_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SingerKind:
    id: str
    label: str
    voice_desc: str
    comfort_action: str
    type: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MishearKind:
    id: str
    heard_as: str
    action_text: str
    worry_text: str
    fix_explainer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindAct:
    id: str
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LightKind:
    id: str
    phrase: str
    glow: str
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.facts = copy.deepcopy(self.facts)
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stir_from_alarm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    ship = world.get("ship")
    if hero.memes["alarm"] >= THRESHOLD:
        sig = ("stir", "ship")
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["stir"] += 1
            out.append("__stir__")
    return out


def _r_kindness_clears_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    listener = world.get("listener")
    if hero.memes["comforted"] >= THRESHOLD:
        sig = ("fear_down", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] = 0.0
            hero.memes["belonging"] += 1
        sig2 = ("settle", "listener")
        if sig2 not in world.fired:
            world.fired.add(sig2)
            listener.memes["sleep"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="stir_from_alarm", tag="social", apply=_r_stir_from_alarm),
    Rule(name="kindness_clears_fear", tag="social", apply=_r_kindness_clears_fear),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


THEMES = {
    "moon_deck": VoyageTheme(
        id="moon_deck",
        opening="The moon laid a silver road across the sea beside the little pirate ship.",
        deck_image="The ropes swayed softly, the mast creaked like an old tree, and the sail looked pale as milk in the dark.",
        game_name="night watch",
        goal="keep the ship brave and snug until morning",
        ending_line="The ship rocked as gently as a cradle, and the sea sounded almost like a purring cat.",
        tags={"ship", "night"},
    ),
    "harbor_cove": VoyageTheme(
        id="harbor_cove",
        opening="The pirate boat rested in a quiet cove where the black water only kissed the sides with little taps.",
        deck_image="Lantern light touched the wooden rail, and the folded sail made a soft hill above the deck.",
        game_name="harbor watch",
        goal="guard the boat while the stars blinked awake",
        ending_line="The cove held the boat still and kind, as if the whole night wanted everyone to rest.",
        tags={"ship", "night"},
    ),
    "star_map": VoyageTheme(
        id="star_map",
        opening="Far from shore, the young pirates looked up at a sky sprinkled with stars like treasure on dark velvet.",
        deck_image="A little map lay by the wheel, the deck boards smelled of salt, and the waves hushed against the hull.",
        game_name="star map watch",
        goal="follow the stars and keep the crew calm",
        ending_line="Above them the stars kept shining, and below them the sea rolled slow and safe.",
        tags={"ship", "night"},
    ),
}

LISTENERS = {
    "baby_brother": ListenerKind(
        id="baby_brother",
        label="baby brother",
        phrase="her baby brother in a little hammock",
        role_noun="baby",
        sleepy_reason="had fought sleep and rubbed his eyes all evening",
        tags={"baby", "sleep"},
    ),
    "little_sister": ListenerKind(
        id="little_sister",
        label="little sister",
        phrase="his little sister curled in a blanket nest",
        role_noun="child",
        sleepy_reason="had yawned and blinked at the stars until her eyes kept closing",
        tags={"child", "sleep"},
    ),
    "sleepy_parrot": ListenerKind(
        id="sleepy_parrot",
        label="parrot",
        phrase="the ship's sleepy parrot on a hanging perch",
        role_noun="parrot",
        sleepy_reason="had spent the day squawking and flapping and was now drooping with sleep",
        tags={"parrot", "sleep"},
    ),
}

SINGERS = {
    "mother": SingerKind(
        id="mother",
        label="mother",
        voice_desc="in a low, warm voice",
        comfort_action="smoothed the blanket with one gentle hand",
        type="mother",
        tags={"parent", "kindness"},
    ),
    "father": SingerKind(
        id="father",
        label="father",
        voice_desc="in a soft, steady voice",
        comfort_action="tucked the cover close with careful fingers",
        type="father",
        tags={"parent", "kindness"},
    ),
    "captain_aunt": SingerKind(
        id="captain_aunt",
        label="captain aunt",
        voice_desc="in a deep, calm captain voice",
        comfort_action="rested a kind hand on the hammock rope so it barely swayed",
        type="captain_female",
        tags={"captain", "kindness"},
    ),
}

MISHEARS = {
    "storm_call": MishearKind(
        id="storm_call",
        heard_as="a storm warning",
        action_text="grabbed the little bell and rang it for danger",
        worry_text="thought the long soft notes meant wind and trouble were coming",
        fix_explainer="It was only a lullaby, not a warning call.",
        tags={"misunderstanding", "alarm"},
    ),
    "treasure_riddle": MishearKind(
        id="treasure_riddle",
        heard_as="a treasure clue",
        action_text="snatched up the map and began whispering about secret gold",
        worry_text="thought the song was hiding directions to buried treasure",
        fix_explainer="It was only a lullaby, not a treasure riddle.",
        tags={"misunderstanding", "treasure"},
    ),
    "row_command": MishearKind(
        id="row_command",
        heard_as="a rowing command",
        action_text="hurried to the oars and tried to push the boat away from the moonlit rocks",
        worry_text="thought the slow rhythm meant everyone had to row at once",
        fix_explainer="It was only a lullaby, not an order.",
        tags={"misunderstanding", "command"},
    ),
}

KIND_ACTS = {
    "hug_and_explain": KindAct(
        id="hug_and_explain",
        text="knelt down, opened both arms, and explained the mistake without even one sharp word",
        qa_text="knelt down, hugged the child, and explained the misunderstanding kindly",
        tags={"hug", "kindness"},
    ),
    "thank_and_teach": KindAct(
        id="thank_and_teach",
        text="thanked the child for trying to help, then gently explained what the song was for",
        qa_text="thanked the child for trying to help and then gently explained the song",
        tags={"thanks", "kindness"},
    ),
    "share_lullaby": KindAct(
        id="share_lullaby",
        text="smiled, patted the deck beside them, and invited the child to listen to the lullaby up close",
        qa_text="smiled and invited the child closer so they could understand the lullaby",
        tags={"sharing", "kindness"},
    ),
}

LIGHTS = {
    "lantern": LightKind(
        id="lantern",
        phrase="a round brass lantern",
        glow="glowed like a warm gold coin",
        tags={"lantern", "light"},
    ),
    "moonbeam": LightKind(
        id="moonbeam",
        phrase="the moonlight on the deck",
        glow="shone silver on the planks",
        tags={"moon", "light"},
    ),
    "star_lamp": LightKind(
        id="star_lamp",
        phrase="a tiny star lamp by the hammock",
        glow="made a small pool of honey-colored light",
        tags={"lamp", "light"},
    ),
}

GIRL_NAMES = ["Lila", "Mara", "Nell", "Poppy", "Tess", "Ava", "Mina", "Rosa"]
BOY_NAMES = ["Finn", "Toby", "Benji", "Leo", "Nico", "Sam", "Owen", "Jude"]
TRAITS = ["brave", "eager", "helpful", "curious", "quick", "kind"]


def misunderstanding_valid(listener_id: str, mishear_id: str) -> bool:
    if listener_id == "sleepy_parrot" and mishear_id == "treasure_riddle":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for listener_id in LISTENERS:
            for mishear_id in MISHEARS:
                if misunderstanding_valid(listener_id, mishear_id):
                    out.append((theme_id, listener_id, mishear_id))
    return out


def explain_rejection(listener_id: str, mishear_id: str) -> str:
    if listener_id == "sleepy_parrot" and mishear_id == "treasure_riddle":
        return ("(No story: a sleepy parrot on this little ship can be soothed by a lullaby, "
                "but the treasure-riddle misunderstanding is too abstract for this listener. "
                "Pick a storm call or rowing command instead.)")
    return "(No story: this misunderstanding does not fit this listener.)"


@dataclass
class StoryParams:
    theme: str
    listener: str
    singer: str
    mishear: str
    kindness: str
    light: str
    child_name: str
    child_gender: str
    parent_name: str
    trait: str
    seed: Optional[int] = None


def play_setup(world: World, theme: VoyageTheme, hero: Entity, singer: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(theme.opening)
    world.say(theme.deck_image)
    world.say(
        f"{hero.id} was a little pirate with a {next(iter(hero.traits), 'bright')} heart, and tonight "
        f"{hero.pronoun()} had promised to help with {theme.game_name} and {theme.goal}."
    )
    world.say(
        f"{singer.id}, {hero.pronoun('possessive')} {singer.label_word}, moved quietly across the deck so nobody sleepy would wake with a start."
    )


def introduce_sleep_need(world: World, singer: Entity, listener_cfg: ListenerKind, light: LightKind) -> None:
    world.say(
        f"Near {light.phrase} that {light.glow}, {singer.id} sat beside {listener_cfg.phrase}, who {listener_cfg.sleepy_reason}."
    )
    world.say(
        f'Soon {singer.pronoun()} began to sing a lullaby {SINGERS[world.facts["singer_cfg"].id].voice_desc}.'
    )
    world.say(
        f"{singer.pronoun().capitalize()} {SINGERS[world.facts['singer_cfg'].id].comfort_action}, and the tune floated over the deck as softly as a feather."
    )


def predict_misunderstanding(world: World, mishear: MishearKind) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    ship = sim.get("ship")
    hero.memes["alarm"] += 1
    if mishear.id == "treasure_riddle":
        hero.memes["excitement"] += 1
    else:
        hero.memes["fear"] += 1
    propagate(sim, narrate=False)
    return {
        "ship_stir": ship.meters["stir"],
        "fear": hero.memes["fear"],
        "excitement": hero.memes["excitement"],
    }


def mishear_song(world: World, hero: Entity, mishear: MishearKind) -> None:
    pred = predict_misunderstanding(world, mishear)
    world.facts["predicted_stir"] = pred["ship_stir"]
    world.say(
        f"But {hero.id} stopped in the moonlight and listened with wide eyes. {hero.pronoun().capitalize()} had never heard this song at sea before and {mishear.worry_text}."
    )
    if mishear.id == "treasure_riddle":
        hero.memes["excitement"] += 1
    else:
        hero.memes["fear"] += 1
    hero.memes["alarm"] += 1
    propagate(world, narrate=False)
    world.say(f"So {hero.pronoun()} {mishear.action_text}.")
    if world.get("ship").meters["stir"] >= THRESHOLD:
        world.say("At once the quiet deck was not quite so quiet anymore.")


def show_consequence(world: World, listener_cfg: ListenerKind) -> None:
    listener = world.get("listener")
    listener.memes["sleep"] = 0.0
    listener.memes["startled"] += 1
    if listener_cfg.id == "sleepy_parrot":
        world.say("The parrot fluffed its feathers and gave one confused squawk instead of settling its beak under its wing.")
    else:
        world.say("The sleepy little listener blinked awake again, and the soft almost-sleepy feeling drifted away.")


def kindly_resolve(world: World, singer: Entity, hero: Entity, mishear: MishearKind, kindness: KindAct) -> None:
    hero.memes["shame"] += 1
    world.say(
        f'{hero.id} froze. "{mishear.heard_as.capitalize()}?" {hero.pronoun()} whispered, suddenly unsure.'
    )
    world.say(
        f"But {singer.id} did not scold. {singer.pronoun().capitalize()} {kindness.text}."
    )
    hero.memes["comforted"] += 1
    world.facts["fix_explainer"] = mishear.fix_explainer
    propagate(world, narrate=False)
    world.say(
        f'"{mishear.fix_explainer} A lullaby is a gentle song for helping someone rest," {singer.pronoun()} said.'
    )
    world.say(
        f'"You were trying to help the ship," {singer.pronoun()} added. "That was kind. Next time, you can ask me first."'
    )


def join_in(world: World, hero: Entity, singer: Entity, listener_cfg: ListenerKind) -> None:
    hero.memes["joy"] += 1
    hero.memes["kindness"] += 1
    listener = world.get("listener")
    listener.memes["sleep"] += 1
    if listener_cfg.id == "sleepy_parrot":
        world.say(
            f"{hero.id} put the bell down very quietly and stood beside {singer.id}. Together they hummed the lullaby until the parrot tucked its head under one wing."
        )
    else:
        world.say(
            f"Then {hero.id} crept closer and hummed the lullaby too, very softly this time. Little by little, the sleepy listener's eyes drooped again."
        )
    world.say(
        f"{hero.id} learned the tune and let it out in a whisper, as gentle as a tide touching sand."
    )


def ending(world: World, theme: VoyageTheme, hero: Entity, singer: Entity, light: LightKind) -> None:
    world.say(
        f'Soon the deck was calm again. {light.phrase.capitalize()} {light.glow}, and {hero.id} leaned against {singer.id} with a peaceful smile.'
    )
    world.say(
        f"{theme.ending_line} {hero.id} knew now that a lullaby was not a warning or a command at all. It was a kind way to help another heart feel safe enough to sleep."
    )


def tell(
    theme: VoyageTheme,
    listener_cfg: ListenerKind,
    singer_cfg: SingerKind,
    mishear: MishearKind,
    kindness: KindAct,
    light: LightKind,
    child_name: str,
    child_gender: str,
    parent_name: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="hero",
        traits=[trait],
    ))
    singer = world.add(Entity(
        id="singer",
        kind="character",
        type=singer_cfg.type,
        label=parent_name,
        phrase=parent_name,
        role="singer",
        tags=set(singer_cfg.tags),
    ))
    listener_type = "parrot" if listener_cfg.id == "sleepy_parrot" else "child"
    listener = world.add(Entity(
        id="listener",
        kind="thing" if listener_type == "parrot" else "character",
        type=listener_type,
        label=listener_cfg.label,
        phrase=listener_cfg.phrase,
        role="listener",
        tags=set(listener_cfg.tags),
    ))
    ship = world.add(Entity(
        id="ship",
        kind="thing",
        type="ship",
        label="pirate ship",
        phrase="the little pirate ship",
        role="setting",
        tags={"ship", "night"},
    ))
    world.facts["theme"] = theme
    world.facts["listener_cfg"] = listener_cfg
    world.facts["singer_cfg"] = singer_cfg
    world.facts["mishear"] = mishear
    world.facts["kindness"] = kindness
    world.facts["light"] = light
    world.facts["hero_name"] = child_name
    world.facts["parent_name"] = parent_name

    play_setup(world, theme, hero, singer)
    introduce_sleep_need(world, singer, listener_cfg, light)

    world.para()
    mishear_song(world, hero, mishear)
    show_consequence(world, listener_cfg)

    world.para()
    kindly_resolve(world, singer, hero, mishear, kindness)
    join_in(world, hero, singer, listener_cfg)

    world.para()
    ending(world, theme, hero, singer, light)

    outcome = "happy" if hero.memes["comforted"] >= THRESHOLD and listener.memes["sleep"] >= THRESHOLD else "unsettled"
    world.facts.update(
        hero=hero,
        singer=singer,
        listener=listener,
        ship=ship,
        outcome=outcome,
        misunderstood=True,
        ship_stir=ship.meters["stir"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "lullaby": [
        ("What is a lullaby?",
         "A lullaby is a gentle song sung to help someone feel calm and sleepy. Its soft rhythm can make rest feel safe.")
    ],
    "ship": [
        ("What is a pirate ship?",
         "A pirate ship is a boat that sails on the sea. In stories, pirates use it to travel, watch the waves, and look for adventure.")
    ],
    "night": [
        ("Why do quiet sounds matter at night?",
         "At night, quiet sounds matter because people and animals may be trying to rest. Loud noises can wake them or make them feel startled.")
    ],
    "misunderstanding": [
        ("What is a misunderstanding?",
         "A misunderstanding happens when someone thinks they heard or understood something, but they got it wrong. Kind explanations can fix it.")
    ],
    "kindness": [
        ("What does it mean to be kind when someone makes a mistake?",
         "It means you help them understand without being cruel. A kind voice can turn a mistake into a lesson.")
    ],
    "lantern": [
        ("What does a lantern do on a boat?",
         "A lantern gives light so people can see in the dark. Its glow can make a deck feel warm and safe.")
    ],
    "moon": [
        ("Why does moonlight help on the sea?",
         "Moonlight can make the water and deck easier to see. It also makes the night feel calm and bright enough for gentle watching.")
    ],
    "parrot": [
        ("Why might a parrot need rest after a busy day?",
         "Like people, a parrot gets tired after making noise and moving around. Rest helps its body settle down.")
    ],
}
KNOWLEDGE_ORDER = ["lullaby", "ship", "night", "misunderstanding", "kindness", "lantern", "moon", "parrot"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    singer = f["singer"]
    mishear = f["mishear"]
    listener_cfg = f["listener_cfg"]
    return [
        'Write a pirate bedtime story for a 3-to-5-year-old that includes the word "lullaby".',
        f"Tell a gentle pirate tale where {hero.label} hears a lullaby on a ship, mistakes it for {mishear.heard_as}, and then learns the truth through kindness.",
        f"Write a happy-ending story in which {singer.label}'s calm explanation helps a child fix a misunderstanding and soothe {listener_cfg.label} back to sleep.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    singer = f["singer"]
    listener_cfg = f["listener_cfg"]
    mishear = f["mishear"]
    kindness = f["kindness"]
    light = f["light"]
    hero_name = hero.label
    singer_name = singer.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little pirate child named {hero_name}, {singer_name}, and {listener_cfg.label} on their ship at night."
        ),
        (
            "What was happening at the start of the story?",
            f"{singer_name} was singing a lullaby beside {listener_cfg.phrase}. The quiet song was meant to help the sleepy listener rest."
        ),
        (
            f"What did {hero_name} misunderstand?",
            f"{hero_name} misunderstood the lullaby and thought it was {mishear.heard_as}. Because of that mistake, {hero.pronoun()} reacted quickly instead of quietly listening."
        ),
        (
            f"What happened because of the misunderstanding?",
            f"{hero_name} {mishear.action_text}, and the calm deck became stirred up. That noise woke or startled the sleepy listener instead of helping {listener_cfg.role_noun} drift off."
        ),
        (
            f"How did {singer_name} respond to the mistake?",
            f"{singer_name} did not scold. {singer.pronoun().capitalize()} {kindness.qa_text}, which helped {hero_name} understand the song was only for comfort."
        ),
        (
            "How did the story end?",
            f"It ended happily. Under {light.phrase}, they quieted the deck again and joined in the lullaby until the sleepy listener could rest."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"lullaby", "ship", "night", "misunderstanding", "kindness"}
    light = world.facts["light"]
    if "lantern" in light.tags or "lamp" in light.tags:
        tags.add("lantern")
    if "moon" in light.tags:
        tags.add("moon")
    if world.facts["listener_cfg"].id == "sleepy_parrot":
        tags.add("parrot")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="moon_deck",
        listener="baby_brother",
        singer="mother",
        mishear="storm_call",
        kindness="hug_and_explain",
        light="lantern",
        child_name="Lila",
        child_gender="girl",
        parent_name="Mama Rosa",
        trait="helpful",
        seed=1,
    ),
    StoryParams(
        theme="harbor_cove",
        listener="little_sister",
        singer="father",
        mishear="row_command",
        kindness="thank_and_teach",
        light="moonbeam",
        child_name="Finn",
        child_gender="boy",
        parent_name="Papa Tom",
        trait="brave",
        seed=2,
    ),
    StoryParams(
        theme="star_map",
        listener="sleepy_parrot",
        singer="captain_aunt",
        mishear="storm_call",
        kindness="share_lullaby",
        light="star_lamp",
        child_name="Mara",
        child_gender="girl",
        parent_name="Captain Una",
        trait="curious",
        seed=3,
    ),
    StoryParams(
        theme="moon_deck",
        listener="little_sister",
        singer="mother",
        mishear="treasure_riddle",
        kindness="thank_and_teach",
        light="lantern",
        child_name="Nico",
        child_gender="boy",
        parent_name="Mama Pearl",
        trait="eager",
        seed=4,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "happy"


ASP_RULES = r"""
valid(T, L, M) :- theme(T), listener(L), mishear(M), not invalid(L, M).
invalid(sleepy_parrot, treasure_riddle).

happy_outcome.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for listener_id in LISTENERS:
        lines.append(asp.fact("listener", listener_id))
    for mishear_id in MISHEARS:
        lines.append(asp.fact("mishear", mishear_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate-child misunderstands a lullaby, and kindness makes the night calm again."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--listener", choices=LISTENERS)
    ap.add_argument("--singer", choices=SINGERS)
    ap.add_argument("--mishear", choices=MISHEARS)
    ap.add_argument("--kindness", choices=KIND_ACTS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--parent-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _pick_parent_name(rng: random.Random, singer_id: str) -> str:
    if singer_id == "father":
        return rng.choice(["Papa Tom", "Papa Reed", "Papa Vale", "Papa Ben"])
    if singer_id == "captain_aunt":
        return rng.choice(["Captain Una", "Captain May", "Captain Brin"])
    return rng.choice(["Mama Rosa", "Mama Pearl", "Mama June", "Mama Wren"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.listener and args.mishear and not misunderstanding_valid(args.listener, args.mishear):
        raise StoryError(explain_rejection(args.listener, args.mishear))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.listener is None or combo[1] == args.listener)
        and (args.mishear is None or combo[2] == args.mishear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, listener_id, mishear_id = rng.choice(sorted(combos))
    singer_id = args.singer or rng.choice(sorted(SINGERS.keys()))
    kindness_id = args.kindness or rng.choice(sorted(KIND_ACTS.keys()))
    light_id = args.light or rng.choice(sorted(LIGHTS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, gender)
    parent_name = args.parent_name or _pick_parent_name(rng, singer_id)
    trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        listener=listener_id,
        singer=singer_id,
        mishear=mishear_id,
        kindness=kindness_id,
        light=light_id,
        child_name=child_name,
        child_gender=gender,
        parent_name=parent_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"Unknown theme: {params.theme}")
    if params.listener not in LISTENERS:
        raise StoryError(f"Unknown listener: {params.listener}")
    if params.singer not in SINGERS:
        raise StoryError(f"Unknown singer: {params.singer}")
    if params.mishear not in MISHEARS:
        raise StoryError(f"Unknown mishear choice: {params.mishear}")
    if params.kindness not in KIND_ACTS:
        raise StoryError(f"Unknown kindness choice: {params.kindness}")
    if params.light not in LIGHTS:
        raise StoryError(f"Unknown light: {params.light}")
    if not misunderstanding_valid(params.listener, params.mishear):
        raise StoryError(explain_rejection(params.listener, params.mishear))

    world = tell(
        theme=THEMES[params.theme],
        listener_cfg=LISTENERS[params.listener],
        singer_cfg=SINGERS[params.singer],
        mishear=MISHEARS[params.mishear],
        kindness=KIND_ACTS[params.kindness],
        light=LIGHTS[params.light],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_name=params.parent_name,
        trait=params.trait,
    )
    story_text = world.render().replace("hero", params.child_name).replace("singer", params.parent_name)
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, listener, mishear) combos:\n")
        for theme_id, listener_id, mishear_id in combos:
            print(f"  {theme_id:11} {listener_id:13} {mishear_id}")
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
            header = f"### {p.child_name}: {p.mishear} on {p.theme} ({p.listener}, {p.singer})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
