#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/doze_radiate_deep_puddle_magic_surprise_bad.py
=========================================================================

A standalone storyworld for a tiny superhero-style domain:

A child playing superhero beside a deep puddle sees something stranded in the
water. A magic charm begins to radiate light in a surprising way, showing that
the puddle is deeper than it looks. A wiser companion may stop the leap before
it happens; otherwise the child jumps in, a grown-up must help, and the ending
depends on whether the chosen rescue method is strong enough for the depth and
delay.

This world keeps the seed words "doze" and "radiate" in the story text while
treating them as state-driven beats, not as random token swaps.

Run it
------
    python storyworlds/worlds/gpt-5.4/doze_radiate_deep_puddle_magic_surprise_bad.py
    python storyworlds/worlds/gpt-5.4/doze_radiate_deep_puddle_magic_surprise_bad.py --target reflection
    python storyworlds/worlds/gpt-5.4/doze_radiate_deep_puddle_magic_surprise_bad.py --response superhero_jump
    python storyworlds/worlds/gpt-5.4/doze_radiate_deep_puddle_magic_surprise_bad.py --all
    python storyworlds/worlds/gpt-5.4/doze_radiate_deep_puddle_magic_surprise_bad.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/doze_radiate_deep_puddle_magic_surprise_bad.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
class MagicItem:
    id: str
    label: str = ""
    phrase: str = ""
    glow: str = ""
    lesson: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str = ""
    phrase: str = ""
    place_text: str = ""
    peril_text: str = ""
    need_text: str = ""
    drift: int = 1
    retrievable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int = 0
    power: int = 0
    text: str = ""
    fail: str = ""
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
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "sidekick"}]

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


def _r_puddle_risk(world: World) -> list[str]:
    hero = world.entities.get("hero")
    puddle = world.entities.get("puddle")
    if hero is None or puddle is None:
        return []
    if hero.meters["in_puddle"] < THRESHOLD:
        return []
    sig = ("puddle_risk", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["wet"] += 1
    hero.meters["muddy"] += 1
    puddle.meters["danger"] += 1
    for child in world.children():
        child.memes["fear"] += 1
    return ["__splash__"]


def _r_glow_reveals(world: World) -> list[str]:
    charm = world.entities.get("magic")
    puddle = world.entities.get("puddle")
    if charm is None or puddle is None:
        return []
    if charm.meters["glowing"] < THRESHOLD:
        return []
    sig = ("glow_reveals", charm.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    puddle.meters["revealed_depth"] += 1
    for child in world.children():
        child.memes["awe"] += 1
    return ["__glow__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="puddle_risk", tag="physical", apply=_r_puddle_risk),
    Rule(name="glow_reveals", tag="magic", apply=_r_glow_reveals),
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


def target_at_risk(target: Target) -> bool:
    return target.retrievable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def puddle_severity(target: Target, delay: int) -> int:
    return 1 + target.drift + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= puddle_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, hero_age: int, sidekick_age: int, trait: str) -> bool:
    sidekick_older = relation == "siblings" and sidekick_age > hero_age
    authority = initial_caution(trait) + 1.0 + (3.0 if sidekick_older else 0.0)
    return sidekick_older and authority > BRAVERY_INIT


def predict_leap(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["in_puddle"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("puddle").meters["danger"],
        "wet": sim.get("hero").meters["wet"],
        "revealed_depth": sim.get("puddle").meters["revealed_depth"],
    }


def opening(world: World, hero: Entity, sidekick: Entity, magic: MagicItem, target: Target) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"After a hard rain, {hero.id} and {sidekick.id} stood beside a deep puddle that spread across the path like a shadowy lake."
    )
    world.say(
        f"They had tied towels around their shoulders like superhero capes. Even the last little wind seemed ready to doze, but {hero.id} still bounced on brave feet."
    )
    world.say(
        f"In {hero.id}'s pocket was {magic.phrase}. {target.place_text}"
    )


def surprise_glow(world: World, hero: Entity, sidekick: Entity, magic: MagicItem, target: Target) -> None:
    charm = world.get("magic")
    charm.meters["glowing"] += 1
    propagate(world, narrate=False)
    world.facts["surprise"] = True
    hero.memes["bravado"] += 1
    world.say(
        f"Then came the surprise. {magic.phrase.capitalize()} began to radiate {magic.glow}, and the bright shimmer showed {target.peril_text}."
    )
    world.say(
        f'"Super mission!" {hero.id} said. "I can save it."'
    )
    if world.get("puddle").meters["revealed_depth"] >= THRESHOLD:
        world.say(
            f"{sidekick.id} saw at once that the middle of the puddle was deeper and darker than it had looked from the grass."
        )


def warn(world: World, sidekick: Entity, hero: Entity, guardian: Entity, magic: MagicItem, target: Target) -> None:
    pred = predict_leap(world)
    sidekick.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{sidekick.id} grabbed {hero.id}\'s sleeve. "{hero.id}, wait," {sidekick.pronoun()} said. "{guardian.label_word.capitalize()} said deep puddles can hide slippery mud. {magic.label.capitalize()} is warning us, not giving us flying feet."'
    )


def back_down(world: World, hero: Entity, sidekick: Entity, guardian: Entity, target: Target) -> None:
    hero.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    hero.memes["bravery"] = 0.0
    world.say(
        f"{hero.id} looked at the dark middle of the puddle, then at {sidekick.id}, and the brave jump melted away."
    )
    world.say(
        f'"You\'re right," {hero.pronoun()} said. "Real heroes ask for help before somebody gets hurt." They called {guardian.label_word} instead of charging in.'
    )


def defy(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I\'m the fastest hero here!" {hero.id} said, and before {sidekick.id} could stop {hero.pronoun("object")}, {hero.pronoun()} sprang toward the water.'
    )


def leap_in(world: World, hero: Entity, target: Target, magic: MagicItem) -> None:
    hero.meters["in_puddle"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} landed with a huge sploosh. Cold muddy water swallowed {hero.pronoun('possessive')} boots, and the deep puddle tugged at {hero.pronoun('possessive')} knees."
    )
    world.say(
        f"{target.need_text} At the same moment, {magic.phrase} slipped out and kept trying to radiate through the brown water like a tiny buried star."
    )


def alarm(world: World, sidekick: Entity, hero: Entity, guardian: Entity) -> None:
    world.say(f'"{guardian.label_word.capitalize()}!" {sidekick.id} shouted. "{hero.id} is stuck!"')


def rescue_success(world: World, guardian: Entity, response: Response, target: Target) -> None:
    hero = world.get("hero")
    hero.meters["in_puddle"] = 0.0
    hero.meters["safe"] += 1
    world.get("puddle").meters["danger"] = 0.0
    world.say(
        f"{guardian.label_word.capitalize()} came running and {response.text.replace('{target}', target.label)}."
    )
    world.say(
        f"Soon {hero.id} was back on the grass, dripping and shaky but safe, with {target.phrase} rescued at last."
    )


def lesson(world: World, guardian: Entity, hero: Entity, sidekick: Entity, magic: MagicItem) -> None:
    for child in (hero, sidekick):
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        child.memes["fear"] = 0.0
    world.say(
        f"{guardian.label_word.capitalize()} wrapped both children in dry towels. \"A glow can help you notice danger,\" {guardian.pronoun()} said, \"but magic is not a reason to jump into deep water.\""
    )
    world.say(
        f'{hero.id} nodded. "{magic.lesson}"'
    )


def happy_end(world: World, hero: Entity, sidekick: Entity, guardian: Entity, magic: MagicItem) -> None:
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    world.say(
        f"Later, when the sun peeked through, {magic.phrase} shone again from the porch rail, gentle this time instead of urgent."
    )
    world.say(
        f"{hero.id} and {sidekick.id} stood on the safe side of the puddle and practiced superhero poses while {guardian.label_word} cheered. They still felt brave, but now their bravery had room for listening."
    )


def rescue_fail(world: World, guardian: Entity, response: Response, target: Target, magic: MagicItem) -> None:
    hero = world.get("hero")
    hero.meters["safe"] += 1
    hero.meters["in_puddle"] = 0.0
    world.get("puddle").meters["danger"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} came running and {response.fail.replace('{target}', target.label)}."
    )
    world.say(
        f"{hero.id} was pulled out safely, but the puddle had already swallowed too much of the mission."
    )
    world.facts["lost_magic"] = True
    world.facts["target_lost"] = True
    world.get("magic").meters["lost"] += 1
    world.get("target").meters["lost"] += 1


def bad_end(world: World, hero: Entity, sidekick: Entity, target: Target, magic: MagicItem) -> None:
    for child in (hero, sidekick):
        child.memes["sadness"] += 1
        child.memes["lesson"] += 1
    world.say(
        f"The muddy water rolled {target.phrase} into a storm drain, and {magic.phrase} vanished after it with one last blink of light."
    )
    world.say(
        f"{hero.id}'s cape hung heavy and brown. No one played superhero after that. They walked home quietly, surprised at how a pretend rescue had turned into a bad ending."
    )


def safe_after_avert(world: World, hero: Entity, sidekick: Entity, guardian: Entity, target: Target, response: Response, magic: MagicItem) -> None:
    world.say(
        f"{guardian.label_word.capitalize()} came with calm steps and {response.text.replace('{target}', target.label)}."
    )
    world.say(
        f"When {target.phrase} was back on the path, {hero.id} laughed with relief. {magic.phrase.capitalize()} gave one soft glow, as if it liked the safe kind of hero work best."
    )


def tell(
    magic: MagicItem,
    target: Target,
    response: Response,
    hero_name: str = "Nova",
    hero_gender: str = "girl",
    sidekick_name: str = "Max",
    sidekick_gender: str = "boy",
    trait: str = "careful",
    guardian_type: str = "mother",
    delay: int = 0,
    hero_age: int = 6,
    sidekick_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["bold"],
        age=hero_age,
        attrs={"display_name": hero_name, "relation": relation},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type=sidekick_gender,
        label=sidekick_name,
        role="sidekick",
        traits=[trait],
        age=sidekick_age,
        attrs={"display_name": sidekick_name, "relation": relation},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_type,
        label="the parent",
        role="guardian",
    ))
    puddle = world.add(Entity(
        id="puddle",
        type="puddle",
        label="deep puddle",
        phrase="the deep puddle",
    ))
    magic_ent = world.add(Entity(
        id="magic",
        type="magic",
        label=magic.label,
        phrase=magic.phrase,
        tags=set(magic.tags),
    ))
    target_ent = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        phrase=target.phrase,
        tags=set(target.tags),
    ))

    hero.id = hero_name
    sidekick.id = sidekick_name
    guardian.id = "Parent"
    world.entities = {
        hero.id: hero,
        sidekick.id: sidekick,
        guardian.id: guardian,
        puddle.id: puddle,
        magic_ent.id: magic_ent,
        target_ent.id: target_ent,
    }

    hero.memes["bravery"] = BRAVERY_INIT
    sidekick.memes["caution"] = initial_caution(trait)
    sidekick.memes["trust"] = float(trust)

    opening(world, hero, sidekick, magic, target)
    world.para()
    surprise_glow(world, hero, sidekick, magic, target)
    warn(world, sidekick, hero, guardian, magic, target)

    averted = would_avert(relation, hero_age, sidekick_age, trait)
    if averted:
        back_down(world, hero, sidekick, guardian, target)
        world.para()
        safe_after_avert(world, hero, sidekick, guardian, target, response, magic)
        world.para()
        happy_end(world, hero, sidekick, guardian, magic)
        contained = True
        severity = 0
    else:
        defy(world, hero, sidekick)
        world.para()
        leap_in(world, hero, target, magic)
        alarm(world, sidekick, hero, guardian)
        severity = puddle_severity(target, delay)
        contained = is_contained(response, target, delay)
        world.para()
        if contained:
            rescue_success(world, guardian, response, target)
            lesson(world, guardian, hero, sidekick, magic)
            world.para()
            happy_end(world, hero, sidekick, guardian, magic)
        else:
            rescue_fail(world, guardian, response, target, magic)
            bad_end(world, hero, sidekick, target, magic)

    outcome = "averted" if averted else ("contained" if contained else "lost")
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        guardian=guardian,
        magic_cfg=magic,
        target_cfg=target,
        response=response,
        relation=relation,
        surprise=True,
        delay=delay,
        severity=severity,
        outcome=outcome,
        rescued=contained,
        jumped=not averted,
        trust=trust,
        magic_lost=world.facts.get("lost_magic", False),
    )
    return world


MAGIC_ITEMS = {
    "star_badge": MagicItem(
        id="star_badge",
        label="star badge",
        phrase="a silver star badge",
        glow="blue light",
        lesson="I can be brave without jumping first.",
        tags={"magic", "badge", "light"},
    ),
    "moon_ring": MagicItem(
        id="moon_ring",
        label="moon ring",
        phrase="a moon ring",
        glow="pearly light",
        lesson="A hero uses warnings, not wishes.",
        tags={"magic", "ring", "light"},
    ),
    "sun_stone": MagicItem(
        id="sun_stone",
        label="sun stone",
        phrase="a warm sun stone",
        glow="gold light",
        lesson="The safest plan is the strongest power.",
        tags={"magic", "stone", "light"},
    ),
}

TARGETS = {
    "toy_boat": Target(
        id="toy_boat",
        label="toy boat",
        phrase="the toy boat",
        place_text="A toy boat bobbed near the middle, turning in slow circles.",
        peril_text="the boat drifting toward the deepest middle",
        need_text="The boat spun farther away instead of coming closer.",
        drift=1,
        retrievable=True,
        tags={"boat", "puddle"},
    ),
    "cape_mask": Target(
        id="cape_mask",
        label="cape mask",
        phrase="the cape mask",
        place_text="A little cape mask had blown off a fence and plastered itself to a muddy stone.",
        peril_text="the mask stuck on a slick rock where the water suddenly dropped away",
        need_text="The mask slid from the rock and bobbed just out of reach.",
        drift=2,
        retrievable=True,
        tags={"costume", "puddle"},
    ),
    "comic_book": Target(
        id="comic_book",
        label="comic book",
        phrase="the comic book",
        place_text="A comic book lay half-open on a small patch of gravel, its bright hero on the cover staring at the sky.",
        peril_text="the comic book sagging at the edges while muddy water lapped over the paper",
        need_text="The pages soaked up water and turned heavy as soup.",
        drift=2,
        retrievable=True,
        tags={"book", "puddle"},
    ),
    "reflection": Target(
        id="reflection",
        label="golden reflection",
        phrase="the golden reflection",
        place_text="A golden shape trembled in the water, but it was only the sun peeking through the clouds.",
        peril_text="nothing solid at all, only a shine on the surface",
        need_text="There was nothing there to rescue.",
        drift=0,
        retrievable=False,
        tags={"reflection"},
    ),
}

RESPONSES = {
    "garden_rake": Response(
        id="garden_rake",
        sense=3,
        power=4,
        text="used a long garden rake from the shed to hook {target} closer and then reached the child with a steady arm",
        fail="used a long garden rake, but the mud was too slippery and the {target} slid away before the hook could catch",
        qa_text="used a long garden rake and a steady arm to bring everything back to shore",
        tags={"rake", "tool"},
    ),
    "porch_board": Response(
        id="porch_board",
        sense=3,
        power=3,
        text="laid a porch board over the edge of the puddle, crawled out along it, and pulled {target} back before the child slipped again",
        fail="laid a porch board over the edge, but it sank crooked in the mud while the {target} drifted farther away",
        qa_text="laid a board across the mud and reached the stranded thing safely",
        tags={"board", "tool"},
    ),
    "rope_loop": Response(
        id="rope_loop",
        sense=2,
        power=2,
        text="threw a rope loop for the child to hold and tugged both child and {target} back toward the grass",
        fail="threw a rope loop, but the child got out alone while the {target} slipped away into the drain",
        qa_text="used a rope loop to pull the child and the stranded thing back",
        tags={"rope", "tool"},
    ),
    "superhero_jump": Response(
        id="superhero_jump",
        sense=1,
        power=1,
        text="tried to leap in like a comic-book hero and grab {target} by hand",
        fail="jumped after the {target}, splashing mud everywhere, but only made the trouble bigger",
        qa_text="jumped in by hand",
        tags={"jump"},
    ),
}

GIRL_NAMES = ["Nova", "Lily", "Zoe", "Mia", "Ava", "Ruby", "Skye", "Nora"]
BOY_NAMES = ["Max", "Leo", "Finn", "Theo", "Eli", "Sam", "Ben", "Jack"]
TRAITS = ["careful", "cautious", "wise", "steady", "curious", "boldish"]


@dataclass
class StoryParams:
    magic: str
    target: str
    response: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    guardian: str
    trait: str
    delay: int = 0
    hero_age: int = 6
    sidekick_age: int = 4
    relation: str = "siblings"
    trust: int = 6
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        magic="star_badge",
        target="toy_boat",
        response="garden_rake",
        hero_name="Nova",
        hero_gender="girl",
        sidekick_name="Max",
        sidekick_gender="boy",
        guardian="mother",
        trait="careful",
        delay=0,
        hero_age=6,
        sidekick_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        magic="moon_ring",
        target="comic_book",
        response="porch_board",
        hero_name="Finn",
        hero_gender="boy",
        sidekick_name="Ruby",
        sidekick_gender="girl",
        guardian="father",
        trait="steady",
        delay=1,
        hero_age=7,
        sidekick_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        magic="sun_stone",
        target="cape_mask",
        response="rope_loop",
        hero_name="Mia",
        hero_gender="girl",
        sidekick_name="Zoe",
        sidekick_gender="girl",
        guardian="mother",
        trait="cautious",
        delay=2,
        hero_age=6,
        sidekick_age=5,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        magic="star_badge",
        target="toy_boat",
        response="garden_rake",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Nora",
        sidekick_gender="girl",
        guardian="father",
        trait="wise",
        delay=0,
        hero_age=5,
        sidekick_age=7,
        relation="siblings",
        trust=3,
    ),
]


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a pretend superhero story?",
            "Magic in a pretend superhero story is a special, surprising power that can glow or help reveal something. It still does not make unsafe choices safe."
        )
    ],
    "puddle": [
        (
            "Why can a deep puddle be dangerous?",
            "A deep puddle can hide slippery mud, holes, or a sudden drop. That is why children should not jump into one alone."
        )
    ],
    "badge": [
        (
            "What is a badge?",
            "A badge is a small sign or token you can pin or wear. In a superhero game, it can feel like part of a costume."
        )
    ],
    "ring": [
        (
            "What is a ring?",
            "A ring is a small band worn on a finger. In stories, people sometimes pretend a ring has magic powers."
        )
    ],
    "stone": [
        (
            "What is a stone?",
            "A stone is a small hard piece of rock. Some stories imagine a special stone can glow or hold magic."
        )
    ],
    "light": [
        (
            "What does radiate mean?",
            "Radiate means to send light or warmth outward. Something glowing can radiate softly or brightly."
        )
    ],
    "rope": [
        (
            "What is a rope good for in a rescue?",
            "A rope can help pull someone toward safety from a distance. Grown-ups use it so they do not have to step into danger right away."
        )
    ],
    "board": [
        (
            "Why can a board help near mud or water?",
            "A wide board can spread your weight and give you a steadier path. It can help a grown-up reach safely where the ground is slippery."
        )
    ],
    "rake": [
        (
            "How can a long rake help get something back?",
            "A long rake lets a grown-up hook or pull something closer without wading into the water. The long handle keeps the helper on safer ground."
        )
    ],
    "book": [
        (
            "Why do books get ruined by puddles?",
            "Books are made of paper, and paper soaks up water quickly. Wet pages wrinkle, tear, and can fall apart."
        )
    ],
    "costume": [
        (
            "Why is a superhero costume just pretend?",
            "A superhero costume can help a game feel exciting, but it does not give a real person flying or super strength. Real safety rules still matter."
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "puddle", "badge", "ring", "stone", "light", "rope", "board", "rake", "book", "costume"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for magic_id in MAGIC_ITEMS:
        for target_id, target in TARGETS.items():
            if target_at_risk(target):
                combos.append((magic_id, target_id))
    return combos


def explain_target_rejection(target: Target) -> str:
    return (
        f"(No story: {target.phrase} is not something real to rescue from a deep puddle. "
        f"The mission needs a stranded object, not a reflection.)"
    )


def explain_response_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of these safer choices: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.hero_age, params.sidekick_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "lost"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    magic = f["magic_cfg"]
    target = f["target_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a superhero-style story for a 3-to-5-year-old set beside a deep puddle. '
        f'Include the words "doze" and "radiate", a magic surprise, and {magic.phrase}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a story where {hero.label} wants to rescue {target.phrase}, but {sidekick.label}, the older companion, stops the risky leap and a grown-up helps safely.",
            f"Write a gentle superhero tale where a glowing magic object warns children away from danger instead of pushing them into it.",
        ]
    if outcome == "lost":
        return [
            base,
            f"Tell a superhero story where {hero.label} jumps into a deep puddle to save {target.phrase}, but the rescue goes badly and the ending is sad.",
            f"Write a cautionary story with a bad ending: a magic surprise happens, but pretending to be a hero does not stop the deep puddle from taking something away.",
        ]
    return [
        base,
        f"Tell a superhero story where {hero.label} leaps toward {target.phrase}, the magic item glows with surprise, and a grown-up uses a smart tool to help.",
        f"Write a simple story that teaches that real heroes listen when danger shows itself, even in the middle of a pretend mission.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    guardian = f["guardian"]
    magic = f["magic_cfg"]
    target = f["target_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {sidekick.label}, and {hero.label}'s {guardian.label_word} beside a deep puddle. They were playing superheroes when the problem began."
        ),
        (
            "What was the surprise in the story?",
            f"The surprise was that {magic.phrase} began to radiate {magic.glow}. The sudden glow showed that the puddle was more dangerous than it first looked."
        ),
        (
            f"Why did {sidekick.label} tell {hero.label} to wait?",
            f"{sidekick.label} could see the deep puddle was slippery and risky. The magic glow acted like a warning, so waiting was safer than jumping."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {hero.label} do after the warning?",
                f"{hero.label} backed down and called a grown-up instead of leaping in. That choice kept the mission brave but safe."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely. A grown-up helped retrieve {target.phrase}, and the children kept playing superhero on dry ground."
            )
        )
    elif outcome == "contained":
        qa.append(
            (
                f"How did {guardian.label_word} help?",
                f"{guardian.label_word.capitalize()} {response.qa_text.replace('{target}', target.label)}. The grown-up's method was strong enough for the deep puddle, so both the child and the stranded thing came back safely."
            )
        )
        qa.append(
            (
                f"What did {hero.label} learn?",
                f"{hero.label} learned that magic and costumes do not replace careful choices. The glow was useful because it warned about danger, not because it made the jump safe."
            )
        )
    else:
        qa.append(
            (
                "What made the ending bad?",
                f"The rescue came too late or was too weak for the deep puddle. {target.phrase} and the magic object were lost, so the game ended in sadness instead of cheers."
            )
        )
        qa.append(
            (
                f"Was {hero.label} safe even though the ending was bad?",
                f"Yes. {hero.label} was pulled out safely, but the important things in the puddle were gone. That is why the ending feels bad even though the child got home."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["magic_cfg"].tags) | set(f["target_cfg"].tags) | set(f["response"].tags) | {"puddle"}
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(M, T) :- magic(M), target(T), retrievable(T).
sensible(R) :- response(R), sense(R, S), sense_min(MN), S >= MN.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

sidekick_older :- relation(siblings), hero_age(HA), sidekick_age(SA), SA > HA.
bonus(3)       :- sidekick_older.
bonus(0)       :- not sidekick_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- sidekick_older, authority(A), bravery_init(BR), A > BR.

severity(1 + Df + Dl) :- chosen_target(T), drift(T, Df), delay(Dl).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(lost) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for magic_id in MAGIC_ITEMS:
        lines.append(asp.fact("magic", magic_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.retrievable:
            lines.append(asp.fact("retrievable", target_id))
        lines.append(asp.fact("drift", target_id, target.drift))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    return sorted(atom[0] for atom in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("sidekick_age", params.sidekick_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sense = set(asp_sensible())
    p_sense = {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a superhero game, a magic surprise, and a deep puddle."
    )
    ap.add_argument("--magic", choices=sorted(MAGIC_ITEMS))
    ap.add_argument("--target", choices=sorted(TARGETS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [name for name in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].retrievable:
        raise StoryError(explain_target_rejection(TARGETS[args.target]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.magic is None or combo[0] == args.magic)
        and (args.target is None or combo[1] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    magic_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_name, hero_gender = _pick_child(rng)
    sidekick_name, sidekick_gender = _pick_child(rng, avoid=hero_name)
    guardian = args.guardian or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    hero_age, sidekick_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        magic=magic_id,
        target=target_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        guardian=guardian,
        trait=trait,
        delay=delay,
        hero_age=hero_age,
        sidekick_age=sidekick_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.magic not in MAGIC_ITEMS:
        raise StoryError(f"Unknown magic item: {params.magic}")
    if params.target not in TARGETS:
        raise StoryError(f"Unknown target: {params.target}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if not TARGETS[params.target].retrievable:
        raise StoryError(explain_target_rejection(TARGETS[params.target]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))

    world = tell(
        magic=MAGIC_ITEMS[params.magic],
        target=TARGETS[params.target],
        response=RESPONSES[params.response],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        trait=params.trait,
        guardian_type=params.guardian,
        delay=params.delay,
        hero_age=params.hero_age,
        sidekick_age=params.sidekick_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (magic, target) combos:\n")
        for magic_id, target_id in combos:
            print(f"  {magic_id:12} {target_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            params = sample.params
            header = (
                f"### {params.hero_name} & {params.sidekick_name}: {params.magic} / "
                f"{params.target} / {params.response} ({outcome_of(params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
