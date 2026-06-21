#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/weenie_shawl_mhiabbi_quest_comedy.py
===============================================================

A standalone story world for a silly quest-comedy: a child's tiny dog named
Weenie chases after a runaway shawl that is needed for a family mhiabbi feast.
The shawl blows away, gets stuck somewhere awkward, and the child must choose a
sensible way to get it back. The world model tracks physical state
(distance, snagged/free, clean/muddy) and emotional state (worry, hope, pride),
then renders a complete story with a beginning, quest middle, turning point, and
ending image that proves what changed.

The domain is deliberately small and constrained. Not every tool fits every
snagged place:
- a ladder helps with high places,
- a snack lure helps with a greedy goat,
- a stick helps with low branches or fences.

Unreasonable explicit choices are rejected with a StoryError rather than turned
into weak stories.

Run it
------
    python storyworlds/worlds/gpt-5.4/weenie_shawl_mhiabbi_quest_comedy.py
    python storyworlds/worlds/gpt-5.4/weenie_shawl_mhiabbi_quest_comedy.py --snag goat_horns --tool ladder
    python storyworlds/worlds/gpt-5.4/weenie_shawl_mhiabbi_quest_comedy.py --snag roof --tool stick
    python storyworlds/worlds/gpt-5.4/weenie_shawl_mhiabbi_quest_comedy.py --all
    python storyworlds/worlds/gpt-5.4/weenie_shawl_mhiabbi_quest_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/weenie_shawl_mhiabbi_quest_comedy.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing | animal
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Errand:
    id: str
    feast: str
    dish: str
    reason: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Snag:
    id: str
    label: str
    place: str
    height: str
    keeper: str
    chase_line: str
    recovery_need: str
    clean_risk: int
    high: bool = False
    animal_guard: bool = False
    muddy: bool = False
    reachable_with_stick: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works_on_high: bool = False
    works_on_animal: bool = False
    works_on_low: bool = False
    keeps_clean: bool = True
    action: str = ""
    qa_action: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    style: str
    gives_bonus: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return World(
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_fuss(world: World) -> list[str]:
    shawl = world.get("shawl")
    hero = world.get("hero")
    dog = world.get("weenie")
    out: list[str] = []
    if shawl.meters["snagged"] >= THRESHOLD and ("fuss",) not in world.fired:
        world.fired.add(("fuss",))
        hero.memes["worry"] += 1
        dog.memes["alert"] += 1
        out.append("__snagged__")
    return out


def _r_recovered(world: World) -> list[str]:
    shawl = world.get("shawl")
    hero = world.get("hero")
    grandma = world.get("grandma")
    out: list[str] = []
    if shawl.meters["recovered"] >= THRESHOLD and ("recovered",) not in world.fired:
        world.fired.add(("recovered",))
        hero.memes["pride"] += 1
        hero.memes["worry"] = 0.0
        grandma.memes["relief"] += 1
        out.append("__recovered__")
    return out


CAUSAL_RULES = [
    Rule(name="fuss", tag="emotion", apply=_r_fuss),
    Rule(name="recovered", tag="emotion", apply=_r_recovered),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def tool_fits(tool: Tool, snag: Snag) -> bool:
    if snag.high and tool.works_on_high:
        return True
    if snag.animal_guard and tool.works_on_animal:
        return True
    if not snag.high and not snag.animal_guard and tool.works_on_low:
        return True
    return False


def happy_with(tool: Tool, snag: Snag) -> bool:
    return tool_fits(tool, snag) and (tool.keeps_clean or snag.clean_risk <= 1)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for errand_id in ERRANDS:
        for snag_id, snag in SNAGS.items():
            for tool_id, tool in TOOLS.items():
                if not tool_fits(tool, snag):
                    continue
                for helper_id in HELPERS:
                    combos.append((errand_id, snag_id, tool_id, helper_id))
    return combos


def explain_rejection(tool: Tool, snag: Snag) -> str:
    if snag.high:
        return (
            f"(No story: {snag.label} is too high for {tool.phrase}. "
            f"Pick something that can reach up safely, like a ladder.)"
        )
    if snag.animal_guard:
        return (
            f"(No story: {snag.label} is guarded by a hungry goat, and {tool.phrase} "
            f"won't persuade it to let go. Pick a snack lure.)"
        )
    return (
        f"(No story: {tool.phrase.capitalize()} is the wrong kind of tool for {snag.label}. "
        f"Pick something that can hook or nudge the shawl free.)"
    )


def outcome_of_params(params: "StoryParams") -> str:
    tool = TOOLS[params.tool]
    snag = SNAGS[params.snag]
    return "clean_return" if happy_with(tool, snag) else "messy_return"


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def setup_home(world: World, errand: Errand, hero: Entity, grandma: Entity, dog: Entity) -> None:
    hero.memes["joy"] += 1
    dog.memes["joy"] += 1
    world.say(
        f"On the morning of {errand.feast}, {hero.id} was helping {grandma.label_word} in the yard. "
        f"{errand.opening}"
    )
    world.say(
        f"At {hero.id}'s feet trotted Weenie, a sausage-shaped little dog with busy paws and a nose "
        f"that believed every breeze was a message."
    )
    world.say(
        f"{grandma.label_word.capitalize()} wore her best shawl because {errand.reason}. "
        f'"After we finish, we will carry out the {errand.dish}," {grandma.pronoun()} said.'
    )


def blowaway(world: World, snag: Snag, hero: Entity, grandma: Entity) -> None:
    shawl = world.get("shawl")
    shawl.meters["airborne"] += 1
    shawl.meters["snagged"] += 1
    shawl.attrs["snag"] = snag.id
    world.facts["snagged_at"] = snag.place
    propagate(world, narrate=False)
    world.say(
        f"Then a rude puff of wind scooped up the shawl and sent it sailing over the path. "
        f"{snag.chase_line}"
    )
    world.say(
        f'"My shawl!" cried {grandma.label_word}. "And the mhiabbi feast is not the same without it."'
    )


def volunteer(world: World, errand: Errand, hero: Entity, helper: Helper) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f'{hero.id} puffed up with quest-important feelings. "{errand.id.capitalize()} quest!" '
        f'{hero.pronoun()} declared. "{helper.style.capitalize()}, Weenie!"'
    )


def set_out(world: World, snag: Snag, tool: Tool, helper: Helper, hero: Entity, dog: Entity) -> None:
    hero.meters["distance"] += 1
    dog.meters["distance"] += 1
    hero.attrs["helper_style"] = helper.style
    world.say(
        f"So off they went: {hero.id}, Weenie, and {helper.phrase}. "
        f"{helper.label.capitalize()} {helper.gives_bonus} while {hero.id} carried {tool.phrase}."
    )
    world.say(
        f"The quest led past the bakery, across the puddle stones, and toward {snag.place}, "
        f"where the shawl waited in a very silly sort of trouble."
    )


def comic_obstacle(world: World, snag: Snag, hero: Entity, dog: Entity) -> None:
    hero.memes["worry"] += 1
    if snag.animal_guard:
        world.say(
            f"There it was: the shawl looped over {snag.label}, while a goat chewed one fringe with dreamy eyes. "
            f"Weenie barked so hard his back feet slid backward."
        )
    elif snag.high:
        world.say(
            f"There it was: the shawl flapped from {snag.label}, high enough to tease and low enough to brag. "
            f"Weenie jumped twice, rose nowhere, and looked offended by gravity."
        )
    else:
        world.say(
            f"There it was: the shawl caught on {snag.label}. Each little gust made it wave as if it were enjoying "
            f"the quest more than anybody else."
        )


def recover(world: World, snag: Snag, tool: Tool, helper: Helper, hero: Entity, dog: Entity) -> None:
    shawl = world.get("shawl")
    hero.memes["hope"] += 1
    if snag.animal_guard:
        world.say(
            f'{helper.label.capitalize()} whispered, "Slowly now," and {hero.id} held out {tool.phrase}. '
            f'The goat forgot the fringe, followed the snack, and Weenie danced in a very tiny circle.'
        )
    elif snag.high:
        world.say(
            f'{helper.label.capitalize()} steadied the ladder while {hero.id} climbed step by step. '
            f'With one careful reach, {hero.pronoun()} {tool.action}.'
        )
    else:
        world.say(
            f'{helper.label.capitalize()} pointed from below while {hero.id} {tool.action}. '
            f'Weenie added three encouraging sneezes.'
        )
    shawl.meters["snagged"] = 0.0
    shawl.meters["recovered"] += 1
    if not tool.keeps_clean and snag.clean_risk >= 2:
        shawl.meters["muddy"] += 1
    world.facts["recovery_method"] = tool.qa_action
    propagate(world, narrate=False)


def return_home(world: World, errand: Errand, snag: Snag, hero: Entity, grandma: Entity) -> None:
    shawl = world.get("shawl")
    hero.meters["distance"] += 1
    if shawl.meters["muddy"] >= THRESHOLD:
        world.say(
            f"They marched home in triumph, though the shawl now wore a strip of mud like an extra eyebrow. "
            f"{grandma.label_word.capitalize()} laughed when {hero.id} handed it back."
        )
        world.say(
            f'"Well," {grandma.pronoun()} said, shaking it out, "it looks as if the quest had breakfast with a puddle."'
        )
    else:
        world.say(
            f"They hurried back with the rescued shawl folded over {hero.id}'s arms. "
            f"{grandma.label_word.capitalize()} put it on at once and spun once just to make the fringe clap."
        )
    if shawl.meters["muddy"] >= THRESHOLD:
        world.say(
            f'"A quick wash, a warm line in the sun, and it will still be ready for {errand.feast}," '
            f'{grandma.pronoun()} said. Weenie sneezed on the fringe as if agreeing.'
        )
    else:
        world.say(
            f'Soon the shawl was back where it belonged, and the yard smelled of {errand.dish}. '
            f'The quest had ended with both dignity and crumbs.'
        )


def feast_ending(world: World, errand: Errand, hero: Entity, grandma: Entity, helper: Helper) -> None:
    shawl = world.get("shawl")
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    if shawl.meters["muddy"] >= THRESHOLD:
        world.say(
            f"By evening the clean shawl was fluttering on the line no more. It rested on {grandma.label_word}'s shoulders "
            f"while everybody ate {errand.dish}, and Weenie sat beneath the table hoping a hero's reward might fall."
        )
    else:
        world.say(
            f"By evening the whole family sat down to the {errand.feast}. The mhiabbi smelled rich and warm, "
            f"the shawl glowed on {grandma.label_word}'s shoulders, and Weenie received a tiny crust for loyal barking."
        )
    world.say(
        f'When someone asked who had saved the day, {hero.id} bowed, {helper.label} bowed even lower, and '
        f'Weenie rolled onto his back as if that were also part of the quest.'
    )
    world.say(errand.ending)


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    errand: Errand,
    snag: Snag,
    tool: Tool,
    helper: Helper,
    *,
    hero_name: str = "Tilda",
    hero_gender: str = "girl",
    grandma_type: str = "grandmother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    grandma = world.add(
        Entity(id="grandma", kind="character", type=grandma_type, label="the grandmother", role="grandma")
    )
    dog = world.add(
        Entity(
            id="weenie",
            kind="animal",
            type="dog",
            label="Weenie",
            role="dog",
            traits=["small", "bold"],
            attrs={"shape": "long"},
        )
    )
    shawl = world.add(
        Entity(
            id="shawl",
            kind="thing",
            type="shawl",
            label="shawl",
            role="prize",
            attrs={"owner": "grandma"},
        )
    )

    world.facts.update(
        errand=errand,
        snag=snag,
        tool=tool,
        helper=helper,
        hero=hero,
        grandma=grandma,
        dog=dog,
        shawl=shawl,
    )

    setup_home(world, errand, hero, grandma, dog)
    world.para()
    blowaway(world, snag, hero, grandma)
    volunteer(world, errand, hero, helper)
    world.para()
    set_out(world, snag, tool, helper, hero, dog)
    comic_obstacle(world, snag, hero, dog)
    recover(world, snag, tool, helper, hero, dog)
    world.para()
    return_home(world, errand, snag, hero, grandma)
    feast_ending(world, errand, hero, grandma, helper)

    world.facts.update(
        outcome="messy_return" if shawl.meters["muddy"] >= THRESHOLD else "clean_return",
        rescued=shawl.meters["recovered"] >= THRESHOLD,
        muddy=shawl.meters["muddy"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ERRANDS = {
    "feast": Errand(
        id="feast",
        feast="the Noon Mhiabbi Feast",
        dish="steaming bowls of mhiabbi stew and warm rolls",
        reason="the shawl was her lucky feast shawl",
        opening="Today was the Noon Mhiabbi Feast, which meant pots bubbling, spoons clinking, and everybody trying not to taste too early.",
        ending="The whole family agreed that quests are easier with courage, laughter, and one absurdly determined little weenie dog.",
        tags={"mhiabbi", "feast"},
    ),
    "picnic": Errand(
        id="picnic",
        feast="the Mhiabbi Picnic",
        dish="a basket of mhiabbi buns with onion butter",
        reason="she always wore it when she carried the picnic basket",
        opening="It was Mhiabbi Picnic day, and the garden path already smelled buttery and happy.",
        ending="After that, nobody in the family could say the word mhiabbi without also smiling at Weenie.",
        tags={"mhiabbi", "picnic"},
    ),
    "parade": Errand(
        id="parade",
        feast="the Grand Mhiabbi Parade",
        dish="mhiabbi cakes dusted with sugar",
        reason="she planned to lead the parade table with it fluttering behind her",
        opening="The Grand Mhiabbi Parade was only an hour away, so every ribbon in the neighborhood seemed to be practicing.",
        ending="From then on, the family said that even a runaway shawl cannot outwit a good quest for long.",
        tags={"mhiabbi", "parade"},
    ),
}

SNAGS = {
    "pear_tree": Snag(
        id="pear_tree",
        label="a pear tree branch",
        place="the old pear tree by the wall",
        height="high",
        keeper="wind",
        chase_line="Up it went, then down, then sideways, until it landed in a pear tree branch and fluttered there like a flag that had forgotten its country.",
        recovery_need="reach",
        clean_risk=0,
        high=True,
        reachable_with_stick=False,
        tags={"tree", "high_place"},
    ),
    "goat_horns": Snag(
        id="goat_horns",
        label="a goat's curly horns",
        place="Mrs. Pepple's goat pen",
        height="low",
        keeper="goat",
        chase_line="It drifted right into Mrs. Pepple's goat pen, where a plump goat blinked once and somehow ended up wearing the shawl on its horns.",
        recovery_need="lure",
        clean_risk=1,
        animal_guard=True,
        tags={"goat", "animal"},
    ),
    "fence_post": Snag(
        id="fence_post",
        label="a splintery fence post",
        place="the fence beside the duck pond",
        height="low",
        keeper="splinters",
        chase_line="One naughty swirl later, it snagged on a splintery fence post beside the duck pond, where it flapped and flapped like it was practicing speeches.",
        recovery_need="hook",
        clean_risk=0,
        reachable_with_stick=True,
        tags={"fence", "low_place"},
    ),
    "puddle_cart": Snag(
        id="puddle_cart",
        label="the wheel of an abandoned handcart in a puddle",
        place="the muddy lane behind the bakery",
        height="low",
        keeper="mud",
        chase_line="The shawl dropped at last onto the wheel of an abandoned handcart in a puddle, where the mud waited below with mean little patience.",
        recovery_need="hook",
        clean_risk=2,
        muddy=True,
        reachable_with_stick=True,
        tags={"mud", "low_place"},
    ),
    "roof": Snag(
        id="roof",
        label="the low bakery roof",
        place="the bakery roof",
        height="high",
        keeper="height",
        chase_line="It skimmed over two chimneys and sat down on the bakery roof as if it had paid rent.",
        recovery_need="reach",
        clean_risk=0,
        high=True,
        tags={"roof", "high_place"},
    ),
}

TOOLS = {
    "ladder": Tool(
        id="ladder",
        label="ladder",
        phrase="a tall ladder",
        works_on_high=True,
        keeps_clean=True,
        action="lifted the shawl free from the nail of bark and tucked it under one arm",
        qa_action="used a ladder to reach the shawl safely",
        tags={"ladder"},
    ),
    "snack_lure": Tool(
        id="snack_lure",
        label="snack lure",
        phrase="a paper cone of turnip crisps",
        works_on_animal=True,
        keeps_clean=True,
        action="",
        qa_action="lured the goat away with a snack so the shawl could be slipped free",
        tags={"snack", "goat"},
    ),
    "stick": Tool(
        id="stick",
        label="hooked stick",
        phrase="a long hooked stick",
        works_on_low=True,
        keeps_clean=True,
        action="nudged and hooked the fringe until the shawl slipped loose",
        qa_action="used a hooked stick to nudge the shawl free",
        tags={"stick"},
    ),
    "bare_hands": Tool(
        id="bare_hands",
        label="bare hands",
        phrase="bare hands",
        works_on_low=True,
        keeps_clean=False,
        action="leaned down and snatched the shawl up before the puddle could gulp it twice",
        qa_action="grabbed the shawl by hand",
        tags={"hands"},
    ),
}

HELPERS = {
    "baker": Helper(
        id="baker",
        label="the baker",
        phrase="the floury baker from the corner shop",
        style="marching with crumbs",
        gives_bonus="kept saying this was the most exciting thing to happen to bread all morning",
        tags={"baker"},
    ),
    "mail_carrier": Helper(
        id="mail_carrier",
        label="the mail carrier",
        phrase="the mail carrier with jangling keys",
        style="saluting at puddles",
        gives_bonus="insisted that every great quest deserved proper announcements",
        tags={"mail"},
    ),
    "cousin": Helper(
        id="cousin",
        label="cousin Pip",
        phrase="cousin Pip in a crooked cap",
        style="tiptoeing dramatically",
        gives_bonus="whispered each clue as if the shrubs were listening",
        tags={"cousin"},
    ),
}

GIRL_NAMES = ["Tilda", "Mina", "Poppy", "Nell", "Asha", "Dora", "Lina", "Ruth"]
BOY_NAMES = ["Otis", "Milo", "Ned", "Jasper", "Hugo", "Bram", "Eli", "Theo"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    errand: str = "feast"
    snag: str = "pear_tree"
    tool: str = "ladder"
    helper: str = "baker"
    hero_name: str = "Tilda"
    hero_gender: str = "girl"
    grandma_type: str = "grandmother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "shawl": [
        (
            "What is a shawl?",
            "A shawl is a soft cloth people wear around their shoulders for warmth or decoration."
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps you reach something that is high up. A grown-up should steady it so climbing stays safe."
        )
    ],
    "goat": [
        (
            "Why might a goat follow a snack?",
            "Goats are curious animals and often come over when they smell food. A snack can distract one from whatever it was nosing before."
        )
    ],
    "mud": [
        (
            "Why does mud make cloth dirty?",
            "Mud is wet earth, so it sticks to cloth and leaves brown marks behind. That is why people try to keep nice clothes and shawls out of puddles."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip with a clear goal, like finding something lost or helping someone. In stories, a quest usually has a problem, a plan, and a happy return."
        )
    ],
    "mhiabbi": [
        (
            "What is mhiabbi in this story world?",
            "Mhiabbi is the family's funny special feast food and celebration word. It makes the meal sound extra important and a little bit silly."
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "shawl", "ladder", "goat", "mud", "mhiabbi"]


def generation_prompts(world: World) -> list[str]:
    errand = world.facts["errand"]
    snag = world.facts["snag"]
    tool = world.facts["tool"]
    helper = world.facts["helper"]
    hero = world.facts["hero"]
    return [
        f'Write a short Comedy quest for a 3-to-5-year-old that includes the words "weenie", "shawl", and "mhiabbi".',
        f"Tell a silly quest story where {hero.label} and a tiny dog named Weenie chase after a runaway shawl before {errand.feast}.",
        f"Write a gentle comic adventure where a shawl blows to {snag.place}, {helper.label} helps, and the shawl is recovered with {tool.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    errand = world.facts["errand"]
    snag = world.facts["snag"]
    tool = world.facts["tool"]
    helper = world.facts["helper"]
    hero = world.facts["hero"]
    grandma = world.facts["grandma"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, {grandma.label_word}, and a tiny dog named Weenie. They are trying to get {grandma.label_word}'s shawl back."
        ),
        (
            "Why did the shawl matter so much?",
            f"The shawl mattered because it was {grandma.label_word}'s special shawl for {errand.feast}. She wanted it for the meal and the celebration, so losing it made the quest feel urgent."
        ),
        (
            "Where did the shawl go?",
            f"The wind carried the shawl to {snag.place}. It ended up caught on {snag.label}, which turned a quiet morning into a silly chase."
        ),
        (
            "How did the quest turn funny instead of scary?",
            f"The trouble stayed funny because Weenie kept acting brave in a small, wiggly way, and the helper treated the search like an adventure. The silly barking, puddles, and fuss made the problem feel comic instead of frightening."
        ),
    ]
    if world.facts.get("rescued"):
        extra = "The shawl stayed clean." if not world.facts.get("muddy") else "The shawl got muddy, but they still saved it and brought it home."
        qa.append(
            (
                "How did they get the shawl back?",
                f"They got it back because {hero.label} {world.facts['recovery_method']}. {extra}"
            )
        )
    if world.facts.get("muddy"):
        qa.append(
            (
                "Why was the shawl dirty when it came home?",
                f"It came home dirty because it had been stuck near mud and was grabbed in a messier way. Even so, {grandma.label_word} laughed and cleaned it instead of scolding anyone."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"The shawl came home clean, and the family could enjoy {errand.dish}. The ending image shows that the quest really worked because {grandma.label_word} was wearing the shawl again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"quest", "shawl", "mhiabbi"}
    snag = world.facts["snag"]
    tool = world.facts["tool"]
    if snag.animal_guard:
        tags.add("goat")
    if snag.muddy or world.facts.get("muddy"):
        tags.add("mud")
    if tool.id == "ladder":
        tags.add("ladder")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(E,S,T,H) :- errand(E), snag(S), tool(T), helper(H), fits(T,S).

fits(T,S) :- high(S), tool_high(T).
fits(T,S) :- animal(S), tool_animal(T).
fits(T,S) :- low_plain(S), tool_low(T).

low_plain(S) :- snag(S), not high(S), not animal(S).

clean_return :- chosen_snag(S), chosen_tool(T), fits(T,S), keeps_clean(T).
clean_return :- chosen_snag(S), chosen_tool(T), fits(T,S), clean_risk(S,R), R <= 1.
messy_return :- chosen_snag(S), chosen_tool(T), fits(T,S), not clean_return.

outcome(clean_return) :- clean_return.
outcome(messy_return) :- messy_return.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for eid in ERRANDS:
        lines.append(asp.fact("errand", eid))
    for sid, snag in SNAGS.items():
        lines.append(asp.fact("snag", sid))
        lines.append(asp.fact("clean_risk", sid, snag.clean_risk))
        if snag.high:
            lines.append(asp.fact("high", sid))
        if snag.animal_guard:
            lines.append(asp.fact("animal", sid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.works_on_high:
            lines.append(asp.fact("tool_high", tid))
        if tool.works_on_animal:
            lines.append(asp.fact("tool_animal", tid))
        if tool.works_on_low:
            lines.append(asp.fact("tool_low", tid))
        if tool.keeps_clean:
            lines.append(asp.fact("keeps_clean", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_snag", params.snag),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of_params(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0] if cases else CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:  # pragma: no cover - verify guard
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A silly quest-comedy about Weenie, a runaway shawl, and a mhiabbi feast."
    )
    ap.add_argument("--errand", choices=sorted(ERRANDS))
    ap.add_argument("--snag", choices=sorted(SNAGS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--grandma-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snag and args.tool:
        snag = SNAGS[args.snag]
        tool = TOOLS[args.tool]
        if not tool_fits(tool, snag):
            raise StoryError(explain_rejection(tool, snag))

    combos = [
        combo for combo in valid_combos()
        if (args.errand is None or combo[0] == args.errand)
        and (args.snag is None or combo[1] == args.snag)
        and (args.tool is None or combo[2] == args.tool)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    errand_id, snag_id, tool_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    grandma_type = args.grandma_type or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        errand=errand_id,
        snag=snag_id,
        tool=tool_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        grandma_type=grandma_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.errand not in ERRANDS:
        raise StoryError(f"(Unknown errand: {params.errand})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    snag = SNAGS[params.snag]
    tool = TOOLS[params.tool]
    if not tool_fits(tool, snag):
        raise StoryError(explain_rejection(tool, snag))

    world = tell(
        ERRANDS[params.errand],
        snag,
        tool,
        HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        grandma_type=params.grandma_type,
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


CURATED = [
    StoryParams(
        errand="feast",
        snag="pear_tree",
        tool="ladder",
        helper="baker",
        hero_name="Tilda",
        hero_gender="girl",
        grandma_type="grandmother",
    ),
    StoryParams(
        errand="picnic",
        snag="goat_horns",
        tool="snack_lure",
        helper="cousin",
        hero_name="Otis",
        hero_gender="boy",
        grandma_type="grandmother",
    ),
    StoryParams(
        errand="parade",
        snag="fence_post",
        tool="stick",
        helper="mail_carrier",
        hero_name="Mina",
        hero_gender="girl",
        grandma_type="grandfather",
    ),
    StoryParams(
        errand="feast",
        snag="puddle_cart",
        tool="bare_hands",
        helper="baker",
        hero_name="Ned",
        hero_gender="boy",
        grandma_type="grandmother",
    ),
    StoryParams(
        errand="picnic",
        snag="roof",
        tool="ladder",
        helper="mail_carrier",
        hero_name="Poppy",
        hero_gender="girl",
        grandma_type="grandfather",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (errand, snag, tool, helper) combos:\n")
        for errand, snag, tool, helper in combos:
            print(f"  {errand:7} {snag:12} {tool:10} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
        for i, sample in enumerate(samples):
            sample.params.seed = base_seed + i
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
            header = f"### {p.hero_name}: {p.errand}, {p.snag}, {p.tool} ({outcome_of_params(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
