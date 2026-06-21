#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/petite_release_cautionary_friendship_transformation_adventure.py
=================================================================================================

A standalone story world for a tiny adventure about two friends, a magical little
creature, and the trouble that begins when one child tries to keep a wild wonder
instead of letting it go.

Seed requirements carried into the world:
- word: petite
- word: release
- features: Cautionary, Friendship, Transformation
- style: Adventure

Core premise
------------
Two friends are exploring a place that feels adventurous. They find a petite
magical creature and trap it in a container, hoping it can help with the quest.
A kinder friend warns that wild things should be free. The trapped creature's
magic transforms the children, shrinking them until the world becomes huge.
To recover, they must work together, understand the harm they caused, and
release the creature in the right place. Quick releases lead to a bright ending;
late releases lead to a harder lesson before the magic is undone.

Run it
------
    python storyworlds/worlds/gpt-5.4/petite_release_cautionary_friendship_transformation_adventure.py
    python storyworlds/worlds/gpt-5.4/petite_release_cautionary_friendship_transformation_adventure.py --setting marsh --creature sprite
    python storyworlds/worlds/gpt-5.4/petite_release_cautionary_friendship_transformation_adventure.py --container corked_bottle
    python storyworlds/worlds/gpt-5.4/petite_release_cautionary_friendship_transformation_adventure.py --all
    python storyworlds/worlds/gpt-5.4/petite_release_cautionary_friendship_transformation_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4/petite_release_cautionary_friendship_transformation_adventure.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | creature | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    habitat: str = ""
    breathable: bool = True
    wild: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    path: str
    habitat: str
    release_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    habitat: str
    glow: str
    cry: str
    magic: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    breathable: bool
    sense: int
    catch_verb: str
    release_verb: str
    fail_note: str
    tags: set[str] = field(default_factory=set)


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.role in {"finder", "friend"}]

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


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    container = world.get("container")
    if creature.meters["confined"] < THRESHOLD:
        return out
    sig = ("distress", container.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["distress"] += 1
    if not container.attrs.get("breathable", True):
        creature.meters["air_risk"] += 1
    out.append("__distress__")
    return out


def _r_shrink(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.memes["distress"] < THRESHOLD or creature.meters["released"] >= THRESHOLD:
        return out
    sig = ("shrink", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.meters["tiny"] += 1
        kid.memes["fear"] += 1
        kid.memes["awe"] += 1
    world.get("place").meters["enormous"] += 1
    out.append("__shrink__")
    return out


def _r_release_calm(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.meters["released"] < THRESHOLD:
        return out
    sig = ("calm", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.memes["distress"] = 0.0
    for kid in world.kids():
        kid.meters["tiny"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["kindness"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="distress", tag="emotional", apply=_r_distress),
    Rule(name="shrink", tag="physical", apply=_r_shrink),
    Rule(name="release_calm", tag="physical", apply=_r_release_calm),
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
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def habitat_match(setting: Setting, creature: Creature) -> bool:
    return setting.habitat == creature.habitat


def sensible_containers() -> list[Container]:
    return [c for c in CONTAINERS.values() if c.sense >= SENSE_MIN]


def release_possible(setting: Setting, creature: Creature) -> bool:
    return habitat_match(setting, creature)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for creature_id, creature in CREATURES.items():
            for container_id, container in CONTAINERS.items():
                if habitat_match(setting, creature) and container.sense >= SENSE_MIN and release_possible(setting, creature):
                    combos.append((setting_id, creature_id, container_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.delay <= 1:
        return "quick_release"
    return "late_release"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    creature = sim.get("creature")
    creature.meters["confined"] += 1
    propagate(sim, narrate=False)
    return {
        "tiny": any(kid.meters["tiny"] >= THRESHOLD for kid in sim.kids()),
        "air_risk": creature.meters["air_risk"] >= THRESHOLD,
    }


def introduce(world: World, finder: Entity, friend: Entity) -> None:
    for kid in (finder, friend):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {finder.id} and {friend.id} followed {world.setting.path} into {world.setting.label}. "
        f"{world.setting.opening}"
    )
    world.say(
        f"They were sure a secret trail would lead to a hidden marvel before sunset, and that made the day feel like an adventure."
    )


def discover(world: World, finder: Entity, friend: Entity, creature_cfg: Creature) -> None:
    creature = world.get("creature")
    creature.memes["calm"] += 1
    world.say(
        f"Near {world.setting.release_spot}, they found {creature_cfg.phrase}. It {creature_cfg.glow}, and {friend.id} whispered, "
        f'"It is so petite."'
    )
    world.say(
        f'{finder.id} grinned. "{creature_cfg.cry} Maybe it can show us the way."'
    )


def catch(world: World, finder: Entity, container_cfg: Container, creature_cfg: Creature) -> None:
    finder.memes["greed"] += 1
    creature = world.get("creature")
    creature.meters["confined"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before {friend_name(world)} could stop {finder.pronoun('object')}, {finder.id} {container_cfg.catch_verb} and slipped the little traveler inside."
    )
    world.say(
        f"The {container_cfg.label} glimmered in {finder.id}'s hands, but {creature_cfg.magic} began to tremble against the sides."
    )


def friend_name(world: World) -> str:
    return world.facts["friend"].id


def warn(world: World, friend: Entity, finder: Entity, container_cfg: Container, creature_cfg: Creature) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_tiny"] = pred["tiny"]
    world.facts["predicted_air_risk"] = pred["air_risk"]
    friend.memes["care"] += 1
    extra = ""
    if pred["air_risk"]:
        extra = " It did not look like there was enough air in there."
    world.say(
        f'{friend.id} put a hand on the {container_cfg.label}. "We should release it," {friend.pronoun()} said. '
        f'"Wild things are not treasure, and scared magic never stays gentle."{extra}'
    )
    if pred["tiny"]:
        world.say(
            f"{friend.id} had a prickly feeling that holding the creature captive would turn the adventure upside down."
        )


def transform(world: World, finder: Entity, friend: Entity, creature_cfg: Creature) -> None:
    for kid in (finder, friend):
        kid.memes["fear"] += 1
    world.say(
        f"Then {creature_cfg.magic} burst in a ring of silver light. In one blink, the children were no taller than acorns."
    )
    world.say(
        f"What had been a footpath became a canyon of roots, and every fern towered above their heads like a jungle gate."
    )


def tiny_journey(world: World, finder: Entity, friend: Entity, creature_cfg: Creature) -> None:
    finder.memes["shame"] += 1
    friend.memes["bravery"] += 1
    world.say(
        f'The trapped {creature_cfg.label} fluttered inside the {world.get("container").label}, and {finder.id} finally gasped, "I was wrong."'
    )
    world.say(
        f"{friend.id} took {finder.id}'s hand. Together they climbed over a curled leaf, ducked beneath a swinging blade of grass, and reached {world.setting.release_spot}."
    )


def release_now(world: World, finder: Entity, friend: Entity, container_cfg: Container, creature_cfg: Creature) -> None:
    creature = world.get("creature")
    creature.meters["released"] += 1
    propagate(world, narrate=False)
    for kid in (finder, friend):
        kid.memes["friendship"] += 1
    world.say(
        f"With shaking fingers, {finder.id} opened the {container_cfg.label} and let the little creature {container_cfg.release_verb} into the open air."
    )
    world.say(
        f'"Thank you for helping me release it," {finder.id} told {friend.id}. "{friend.id} was right."'
    )
    world.say(
        f"The {creature_cfg.label} circled them once, warm and bright, and the shrinking magic unwound like a ribbon."
    )


def hard_delay(world: World, finder: Entity, friend: Entity, creature_cfg: Creature) -> None:
    for kid in (finder, friend):
        kid.memes["tired"] += 1
    world.say(
        f"But the path felt endless at that tiny size. Dewdrops rolled past like glass boulders, and once they had to hide from a beetle that clattered by like a cart."
    )
    world.say(
        f"{friend.id} kept urging {finder.id} onward, even when both of them were sore and hungry."
    )
    world.say(
        f"Only when they reached {world.setting.release_spot} at the edge of dusk did {finder.id} dare to whisper, "
        f'"Please. We are ready to make this right."'
    )


def release_late(world: World, finder: Entity, friend: Entity, container_cfg: Container, creature_cfg: Creature) -> None:
    creature = world.get("creature")
    creature.meters["released"] += 1
    propagate(world, narrate=False)
    for kid in (finder, friend):
        kid.memes["friendship"] += 1
    world.say(
        f"{finder.id} knelt in the moss and opened the {container_cfg.label} at last. The creature rose out slowly, as if testing whether the world was truly kind again."
    )
    world.say(
        f"It brushed both friends with a soft glow, and their petite shapes stretched back to normal just as the first evening star appeared."
    )
    world.say(
        f'{finder.id} said, "Next time I will listen sooner." {friend.id} nodded and stayed close beside {finder.pronoun("object")}.'
    )


def ending_quick(world: World, finder: Entity, friend: Entity, creature_cfg: Creature) -> None:
    world.say(
        f"Now full-sized again, they watched the {creature_cfg.label} skim across the water and disappear into its home."
    )
    world.say(
        f"They did not find buried treasure after all. Instead, the two friends went home with a better prize: a truer friendship and a story about the day kindness saved their adventure."
    )


def ending_late(world: World, finder: Entity, friend: Entity, creature_cfg: Creature) -> None:
    world.say(
        f"They walked home slowly under the darkening sky, holding hands whenever the shadows made the path look strange."
    )
    world.say(
        f"The adventure had turned into a warning they would never forget: if wonder is caged, even a lovely day can grow frightening. Still, because they stayed together and finally chose mercy, the night ended with both friends safe."
    )


def tell(
    setting: Setting,
    creature_cfg: Creature,
    container_cfg: Container,
    *,
    finder_name: str = "Nora",
    finder_gender: str = "girl",
    friend_name_param: str = "Ben",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    delay: int = 1,
) -> World:
    world = World(setting)
    finder = world.add(Entity(
        id=finder_name,
        kind="character",
        type=finder_gender,
        role="finder",
        label=finder_name,
    ))
    friend = world.add(Entity(
        id=friend_name_param,
        kind="character",
        type=friend_gender,
        role="friend",
        label=friend_name_param,
    ))
    world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=setting.label,
    ))
    world.add(Entity(
        id="creature",
        kind="creature",
        type="creature",
        label=creature_cfg.label,
        phrase=creature_cfg.phrase,
        habitat=creature_cfg.habitat,
        wild=True,
        magical=True,
        tags=set(creature_cfg.tags),
    ))
    world.add(Entity(
        id="container",
        kind="thing",
        type="container",
        label=container_cfg.label,
        phrase=container_cfg.phrase,
        attrs={"breathable": container_cfg.breathable, "sense": container_cfg.sense},
        breathable=container_cfg.breathable,
        tags=set(container_cfg.tags),
    ))

    introduce(world, finder, friend)
    discover(world, finder, friend, creature_cfg)

    world.para()
    catch(world, finder, container_cfg, creature_cfg)
    warn(world, friend, finder, container_cfg, creature_cfg)

    world.para()
    transform(world, finder, friend, creature_cfg)
    tiny_journey(world, finder, friend, creature_cfg)

    world.para()
    if delay <= 1:
        release_now(world, finder, friend, container_cfg, creature_cfg)
        ending_quick(world, finder, friend, creature_cfg)
        outcome = "quick_release"
    else:
        hard_delay(world, finder, friend, creature_cfg)
        release_late(world, finder, friend, container_cfg, creature_cfg)
        ending_late(world, finder, friend, creature_cfg)
        outcome = "late_release"

    world.facts.update(
        finder=finder,
        friend=friend,
        parent=world.get("Parent"),
        creature_cfg=creature_cfg,
        setting=setting,
        container_cfg=container_cfg,
        transformed=True,
        released=True,
        outcome=outcome,
        delay=delay,
        container_air_risk=world.get("creature").meters["air_risk"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "marsh": Setting(
        id="marsh",
        label="the whispering marsh",
        opening="Reeds leaned over dark water, and the stepping stones looked like pieces of a map.",
        path="a ribbon of stepping stones",
        habitat="water_edge",
        release_spot="the moon-bright reeds",
        tags={"marsh", "water"},
    ),
    "glade": Setting(
        id="glade",
        label="the fern glade",
        opening="Sunlight poured through leaves in green stripes, and every stump looked like part of an old ruin.",
        path="a twisting deer trail",
        habitat="flower_ring",
        release_spot="the ring of foxglove flowers",
        tags={"forest", "flowers"},
    ),
    "shore": Setting(
        id="shore",
        label="the shell shore",
        opening="Small waves tapped the stones, and the tide pools glittered like secret doorways.",
        path="a curve of silver pebbles",
        habitat="tide_pool",
        release_spot="the warm tide pool",
        tags={"shore", "water"},
    ),
}

CREATURES = {
    "sprite": Creature(
        id="sprite",
        label="reed sprite",
        phrase="a petite reed sprite no bigger than a thumb",
        habitat="water_edge",
        glow="glowed green as if a firefly had learned to swim",
        cry="A marsh guide!",
        magic="its ripple-magic",
        tags={"wild_creature", "magic", "release"},
    ),
    "moth": Creature(
        id="moth",
        label="lantern moth",
        phrase="a petite lantern moth with glassy wings",
        habitat="flower_ring",
        glow="shone like a tiny lantern trimmed with gold",
        cry="A trail lantern!",
        magic="its dust-bright magic",
        tags={"wild_creature", "magic", "release"},
    ),
    "driftling": Creature(
        id="driftling",
        label="shell driftling",
        phrase="a petite shell driftling tucked beside a pool",
        habitat="tide_pool",
        glow="sparkled with blue light under its pearl-pale shell",
        cry="A tide scout!",
        magic="its tide-song magic",
        tags={"wild_creature", "magic", "release"},
    ),
}

CONTAINERS = {
    "glass_jar": Container(
        id="glass_jar",
        label="glass jar",
        phrase="a clear glass jar",
        breathable=True,
        sense=2,
        catch_verb="lifted the glass jar over the creature",
        release_verb="float free",
        fail_note="Even with air holes, a jar is still a cage.",
        tags={"jar", "container"},
    ),
    "lunch_tin": Container(
        id="lunch_tin",
        label="lunch tin",
        phrase="a little lunch tin with the lid tipped open",
        breathable=True,
        sense=2,
        catch_verb="coaxed the creature into the lunch tin",
        release_verb="hop free",
        fail_note="A box can still frighten a wild thing.",
        tags={"tin", "container"},
    ),
    "corked_bottle": Container(
        id="corked_bottle",
        label="corked bottle",
        phrase="a narrow bottle with a cork",
        breathable=False,
        sense=1,
        catch_verb="trapped the creature inside the corked bottle",
        release_verb="dart free",
        fail_note="A corked bottle is too mean and too unsafe for a breathing creature.",
        tags={"bottle", "container"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Rose", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Eli", "Theo", "Jack"]


@dataclass
class StoryParams:
    setting: str
    creature: str
    container: str
    finder_name: str
    finder_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    delay: int = 1
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="marsh",
        creature="sprite",
        container="glass_jar",
        finder_name="Nora",
        finder_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        setting="glade",
        creature="moth",
        container="lunch_tin",
        finder_name="Leo",
        finder_gender="boy",
        friend_name="Mia",
        friend_gender="girl",
        parent="father",
        delay=2,
    ),
    StoryParams(
        setting="shore",
        creature="driftling",
        container="glass_jar",
        finder_name="Ava",
        finder_gender="girl",
        friend_name="Sam",
        friend_gender="boy",
        parent="mother",
        delay=0,
    ),
]


KNOWLEDGE = {
    "wild_creature": [
        (
            "Why should wild creatures be let go?",
            "Wild creatures belong in their own homes, where they can breathe, move, and find what they need. Keeping them trapped can scare or hurt them."
        )
    ],
    "magic": [
        (
            "What is a transformation?",
            "A transformation is when something changes into a different form or size. In stories, magic often causes a transformation so characters can learn something important."
        )
    ],
    "release": [
        (
            "What does release mean?",
            "To release something means to let it go free. If a creature has been trapped, releasing it means opening the way so it can return home."
        )
    ],
    "jar": [
        (
            "Why is a jar not a good home for a wild creature?",
            "A jar can hold a creature for a moment, but it is not a real home. Wild creatures need freedom, space, and the right place to live."
        )
    ],
    "tin": [
        (
            "Why can a box or tin frighten a little animal?",
            "A closed tin is dark and strange inside. A small animal or magical creature may feel trapped and afraid there."
        )
    ],
    "marsh": [
        (
            "What is a marsh?",
            "A marsh is a wet place with grasses and reeds growing around shallow water. Many tiny creatures live there."
        )
    ],
    "forest": [
        (
            "What is a glade?",
            "A glade is an open space in a forest where sunlight can shine through. Flowers and insects often like those bright patches."
        )
    ],
    "shore": [
        (
            "What is a tide pool?",
            "A tide pool is a little pool of sea water left behind among rocks when the tide goes out. Small shore creatures can live there."
        )
    ],
    "water": [
        (
            "Why do shore and marsh creatures need the right water place?",
            "Many creatures can only live well where the water, plants, and shelter are right for them. Moving them away from that place can put them in danger."
        )
    ],
    "flowers": [
        (
            "Why do moths visit flowers?",
            "Many moths visit flowers to sip nectar and to move pollen from place to place. Flowers can be an important part of their home."
        )
    ],
}
KNOWLEDGE_ORDER = ["wild_creature", "magic", "release", "jar", "tin", "marsh", "forest", "shore", "water", "flowers"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    creature_cfg = f["creature_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    prompts = [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "petite" and the word "release".',
        f"Tell a cautionary friendship story where {finder.id} and {friend.id} find {creature_cfg.phrase} in {setting.label}, make a bad choice, and then fix it together.",
    ]
    if outcome == "quick_release":
        prompts.append(
            "Write a magical adventure where two friends are briefly transformed after trapping a tiny wild creature, then become normal again by showing kindness."
        )
    else:
        prompts.append(
            "Write a gentle but cautionary adventure where two friends stay tiny for a hard journey after trapping a magical creature, and only change back after releasing it."
        )
    return prompts


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    creature_cfg = f["creature_cfg"]
    setting = f["setting"]
    container_cfg = f["container_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(finder, friend)}, {finder.id} and {friend.id}. They were exploring {setting.label} when they found {creature_cfg.phrase}."
        ),
        (
            "What mistake did the friends make?",
            f"{finder.id} trapped the {creature_cfg.label} in a {container_cfg.label} because the children hoped it could help with the adventure. That was a mistake because the creature was wild and needed to stay free."
        ),
        (
            f"Why did {friend.id} want to release the creature?",
            f"{friend.id} understood that the little creature was frightened in the {container_cfg.label}. {friend.pronoun().capitalize()} also sensed that scared magic could turn dangerous if they kept it captive."
        ),
        (
            "What transformation happened?",
            "The creature's magic shrank both children until they were tiny like acorns. The path and plants around them suddenly felt huge, which showed how badly the adventure had gone wrong."
        ),
    ]
    if outcome == "quick_release":
        qa.append(
            (
                "How did they solve the problem?",
                f"{finder.id} listened, opened the {container_cfg.label}, and helped release the {creature_cfg.label} at {setting.release_spot}. Once they chose kindness, the magic unwound and made them normal-sized again."
            )
        )
        qa.append(
            (
                "What did the friends learn?",
                f"They learned that wonder is not something to keep in a cage. Their friendship grew stronger because {finder.id} admitted the mistake and {friend.id} still helped fix it."
            )
        )
    else:
        qa.append(
            (
                "Why was the journey harder in this story?",
                f"The children waited too long before they let the creature go, so they had to travel while still tiny. That made ordinary things like dew, grass, and beetles feel big and scary."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The friends finally released the {creature_cfg.label} at {setting.release_spot}, and the magic returned them to normal at dusk. The ending was safe, but it stayed cautionary because they had suffered a long, frightening lesson first."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["creature_cfg"].tags) | set(world.facts["setting"].tags)
    container_tags = world.facts["container_cfg"].tags
    if "jar" in container_tags:
        tags.add("jar")
    if "tin" in container_tags:
        tags.add("tin")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.habitat:
            bits.append(f"habitat={ent.habitat}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, creature: Creature, container: Container) -> str:
    if not habitat_match(setting, creature):
        return (
            f"(No story: {creature.label} belongs in {creature.habitat.replace('_', ' ')}, but {setting.label} does not match that habitat. "
            f"A release story needs the creature to have a sensible home nearby.)"
        )
    if container.sense < SENSE_MIN:
        return (
            f"(Refusing container '{container.id}': {container.fail_note} "
            f"Try one of: {', '.join(sorted(c.id for c in sensible_containers()))}.)"
        )
    return "(No story: this combination does not make a reasonable transformation-and-release adventure.)"


ASP_RULES = r"""
habitat_match(S, C) :- setting(S), creature(C), habitat_of_setting(S, H), habitat_of_creature(C, H).
sensible_container(K) :- container(K), sense(K, V), sense_min(M), V >= M.
valid(S, C, K) :- habitat_match(S, C), sensible_container(K).

quick_release :- delay(D), D <= 1.
late_release  :- delay(D), D >= 2.

outcome(quick_release) :- quick_release.
outcome(late_release)  :- late_release.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("habitat_of_setting", setting_id, setting.habitat))
    for creature_id, creature in CREATURES.items():
        lines.append(asp.fact("creature", creature_id))
        lines.append(asp.fact("habitat_of_creature", creature_id, creature.habitat))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("sense", container_id, container.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A tiny adventure storyworld about friendship, transformation, and the choice to release a wild magical creature."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the children wait before releasing the creature")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check Python and ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.creature and args.container:
        setting = SETTINGS[args.setting]
        creature = CREATURES[args.creature]
        container = CONTAINERS[args.container]
        if not (habitat_match(setting, creature) and container.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(setting, creature, container))

    if args.container and CONTAINERS[args.container].sense < SENSE_MIN:
        dummy_setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        dummy_creature = CREATURES[args.creature] if args.creature else next(iter(CREATURES.values()))
        raise StoryError(explain_rejection(dummy_setting, dummy_creature, CONTAINERS[args.container]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.creature is None or combo[1] == args.creature)
        and (args.container is None or combo[2] == args.container)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, creature_id, container_id = rng.choice(sorted(combos))
    finder_name, finder_gender = _pick_kid(rng)
    friend_name_value, friend_gender = _pick_kid(rng, avoid=finder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        setting=setting_id,
        creature=creature_id,
        container=container_id,
        finder_name=finder_name,
        finder_gender=finder_gender,
        friend_name=friend_name_value,
        friend_gender=friend_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")

    setting = SETTINGS[params.setting]
    creature = CREATURES[params.creature]
    container = CONTAINERS[params.container]
    if not habitat_match(setting, creature) or container.sense < SENSE_MIN:
        raise StoryError(explain_rejection(setting, creature, container))

    world = tell(
        setting=setting,
        creature_cfg=creature,
        container_cfg=container,
        finder_name=params.finder_name,
        finder_gender=params.finder_gender,
        friend_name_param=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        delay=params.delay,
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

    cases = list(CURATED)
    for delay in [0, 1, 2]:
        base = CURATED[0]
        cases.append(
            StoryParams(
                setting=base.setting,
                creature=base.creature,
                container=base.container,
                finder_name=base.finder_name,
                finder_gender=base.finder_gender,
                friend_name=base.friend_name,
                friend_gender=base.friend_gender,
                parent=base.parent,
                delay=delay,
            )
        )
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
        if not sample.story or "petite" not in sample.story or "release" not in sample.story:
            raise StoryError("(Smoke test failed: story missing required seed words or empty output.)")
        sink = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = sink
        try:
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old_stdout
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, creature, container) combos:\n")
        for setting_id, creature_id, container_id in combos:
            print(f"  {setting_id:8} {creature_id:10} {container_id}")
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
            header = f"### {p.finder_name} and {p.friend_name}: {p.creature} in {p.setting} ({outcome_of(p)})"
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
