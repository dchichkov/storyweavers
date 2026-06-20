#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/resent_brother_mood_quest_surprise_moral_value.py
=============================================================================

A small fairy-tale storyworld about a child who begins to resent a brother's
mood during a quest, then learns a moral through a surprising act of kindness.

The domain is intentionally narrow and state-driven:

* A grandmother sends two siblings on a small quest for a needed wonder-item.
* The hero starts in a sour mood and quietly resents the brother's bright mood.
* A real obstacle on the road creates the turn.
* The brother reveals a sensible hidden aid, surprising the hero.
* They finish the quest, and the ending image proves the resentment changed into
  gratitude and a named moral value.

Run it
------
    python storyworlds/worlds/gpt-5.4/resent_brother_mood_quest_surprise_moral_value.py
    python storyworlds/worlds/gpt-5.4/resent_brother_mood_quest_surprise_moral_value.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/resent_brother_mood_quest_surprise_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/resent_brother_mood_quest_surprise_moral_value.py --qa
    python storyworlds/worlds/gpt-5.4/resent_brother_mood_quest_surprise_moral_value.py --trace
    python storyworlds/worlds/gpt-5.4/resent_brother_mood_quest_surprise_moral_value.py --json
    python storyworlds/worlds/gpt-5.4/resent_brother_mood_quest_surprise_moral_value.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    place: str
    path: str
    light: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    item: str
    source: str
    use: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    trouble: str
    fear: str
    solved_by: str
    values: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    reveal: str
    action: str
    for_obstacle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    noun: str
    lesson: str
    closing: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
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
        clone = World(self.realm)
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


def _r_stuck_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero and hero.meters["stuck"] >= THRESHOLD:
        sig = ("worry", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_help_soften(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    brother = world.entities.get("brother")
    if not hero or not brother:
        return out
    if brother.memes["helped"] >= THRESHOLD and hero.memes["resentment"] >= THRESHOLD:
        sig = ("soften", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["softened"] += 1
            hero.memes["resentment"] = 0.0
            hero.memes["gratitude"] += 1
            out.append("__soften__")
    return out


def _r_complete_joy(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    brother = world.entities.get("brother")
    if hero and brother and world.facts.get("got_item"):
        sig = ("joy", "siblings")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] += 1
            brother.memes["joy"] += 1
            out.append("__joy__")
    return out


CAUSAL_RULES = [
    Rule("stuck_worry", "emotional", _r_stuck_worry),
    Rule("help_soften", "emotional", _r_help_soften),
    Rule("complete_joy", "emotional", _r_complete_joy),
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


def compatible_aid(obstacle: Obstacle, aid: Aid) -> bool:
    return obstacle.id == aid.for_obstacle


def valid_value(obstacle: Obstacle, value: MoralValue) -> bool:
    return value.id in obstacle.values


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for quest_id in QUESTS:
            for obstacle_id in sorted(realm.affords):
                obstacle = OBSTACLES[obstacle_id]
                for aid_id, aid in AIDS.items():
                    if not compatible_aid(obstacle, aid):
                        continue
                    for value_id, value in VALUES.items():
                        if valid_value(obstacle, value):
                            combos.append((realm_id, quest_id, obstacle_id, aid_id, value_id))
    return combos


def explain_rejection(obstacle: Obstacle, aid: Aid, value: MoralValue) -> str:
    if not compatible_aid(obstacle, aid):
        return (
            f"(No story: {aid.label} is not a sensible answer to {obstacle.label}. "
            f"That obstacle is best solved by {obstacle.solved_by}.)"
        )
    if not valid_value(obstacle, value):
        good = ", ".join(sorted(obstacle.values))
        return (
            f"(No story: {value.noun} is not the clearest moral for {obstacle.label}. "
            f"Try one of: {good}.)"
        )
    return "(No story: this combination does not fit the world.)"


def predict_trouble(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["stuck"] += 1
    propagate(sim, narrate=False)
    return {
        "stuck": hero.meters["stuck"] >= THRESHOLD,
        "worry": hero.memes["worry"] >= THRESHOLD,
        "obstacle": obstacle.label,
    }


def opening(world: World, hero: Entity, brother: Entity, elder: Entity,
            quest: Quest) -> None:
    world.say(
        f"In a cottage at the edge of {world.realm.place}, {hero.id} lived with "
        f"{hero.pronoun('possessive')} cheerful brother {brother.id} and their old {elder.label}."
    )
    world.say(
        f"One morning, the old {elder.label} said they must fetch {quest.item} from "
        f"{quest.source}, because {quest.use}."
    )
    hero.memes["duty"] += 1
    brother.memes["duty"] += 1


def spark_resentment(world: World, hero: Entity, brother: Entity, aid: Aid) -> None:
    hero.memes["resentment"] += 1
    brother.memes["bright_mood"] += 1
    world.say(
        f"{brother.id} smiled as if even the pebbles on the road were friendly, and "
        f"{hero.id} walked beside him with a pinched mood."
    )
    world.say(
        f"When {brother.id} was trusted to carry {aid.label}, {hero.id} felt a hot little sting and "
        f"began to resent {hero.pronoun('possessive')} brother's bright mood."
    )


def set_out(world: World, hero: Entity, brother: Entity) -> None:
    world.say(
        f"Together they stepped onto {world.realm.path}, where {world.realm.light}."
    )


def warning(world: World, hero: Entity, brother: Entity, obstacle: Obstacle) -> None:
    pred = predict_trouble(world, obstacle)
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["predicted_obstacle"] = pred["obstacle"]
    world.say(
        f"Soon they reached {obstacle.label}. {obstacle.trouble}"
    )
    if pred["worry"]:
        world.say(
            f"{hero.id}'s heart gave a quick bump, for {hero.pronoun()} could already imagine "
            f"{obstacle.fear}."
        )


def stumble(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} tried first, but {obstacle.fear}. For a breath, the quest seemed ready to stop there."
    )


def surprise_help(world: World, hero: Entity, brother: Entity, obstacle: Obstacle,
                  aid: Aid) -> None:
    brother.memes["kindness"] += 1
    brother.memes["helped"] += 1
    hero.meters["stuck"] = 0.0
    hero.memes["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the surprise. {brother.id} had not been smiling out of pride at all; "
        f"{aid.reveal}"
    )
    world.say(
        f"Gently, {brother.id} {aid.action}. The way opened, and {hero.id} stared at him with new eyes."
    )


def confess(world: World, hero: Entity, brother: Entity) -> None:
    if hero.memes["softened"] >= THRESHOLD:
        world.say(
            f'"I thought I had to walk alone inside my own heart," {hero.id} whispered. '
            f'"Instead, you were helping me all along."'
        )
        world.say(
            f'{brother.id} squeezed {hero.pronoun("possessive")} hand. '
            f'"A quest is lighter when we carry it together," {brother.pronoun()} said.'
        )


def complete_quest(world: World, hero: Entity, brother: Entity, quest: Quest) -> None:
    world.facts["got_item"] = True
    propagate(world, narrate=False)
    hero.meters["carrying_quest"] += 1
    brother.meters["carrying_quest"] += 1
    world.say(
        f"Beyond the obstacle they found {quest.item} at {quest.source}, just where the morning light touched it."
    )
    world.say(
        f"This time {brother.id} let {hero.id} lift it first, and together they carried it home."
    )


def ending(world: World, hero: Entity, brother: Entity, elder: Entity,
           quest: Quest, value: MoralValue) -> None:
    hero.memes["lesson"] += 1
    brother.memes["lesson"] += 1
    world.say(
        f"The old {elder.label} used {quest.item}, and soon {quest.use} no longer felt like a fear over the cottage."
    )
    world.say(
        f'"Remember this," said the old {elder.label}. "{value.lesson}"'
    )
    world.say(
        f"{hero.id} looked at {hero.pronoun('possessive')} brother and smiled without any shadow at all. "
        f"{quest.ending_image}. {value.closing}"
    )


def tell(realm: Realm, quest: Quest, obstacle: Obstacle, aid: Aid, value: MoralValue,
         hero_name: str = "Mira", hero_type: str = "girl",
         brother_name: str = "Tobin", elder_type: str = "grandmother") -> World:
    world = World(realm)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    brother = world.add(Entity(id="brother", kind="character", type="brother", label=brother_name, role="brother"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))

    world.facts.update(
        hero=hero,
        brother=brother,
        elder=elder,
        realm=realm,
        quest=quest,
        obstacle=obstacle,
        aid=aid,
        value=value,
        got_item=False,
    )

    opening(world, hero, brother, elder, quest)
    set_out(world, hero, brother)

    world.para()
    spark_resentment(world, hero, brother, aid)
    warning(world, hero, brother, obstacle)
    stumble(world, hero, obstacle)

    world.para()
    surprise_help(world, hero, brother, obstacle, aid)
    confess(world, hero, brother)
    complete_quest(world, hero, brother, quest)

    world.para()
    ending(world, hero, brother, elder, quest, value)

    world.facts.update(
        softened=hero.memes["softened"] >= THRESHOLD,
        resentful_start=True,
        surprised=hero.memes["surprise"] >= THRESHOLD,
        moral_learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


REALMS = {
    "pinewood": Realm(
        "pinewood",
        "the Pinewood",
        "a needled path under tall green boughs",
        "sun-stripes trembled on the moss",
        affords={"thorns", "mist"},
    ),
    "moonhill": Realm(
        "moonhill",
        "Moonhill",
        "a white path curling around the hill",
        "larks sang over the stones",
        affords={"stream", "mist"},
    ),
    "reedmere": Realm(
        "reedmere",
        "the Mere of Reeds",
        "a narrow road by the whispering water",
        "silver ripples winked by the bank",
        affords={"stream", "thorns"},
    ),
}

QUESTS = {
    "moonblossom": Quest(
        "moonblossom",
        "a moonblossom",
        "the hill garden beyond the trees",
        "its cool petals could soothe the old grandmother's cough",
        "That night the moonblossom shone in a blue bowl by the window",
        tags={"flower", "healing"},
    ),
    "honeydrop": Quest(
        "honeydrop",
        "a honeydrop pear",
        "the orchard of the north lane",
        "its sweet juice would brighten the village baker's heavy day",
        "That evening the honeydrop pear rested golden on the table",
        tags={"pear", "kindness"},
    ),
    "sunthread": Quest(
        "sunthread",
        "a spool of sunthread",
        "the weaver's willow gate",
        "its bright thread could mend the torn festival banner",
        "By dusk the sunthread glimmered through the mended banner",
        tags={"thread", "festival"},
    ),
}

OBSTACLES = {
    "thorns": Obstacle(
        "thorns",
        "a hedge of moon-thorns",
        "Its silver thorns knitted so tightly that even a rabbit would have turned away.",
        "one wrong touch would leave little scratches all along her wrists",
        "gloves",
        values={"kindness", "gratitude"},
        tags={"thorns"},
    ),
    "mist": Obstacle(
        "mist",
        "a fold of sleeping mist",
        "The path vanished inside it, and every pine looked like three pines at once.",
        "she might walk in a circle until sunset",
        "lantern",
        values={"trust", "patience"},
        tags={"mist"},
    ),
    "stream": Obstacle(
        "stream",
        "a quick-bellied stream",
        "It skipped over the stones so fast that the bank looked farther away than it was.",
        "she might slip and soak the hem of her dress before the quest was done",
        "rope",
        values={"cooperation", "courage"},
        tags={"stream"},
    ),
}

AIDS = {
    "gloves": Aid(
        "gloves",
        "a pair of soft garden gloves",
        "he drew a pair of soft garden gloves from his satchel, hidden there since dawn",
        "slipped the gloves onto her hands and gently parted the thorns while he held the branches back",
        "thorns",
        tags={"gloves"},
    ),
    "lantern": Aid(
        "lantern",
        "a tin lantern with a star-cut lid",
        "he lifted a tiny lantern from his satchel, and warm gold pricked through the star-holes",
        "raised the lantern high and walked slowly so she could follow each bright step",
        "mist",
        tags={"lantern"},
    ),
    "rope": Aid(
        "rope",
        "a coil of blue rope",
        "he unwound a coil of blue rope from under his cloak, though he had said nothing about it all morning",
        "tied the rope between two willow roots and steadied her until both of them crossed",
        "stream",
        tags={"rope"},
    ),
}

VALUES = {
    "kindness": MoralValue(
        "kindness",
        "kindness",
        "Kindness often reaches the heart before pride can speak.",
        "From then on, her first step in a dark mood was to choose kindness.",
        tags={"kindness"},
    ),
    "gratitude": MoralValue(
        "gratitude",
        "gratitude",
        "Gratitude can untie a knot that resentment only pulls tighter.",
        "From then on, she thanked the hands that helped her before envy could grow.",
        tags={"gratitude"},
    ),
    "trust": MoralValue(
        "trust",
        "trust",
        "Trust lets two travelers see farther than either one alone.",
        "From then on, she remembered that trust can brighten a dim road.",
        tags={"trust"},
    ),
    "patience": MoralValue(
        "patience",
        "patience",
        "Patience keeps a frightened heart from choosing the wrong path.",
        "From then on, she breathed once before speaking in a sour mood.",
        tags={"patience"},
    ),
    "cooperation": MoralValue(
        "cooperation",
        "cooperation",
        "Cooperation turns two small strengths into one safe crossing.",
        "From then on, she reached for her brother's hand instead of walking apart.",
        tags={"cooperation"},
    ),
    "courage": MoralValue(
        "courage",
        "courage",
        "True courage is gentler than boasting, because it makes room for someone else.",
        "From then on, she knew courage could sound as soft as a helpful voice.",
        tags={"courage"},
    ),
}

GIRL_NAMES = ["Mira", "Elsie", "Nell", "Anya", "Lina", "Poppy"]
BOY_NAMES = ["Tobin", "Rowan", "Finn", "Milo", "Bram", "Oren"]

KNOWLEDGE = {
    "thorns": [(
        "Why can thorn bushes be hard to cross?",
        "Thorn bushes have sharp points that can scratch your skin and catch your clothes. "
        "That is why people move slowly around them or use protection on their hands."
    )],
    "mist": [(
        "Why is thick mist hard to walk through?",
        "Mist makes the air cloudy, so far-away things look blurry or disappear. "
        "When you cannot see the path well, it is easier to get lost."
    )],
    "stream": [(
        "Why can crossing a stream be slippery?",
        "Water runs over stones and makes them smooth and wet. "
        "Wet stones can be slippery, so careful help matters."
    )],
    "gloves": [(
        "What do gloves protect?",
        "Gloves cover your hands. They can help keep hands cleaner and safer from scratches or cold."
    )],
    "lantern": [(
        "What is a lantern for?",
        "A lantern gives light when a place is dark or dim. "
        "It helps people see the safe way ahead."
    )],
    "rope": [(
        "Why can a rope help on a crossing?",
        "A rope gives your hands something steady to hold. "
        "That can help people keep their balance."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to help, comfort, or care for someone. "
        "A kind act can change another person's whole day."
    )],
    "gratitude": [(
        "What is gratitude?",
        "Gratitude means noticing help or goodness and feeling thankful for it. "
        "It helps people remember they are not alone."
    )],
    "trust": [(
        "What is trust?",
        "Trust is believing someone will try to do the right thing. "
        "It grows when people are steady and caring."
    )],
    "patience": [(
        "What is patience?",
        "Patience is waiting calmly instead of rushing in a hot feeling. "
        "It gives you time to choose wisely."
    )],
    "cooperation": [(
        "What does cooperation mean?",
        "Cooperation means working together on the same job. "
        "Two people can often do something better together than alone."
    )],
    "courage": [(
        "What is courage?",
        "Courage is doing the needed thing even when you feel afraid. "
        "Real courage is often calm and helpful, not loud."
    )],
}
KNOWLEDGE_ORDER = [
    "thorns", "mist", "stream", "gloves", "lantern", "rope",
    "kindness", "gratitude", "trust", "patience", "cooperation", "courage",
]


@dataclass
class StoryParams:
    realm: str
    quest: str
    obstacle: str
    aid: str
    value: str
    hero_name: str
    hero_type: str
    brother_name: str
    elder: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    brother = f["brother"]
    quest = f["quest"]
    value = f["value"]
    obstacle = f["obstacle"]
    return [
        'Write a fairy-tale story for a 3-to-5-year-old that includes the words '
        '"resent", "brother", and "mood", and uses a quest, a surprise, and a moral value.',
        f"Tell a gentle fairy tale where {hero.label} begins to resent {hero.pronoun('possessive')} brother "
        f"{brother.label}'s bright mood during a quest for {quest.item}, but a surprise at {obstacle.label} changes the heart.",
        f"Write a child-facing fairy tale that ends by teaching {value.noun} through a brother and sister traveling together."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    brother = f["brother"]
    elder = f["elder"]
    quest = f["quest"]
    obstacle = f["obstacle"]
    aid = f["aid"]
    value = f["value"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {hero.pronoun('possessive')} brother {brother.label}, who were sent on a quest by their {elder.label}. "
            f"They had to fetch {quest.item} because {quest.use}."
        ),
        (
            f"Why was {hero.label} in a bad mood at the start?",
            f"{hero.label} felt hurt because {brother.label} carried {aid.label} and still looked cheerful, so {hero.pronoun()} began to resent {hero.pronoun('possessive')} brother's bright mood. "
            f"The sour feeling came from jealousy before {hero.pronoun()} understood what {brother.label} was really doing."
        ),
        (
            "What was the obstacle on the road?",
            f"They had to face {obstacle.label}. {obstacle.trouble}"
        ),
        (
            f"What was the surprise?",
            f"The surprise was that {brother.label} had secretly brought {aid.label}. "
            f"He revealed it at the hard moment and used it to help {hero.label} through the obstacle."
        ),
        (
            f"How did the quest change {hero.label}'s feelings?",
            f"{hero.label}'s resentment melted when {hero.pronoun()} saw that {brother.label} had been preparing to help all along. "
            f"After that, the quest felt shared instead of lonely, and gratitude took the place of the bad mood."
        ),
        (
            "What moral did the story teach?",
            f"It taught {value.noun}. The lesson mattered because {brother.label}'s helpful act solved the problem more strongly than pride or envy ever could."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= f["obstacle"].tags
    tags |= f["aid"].tags
    tags |= f["value"].tags
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = [f"label={e.label!r}"]
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    facts = {k: v for k, v in world.facts.items() if k in {"got_item", "softened", "surprised", "moral_learned"}}
    if facts:
        lines.append(f"  facts: {facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pinewood", "moonblossom", "thorns", "gloves", "kindness", "Mira", "girl", "Tobin", "grandmother"),
    StoryParams("moonhill", "sunthread", "mist", "lantern", "trust", "Elsie", "girl", "Rowan", "grandmother"),
    StoryParams("reedmere", "honeydrop", "stream", "rope", "cooperation", "Nell", "girl", "Finn", "grandmother"),
    StoryParams("pinewood", "honeydrop", "mist", "lantern", "patience", "Anya", "girl", "Milo", "grandmother"),
    StoryParams("reedmere", "moonblossom", "thorns", "gloves", "gratitude", "Lina", "girl", "Bram", "grandmother"),
]


ASP_RULES = r"""
compatible_aid(O, A) :- obstacle(O), aid(A), solves(A, O).
good_value(O, V) :- obstacle_value(O, V).

valid(R, Q, O, A, V) :-
    realm(R), quest(Q), obstacle(O), aid(A), value(V),
    affords(R, O),
    compatible_aid(O, A),
    good_value(O, V).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, realm in REALMS.items():
        lines.append(asp.fact("realm", rid))
        for oid in sorted(realm.affords):
            lines.append(asp.fact("affords", rid, oid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for oid, obs in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        for vid in sorted(obs.values):
            lines.append(asp.fact("obstacle_value", oid, vid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("solves", aid_id, aid.for_obstacle))
    for vid in VALUES:
        lines.append(asp.fact("value", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child begins to resent a brother's mood on a quest, "
                    "then learns a moral through a surprising kindness."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--hero-name")
    ap.add_argument("--brother-name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.aid and not compatible_aid(OBSTACLES[args.obstacle], AIDS[args.aid]):
        value = VALUES[args.value] if args.value else next(iter(VALUES.values()))
        raise StoryError(explain_rejection(OBSTACLES[args.obstacle], AIDS[args.aid], value))
    if args.obstacle and args.value and not valid_value(OBSTACLES[args.obstacle], VALUES[args.value]):
        aid = AIDS[args.aid] if args.aid else next(iter(AIDS.values()))
        raise StoryError(explain_rejection(OBSTACLES[args.obstacle], aid, VALUES[args.value]))

    combos = [
        c for c in valid_combos()
        if (args.realm is None or c[0] == args.realm)
        and (args.quest is None or c[1] == args.quest)
        and (args.obstacle is None or c[2] == args.obstacle)
        and (args.aid is None or c[3] == args.aid)
        and (args.value is None or c[4] == args.value)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm, quest, obstacle, aid, value = rng.choice(sorted(combos))
    hero_name = args.hero_name or rng.choice(GIRL_NAMES)
    brother_name = args.brother_name or rng.choice([n for n in BOY_NAMES if n != hero_name])
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    return StoryParams(realm, quest, obstacle, aid, value, hero_name, "girl", brother_name, elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        REALMS[params.realm],
        QUESTS[params.quest],
        OBSTACLES[params.obstacle],
        AIDS[params.aid],
        VALUES[params.value],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        brother_name=params.brother_name,
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story_qa or not sample.world_qa:
            raise StoryError("generated story missing QA")
        print("OK: default resolve/generate path works.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, quest, obstacle, aid, value) combos:\n")
        for realm, quest, obstacle, aid, value in combos:
            print(f"  {realm:9} {quest:11} {obstacle:8} {aid:8} {value}")
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
            header = f"### {p.hero_name} and {p.brother_name}: {p.quest} via {p.obstacle} ({p.value})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
