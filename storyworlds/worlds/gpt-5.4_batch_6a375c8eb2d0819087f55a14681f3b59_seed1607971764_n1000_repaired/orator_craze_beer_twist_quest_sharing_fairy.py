#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/orator_craze_beer_twist_quest_sharing_fairy.py
============================================================================

A standalone storyworld for a small fairy-tale domain:

A village fair begins with a sweet fizzy beer for everyone, but an eager orator
whips the crowd into a craze and the keg runs low. A child goes on a quest to a
fairy spring, helped only after sharing kindly with a creature of the road.
Then comes the twist: the spring does not answer greedy asking at all. It fills
the village keg again only when the first new cup is given away.

This world models:
- a festive beginning,
- a shortage caused by a craze,
- a quest with a road obstacle,
- sharing that changes emotional and physical state,
- and a fairy-tale ending image that proves what changed.

Run it
------
python storyworlds/worlds/gpt-5.4/orator_craze_beer_twist_quest_sharing_fairy.py
python storyworlds/worlds/gpt-5.4/orator_craze_beer_twist_quest_sharing_fairy.py --festival blossom --beer ginger_beer
python storyworlds/worlds/gpt-5.4/orator_craze_beer_twist_quest_sharing_fairy.py --helper otter --obstacle bramble
python storyworlds/worlds/gpt-5.4/orator_craze_beer_twist_quest_sharing_fairy.py --all
python storyworlds/worlds/gpt-5.4/orator_craze_beer_twist_quest_sharing_fairy.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/orator_craze_beer_twist_quest_sharing_fairy.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Festival:
    id: str
    village: str
    fair: str
    decorations: str
    sendoff: str
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
class BeerKind:
    id: str
    label: str
    phrase: str
    taste: str
    foam: str
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
class OratorKind:
    id: str
    label: str
    title: str
    line: str
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
class HelperKind:
    id: str
    label: str
    kind: str
    likes: str
    gift_line: str
    aid_line: str
    solves: str
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
class Obstacle:
    id: str
    label: str
    path: str
    danger: str
    solved_by: str
    solved_text: str
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
class Gift:
    id: str
    label: str
    phrase: str
    suits: str
    share_text: str
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


def _r_craze_empties_keg(world: World) -> list[str]:
    hero = world.get("hero")
    keg = world.get("keg")
    crowd = world.get("crowd")
    out: list[str] = []
    if crowd.memes["craze"] < THRESHOLD:
        return out
    sig = ("craze_empties",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keg.meters["low"] += 1
    crowd.meters["thirst"] += 1
    hero.memes["worry"] += 1
    out.append("__low_keg__")
    return out


def _r_shared_gift_builds_trust(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    out: list[str] = []
    if hero.meters["gift_shared"] < THRESHOLD:
        return out
    sig = ("trust_after_share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["trust"] += 1
    hero.memes["kindness"] += 1
    hero.memes["hope"] += 1
    out.append("__trust__")
    return out


def _r_trusted_helper_clears_obstacle(world: World) -> list[str]:
    helper = world.get("helper")
    road = world.get("road")
    out: list[str] = []
    if helper.memes["trust"] < THRESHOLD:
        return out
    if road.meters["blocked"] < THRESHOLD:
        return out
    sig = ("clear_road",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    road.meters["blocked"] = 0.0
    road.meters["crossed"] += 1
    world.get("hero").memes["hope"] += 1
    out.append("__crossed__")
    return out


def _r_sharing_opens_spring(world: World) -> list[str]:
    hero = world.get("hero")
    spring = world.get("spring")
    out: list[str] = []
    if hero.memes["shares_first_cup"] < THRESHOLD:
        return out
    sig = ("spring_answers",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    spring.meters["blessing"] += 1
    world.get("keg").meters["full"] += 1
    world.get("keg").meters["low"] = 0.0
    world.get("crowd").memes["craze"] = 0.0
    world.get("crowd").memes["gratitude"] += 1
    hero.memes["lesson"] += 1
    out.append("__blessing__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="craze_empties_keg", tag="physical", apply=_r_craze_empties_keg),
    Rule(name="shared_gift_builds_trust", tag="social", apply=_r_shared_gift_builds_trust),
    Rule(name="trusted_helper_clears_obstacle", tag="physical", apply=_r_trusted_helper_clears_obstacle),
    Rule(name="sharing_opens_spring", tag="magic", apply=_r_sharing_opens_spring),
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
        for s in produced:
            world.say(s)
    return produced


FESTIVALS = {
    "blossom": Festival(
        id="blossom",
        village="Thimblewick",
        fair="Blossom Bell Fair",
        decorations="apple boughs were tied with ribbons, and lanterns shaped like pears swung over the square",
        sendoff="the square smelled of petals and warm bread",
        tags={"fair", "village", "festival"},
    ),
    "moonlantern": Festival(
        id="moonlantern",
        village="Mossmere",
        fair="Moon-Lantern Market",
        decorations="silver paper moons fluttered from every stall, and little lamps winked under the eaves",
        sendoff="the cobbles shone softly under the lantern light",
        tags={"fair", "lantern", "festival"},
    ),
    "dewfeast": Festival(
        id="dewfeast",
        village="Fernhollow",
        fair="Dewfeast Day",
        decorations="garlands of clover lay on the well, and bright pennants skipped in the morning breeze",
        sendoff="the grass by the square glittered like green velvet",
        tags={"fair", "festival", "village"},
    ),
}

BEERS = {
    "berry_beer": BeerKind(
        id="berry_beer",
        label="berry beer",
        phrase="a cask of berry beer",
        taste="sweet as blackberries and cool as cellar stone",
        foam="purple foam",
        tags={"beer", "drink", "berries"},
    ),
    "ginger_beer": BeerKind(
        id="ginger_beer",
        label="ginger beer",
        phrase="a barrel of ginger beer",
        taste="bright and fizzy, with a tickle at the nose",
        foam="golden foam",
        tags={"beer", "drink", "ginger"},
    ),
    "apple_beer": BeerKind(
        id="apple_beer",
        label="apple beer",
        phrase="a round oak keg of apple beer",
        taste="sparkling and sweet with the smell of autumn apples",
        foam="pale foam",
        tags={"beer", "drink", "apple"},
    ),
}

ORATORS = {
    "starling": OratorKind(
        id="starling",
        label="a silver-waistcoated starling orator",
        title="the starling orator",
        line='"One sip and your feet will dance faster than drums!"',
        tags={"orator", "bird"},
    ),
    "miller": OratorKind(
        id="miller",
        label="Old Brindle the flour-dusted orator",
        title="the village orator",
        line='"Come one, come all! The merriest cup in the valley is here!"',
        tags={"orator", "villager"},
    ),
    "cricket": OratorKind(
        id="cricket",
        label="a green-jacketed cricket orator",
        title="the cricket orator",
        line='"Foam for the weary, fizz for the merry, and enough for every friend!"',
        tags={"orator", "cricket"},
    ),
}

HELPERS = {
    "otter": HelperKind(
        id="otter",
        label="an otter",
        kind="creature",
        likes="honey bun",
        gift_line="The otter caught the smell at once and blinked with friendly surprise.",
        aid_line="With a whisk of paws and tail, the otter made the water safe to cross.",
        solves="river",
        tags={"otter", "helper", "river"},
    ),
    "goat": HelperKind(
        id="goat",
        label="a hill goat",
        kind="creature",
        likes="clover ribbon",
        gift_line="The goat lowered its head, nosed the ribbon, and gave a pleased little snort.",
        aid_line="With nimble horns, the goat worried the thorns apart and stamped a neat path through.",
        solves="bramble",
        tags={"goat", "helper", "bramble"},
    ),
    "fireflies": HelperKind(
        id="fireflies",
        label="a swirl of fireflies",
        kind="creature",
        likes="seed cake",
        gift_line="The fireflies drifted around the crumbs as if tiny lanterns had begun to smile.",
        aid_line="They spun into a bright ribbon and lit every dark root and stone ahead.",
        solves="shadow",
        tags={"fireflies", "helper", "light"},
    ),
}

OBSTACLES = {
    "river": Obstacle(
        id="river",
        label="the ribbon river",
        path="the willow path to the fairy spring",
        danger="the stepping stones were slick and the water hurried silver over them",
        solved_by="river",
        solved_text="Soon the child was over the water and dry-footed on the farther bank.",
        tags={"river", "water"},
    ),
    "bramble": Obstacle(
        id="bramble",
        label="the thorn gate",
        path="the fern lane to the fairy spring",
        danger="a wall of roses and briars had woven itself across the lane",
        solved_by="bramble",
        solved_text="In another moment there was a gap just wide enough for a child to slip through.",
        tags={"bramble", "thorns"},
    ),
    "shadow": Obstacle(
        id="shadow",
        label="the hush hollow",
        path="the moss road to the fairy spring",
        danger="the path ducked under old yews where shadows piled thick as blankets",
        solved_by="shadow",
        solved_text="The dark hollow lost its frightful look once the way shone clear.",
        tags={"shadow", "dark"},
    ),
}

GIFTS = {
    "honey_bun": Gift(
        id="honey_bun",
        label="honey bun",
        phrase="a honey bun wrapped in paper leaves",
        suits="otter",
        share_text="broke the honey bun in half and offered the warmest half away first",
        tags={"food", "sharing", "bun"},
    ),
    "clover_ribbon": Gift(
        id="clover_ribbon",
        label="clover ribbon",
        phrase="a clover ribbon from the dancing pole",
        suits="goat",
        share_text="untied the green ribbon and looped it kindly over the waiting horns",
        tags={"gift", "sharing", "ribbon"},
    ),
    "seed_cake": Gift(
        id="seed_cake",
        label="seed cake",
        phrase="a pocket seed cake with sugared crumbs",
        suits="fireflies",
        share_text="crumbled the seed cake onto a flat stone instead of keeping a bite back",
        tags={"food", "sharing", "cake"},
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Tansy", "Nell", "Poppy", "Wren", "Ivy", "Mabel"]
BOY_NAMES = ["Tobin", "Rowan", "Pip", "Alder", "Finn", "Bram", "Nico", "Milo"]
TRAITS = ["brave", "gentle", "curious", "bright", "kind", "quick"]


def helper_matches_obstacle(helper: HelperKind, obstacle: Obstacle) -> bool:
    return helper.solves == obstacle.solved_by


def gift_suits_helper(gift: Gift, helper: HelperKind) -> bool:
    return gift.suits == helper.id


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for festival_id in FESTIVALS:
        for beer_id in BEERS:
            for orator_id in ORATORS:
                for helper_id, helper in HELPERS.items():
                    for obstacle_id, obstacle in OBSTACLES.items():
                        for gift_id, gift in GIFTS.items():
                            if helper_matches_obstacle(helper, obstacle) and gift_suits_helper(gift, helper):
                                combos.append((festival_id, beer_id, orator_id, helper_id, obstacle_id, gift_id))
    return combos


def predict_shortage(world: World) -> dict:
    sim = world.copy()
    sim.get("crowd").memes["craze"] += 1
    propagate(sim, narrate=False)
    return {
        "keg_low": sim.get("keg").meters["low"] >= THRESHOLD,
        "hero_worry": sim.get("hero").memes["worry"] >= THRESHOLD,
    }


def open_fair(world: World, festival: Festival, beer: BeerKind, orator_cfg: OratorKind,
              hero: Entity) -> None:
    crowd = world.get("crowd")
    crowd.memes["joy"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"In the little village of {festival.village}, the morning of {festival.fair} came bright and strange. "
        f"{festival.decorations}. At the center of the square stood {beer.phrase}, {beer.taste}."
    )
    world.say(
        f"{orator_cfg.label} hopped upon the keg and lifted a shining spoon like a scepter. "
        f"{orator_cfg.line}"
    )


def craze_begins(world: World, hero: Entity, orator_cfg: OratorKind, beer: BeerKind) -> None:
    pred = predict_shortage(world)
    world.facts["predicted_keg_low"] = pred["keg_low"]
    world.get("crowd").memes["craze"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The words of {orator_cfg.title} fluttered through the square like sparrows. "
        f"Soon a craze began: cups bobbed in the air, neighbors pushed close, and everyone asked for {beer.label} at once."
    )
    if pred["keg_low"]:
        world.say(
            f"{hero.id}, who had been helping beside the ladle, heard the hollow knock from inside the keg and knew the last cups were near."
        )


def assign_quest(world: World, hero: Entity, elder: Entity, festival: Festival, obstacle: Obstacle) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'{elder.id}, keeper of the fair keys, bent low and whispered, "Only the fairy spring beyond {obstacle.label} can wake an empty keg. '
        f'Will you go?"'
    )
    world.say(
        f"{hero.id} looked at the thirsty square, then at {obstacle.path}, and nodded. So the child began a quest while the bells of {festival.fair} still rang."
    )


def meet_helper(world: World, hero: Entity, helper: HelperKind, obstacle: Obstacle) -> None:
    road = world.get("road")
    road.meters["blocked"] = 1.0
    world.say(
        f"Past the last stall, the road narrowed. On {obstacle.path}, {obstacle.danger}. "
        f"There {hero.id} met {helper.label}, waiting as if it had been listening for small footsteps."
    )


def share_gift(world: World, hero: Entity, helper_cfg: HelperKind, gift: Gift) -> None:
    hero.meters["gift_shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} carried {gift.phrase} from the fair. Instead of clutching it close, {hero.pronoun()} {gift.share_text}. "
        f"{helper_cfg.gift_line}"
    )


def cross_obstacle(world: World, obstacle: Obstacle, helper_cfg: HelperKind) -> None:
    propagate(world, narrate=False)
    world.say(helper_cfg.aid_line)
    world.say(obstacle.solved_text)


def ask_spring(world: World, hero: Entity, beer: BeerKind) -> None:
    hero.memes["wish"] += 1
    spring = world.get("spring")
    spring.memes["listening"] += 1
    world.say(
        f"Beyond the road, the fairy spring rose from a ring of white stones. "
        f"{hero.id} knelt and asked for enough {beer.label} to fill every waiting cup at home."
    )


def reveal_twist(world: World, hero: Entity) -> None:
    spring = world.get("spring")
    spring.memes["riddle"] += 1
    world.say(
        'The water answered in a voice as soft as spoons on glass: "I do not hurry for grabbing hands. '
        'Take home one first shining cup. Give it away before you drink, and the rest will follow."'
    )
    world.say(
        f"That was the twist of the quest: the spring wanted sharing, not begging."
    )
    hero.memes["wonder"] += 1


def first_shared_cup(world: World, hero: Entity, elder: Entity, beer: BeerKind) -> None:
    hero.memes["shares_first_cup"] += 1
    world.say(
        f"When {hero.id} came back, the spring had filled one small glass bottle with {beer.label} and nothing more. "
        f"The square fell quiet."
    )
    world.say(
        f"Though {hero.id} had run the whole long road, {hero.pronoun()} handed that first bright cup to {elder.id}, whose throat had gone dry from calming the crowd."
    )
    propagate(world, narrate=False)


def restored_feast(world: World, hero: Entity, festival: Festival, beer: BeerKind) -> None:
    world.say(
        f"At once the old keg gave a happy glug. {beer.foam} climbed the rim, and cup after cup filled as if the cask had remembered a secret song."
    )
    world.say(
        f"The pushing stopped. People laughed at their own foolish craze and made room for one another. From then on, the first pour of every fair was passed to someone else."
    )
    world.say(
        f"And so, under the bells and ribbons, {hero.id} learned that a feast grows larger when it is shared. All evening {festival.sendoff}, and no one drank alone."
    )


def tell(festival: Festival, beer: BeerKind, orator_cfg: OratorKind, helper_cfg: HelperKind,
         obstacle: Obstacle, gift: Gift, hero_name: str = "Elin", hero_gender: str = "girl",
         parent_type: str = "mother", trait: str = "kind") -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    elder = world.add(Entity(
        id="Mistress Rowan" if parent_type == "mother" else "Master Rowan",
        kind="character",
        type=parent_type,
        label="the elder",
        role="elder",
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="group",
        type="villagers",
        label="the villagers",
        role="crowd",
    ))
    keg = world.add(Entity(
        id="keg",
        kind="thing",
        type="keg",
        label=beer.label,
        role="keg",
    ))
    road = world.add(Entity(
        id="road",
        kind="thing",
        type="path",
        label=obstacle.path,
        role="road",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="creature",
        label=helper_cfg.label,
        role="helper",
        attrs={"likes": helper_cfg.likes},
        tags=set(helper_cfg.tags),
    ))
    spring = world.add(Entity(
        id="spring",
        kind="thing",
        type="spring",
        label="the fairy spring",
        role="spring",
    ))

    world.facts.update(
        festival=festival,
        beer=beer,
        orator=orator_cfg,
        helper_cfg=helper_cfg,
        obstacle=obstacle,
        gift=gift,
        hero=hero,
        elder=elder,
    )

    open_fair(world, festival, beer, orator_cfg, hero)
    world.para()
    craze_begins(world, hero, orator_cfg, beer)
    assign_quest(world, hero, elder, festival, obstacle)

    world.para()
    meet_helper(world, hero, helper_cfg, obstacle)
    share_gift(world, hero, helper_cfg, gift)
    cross_obstacle(world, obstacle, helper_cfg)
    ask_spring(world, hero, beer)
    reveal_twist(world, hero)

    world.para()
    first_shared_cup(world, hero, elder, beer)
    restored_feast(world, hero, festival, beer)

    world.facts.update(
        keg_restored=world.get("keg").meters["full"] >= THRESHOLD,
        crowd_calmed=world.get("crowd").memes["gratitude"] >= THRESHOLD,
        shared_with_helper=world.get("hero").meters["gift_shared"] >= THRESHOLD,
        shared_first_cup=world.get("hero").memes["shares_first_cup"] >= THRESHOLD,
        crossed_road=world.get("road").meters["crossed"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    festival: str
    beer: str
    orator: str
    helper: str
    obstacle: str
    gift: str
    hero_name: str
    hero_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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
    "orator": [
        (
            "What is an orator?",
            "An orator is a person who speaks to a crowd in a strong, clear way. In stories, an orator can stir people's feelings with words.",
        )
    ],
    "beer": [
        (
            "What is ginger beer?",
            "Ginger beer is a fizzy drink flavored with ginger. In children's stories, it is often treated as a sweet festival drink.",
        )
    ],
    "sharing": [
        (
            "Why does sharing help a group?",
            "Sharing helps everyone feel included and cared for. It also stops people from grabbing in a panic and makes it easier to solve problems together.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey taken for an important purpose. In a fairy tale, the traveler usually learns something on the way.",
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise that changes how the problem gets solved. It makes the ending feel fresh and meaningful.",
        )
    ],
    "otter": [
        (
            "Why are otters good swimmers?",
            "Otters have strong bodies and feet that help them move through water quickly. That is why an otter makes a good river helper in a tale.",
        )
    ],
    "goat": [
        (
            "Why can a goat climb tricky places?",
            "Goats are steady on their feet and very nimble. They are good at finding ways through rough ground.",
        )
    ],
    "fireflies": [
        (
            "Why do fireflies glow?",
            "Fireflies make their own tiny light. Their glow helps them signal in the dark.",
        )
    ],
    "river": [
        (
            "Why can a fast little river be hard to cross?",
            "Wet stones can be slippery, and moving water can rush around your feet. That is why crossing a river carefully matters.",
        )
    ],
    "bramble": [
        (
            "What is a bramble?",
            "A bramble is a thorny plant that can grow in a tangled patch. Its sharp stems can block a path.",
        )
    ],
    "shadow": [
        (
            "Why can a dark path feel scary?",
            "When you cannot see the way clearly, your mind imagines hidden trouble. A little light can make the same path feel safe again.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "orator",
    "beer",
    "sharing",
    "quest",
    "twist",
    "otter",
    "goat",
    "fireflies",
    "river",
    "bramble",
    "shadow",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    beer = f["beer"]
    festival = f["festival"]
    orator_cfg = f["orator"]
    helper = f["helper_cfg"]
    obstacle = f["obstacle"]
    return [
        f'Write a short fairy tale for a 3-to-5-year-old that includes the words "orator", "craze", and "{beer.label}".',
        f"Tell a fairy-tale story set at {festival.fair} where {orator_cfg.title} starts a craze over {beer.label}, and a child named {hero.id} goes on a quest to save the feast.",
        f"Write a gentle quest story with a twist: after {hero.id} shares kindly with {helper.label} and crosses {obstacle.label}, the magic answer turns out to be sharing the first cup away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    beer = f["beer"]
    festival = f["festival"]
    helper = f["helper_cfg"]
    obstacle = f["obstacle"]
    gift = f["gift"]
    orator_cfg = f["orator"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child at {festival.fair}. It also features {orator_cfg.title}, {helper.label}, and {elder.id}, who trusts {hero.id} with the quest.",
        ),
        (
            "What problem began at the fair?",
            f"A craze broke out when {orator_cfg.title} praised the {beer.label}, and everyone wanted a cup at once. That rush made the keg run low and worried {hero.id}.",
        ),
        (
            f"Why did {hero.id} go on a quest?",
            f"{elder.id} said only the fairy spring beyond {obstacle.label} could wake the empty keg. So {hero.id} left the square to help the whole village, not just to fetch a drink for {hero.pronoun('object')}.",
        ),
        (
            f"How did {hero.id} get past {obstacle.label}?",
            f"{hero.id} met {helper.label} on the road and shared {gift.phrase}. Because that kindness built trust, the helper cleared the way and the quest could continue.",
        ),
        (
            "What was the twist at the fairy spring?",
            f"The spring would not answer greedy asking. It said the first cup had to be shared away before the rest of the {beer.label} would return.",
        ),
        (
            f"How was the fair saved?",
            f"When {hero.id} came home with one shining cup, {hero.pronoun()} gave it to {elder.id} instead of drinking first. Then the keg filled again, and the crowd stopped pushing because sharing had broken the craze.",
        ),
        (
            "How did the story end?",
            f"The fair ended peacefully, with full cups and room for everyone. The villagers began passing the first pour to someone else, which showed that the village had truly changed.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"orator", "beer", "sharing", "quest", "twist"}
    helper = world.facts["helper_cfg"]
    obstacle = world.facts["obstacle"]
    if helper.id == "otter":
        tags.add("otter")
    if helper.id == "goat":
        tags.add("goat")
    if helper.id == "fireflies":
        tags.add("fireflies")
    tags |= set(obstacle.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        festival="blossom",
        beer="berry_beer",
        orator="starling",
        helper="otter",
        obstacle="river",
        gift="honey_bun",
        hero_name="Elin",
        hero_gender="girl",
        parent="mother",
        trait="kind",
    ),
    StoryParams(
        festival="moonlantern",
        beer="ginger_beer",
        orator="miller",
        helper="goat",
        obstacle="bramble",
        gift="clover_ribbon",
        hero_name="Tobin",
        hero_gender="boy",
        parent="father",
        trait="brave",
    ),
    StoryParams(
        festival="dewfeast",
        beer="apple_beer",
        orator="cricket",
        helper="fireflies",
        obstacle="shadow",
        gift="seed_cake",
        hero_name="Mira",
        hero_gender="girl",
        parent="mother",
        trait="curious",
    ),
]


def explain_rejection(helper: HelperKind, obstacle: Obstacle, gift: Gift) -> str:
    if not helper_matches_obstacle(helper, obstacle):
        return (
            f"(No story: {helper.label.capitalize()} cannot sensibly solve {obstacle.label}. "
            f"Pick a helper whose gift and skill fit that road.)"
        )
    if not gift_suits_helper(gift, helper):
        return (
            f"(No story: {gift.label} is not the gift that wins help from {helper.label}. "
            f"The sharing beat must be grounded in what that helper actually welcomes.)"
        )
    return "(No story: the requested combination is not reasonable in this world.)"


ASP_RULES = r"""
matches_obstacle(H, O) :- helper(H), obstacle(O), solves(H, K), solved_by(O, K).
likes_gift(H, G) :- helper(H), gift(G), likes(H, G).

valid(F, B, O, H, Ob, G) :-
    festival(F), beer(B), orator(O), helper(H), obstacle(Ob), gift(G),
    matches_obstacle(H, Ob), likes_gift(H, G).

quest_success(H, Ob, G) :- matches_obstacle(H, Ob), likes_gift(H, G).
ending(restored) :- quest_success(H, Ob, G), chosen_helper(H), chosen_obstacle(Ob), chosen_gift(G).
#show valid/6.
#show ending/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for festival_id in FESTIVALS:
        lines.append(asp.fact("festival", festival_id))
    for beer_id in BEERS:
        lines.append(asp.fact("beer", beer_id))
    for orator_id in ORATORS:
        lines.append(asp.fact("orator", orator_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("solves", helper_id, helper.solves))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("solved_by", obstacle_id, obstacle.solved_by))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        lines.append(asp.fact("likes", gift.suits, gift_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_gift", params.gift),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "ending")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    obstacle = OBSTACLES[params.obstacle]
    gift = GIFTS[params.gift]
    return "restored" if helper_matches_obstacle(helper, obstacle) and gift_suits_helper(gift, helper) else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: an orator starts a craze, a child goes on a quest, and sharing becomes the twist that saves the feast."
    )
    ap.add_argument("--festival", choices=FESTIVALS)
    ap.add_argument("--beer", choices=BEERS)
    ap.add_argument("--orator", choices=ORATORS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.obstacle:
        helper = HELPERS[args.helper]
        obstacle = OBSTACLES[args.obstacle]
        gift_id = args.gift or next(iter(GIFTS))
        gift = GIFTS[gift_id]
        if not (helper_matches_obstacle(helper, obstacle) and gift_suits_helper(gift, helper)):
            raise StoryError(explain_rejection(helper, obstacle, gift))
    if args.helper and args.gift:
        helper = HELPERS[args.helper]
        gift = GIFTS[args.gift]
        obstacle_id = args.obstacle or next(iter(OBSTACLES))
        obstacle = OBSTACLES[obstacle_id]
        if not gift_suits_helper(gift, helper):
            raise StoryError(explain_rejection(helper, obstacle, gift))
    if args.obstacle and args.gift and args.helper:
        helper = HELPERS[args.helper]
        obstacle = OBSTACLES[args.obstacle]
        gift = GIFTS[args.gift]
        if not (helper_matches_obstacle(helper, obstacle) and gift_suits_helper(gift, helper)):
            raise StoryError(explain_rejection(helper, obstacle, gift))

    combos = [
        combo for combo in valid_combos()
        if (args.festival is None or combo[0] == args.festival)
        and (args.beer is None or combo[1] == args.beer)
        and (args.orator is None or combo[2] == args.orator)
        and (args.helper is None or combo[3] == args.helper)
        and (args.obstacle is None or combo[4] == args.obstacle)
        and (args.gift is None or combo[5] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    festival_id, beer_id, orator_id, helper_id, obstacle_id, gift_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    hero_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        festival=festival_id,
        beer=beer_id,
        orator=orator_id,
        helper=helper_id,
        obstacle=obstacle_id,
        gift=gift_id,
        hero_name=hero_name,
        hero_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for key, registry in (
        ("festival", FESTIVALS),
        ("beer", BEERS),
        ("orator", ORATORS),
        ("helper", HELPERS),
        ("obstacle", OBSTACLES),
        ("gift", GIFTS),
    ):
        value = getattr(params, key)
        if value not in registry:
            raise StoryError(f"(Invalid {key}: {value})")

    helper = HELPERS[params.helper]
    obstacle = OBSTACLES[params.obstacle]
    gift = GIFTS[params.gift]
    if not helper_matches_obstacle(helper, obstacle) or not gift_suits_helper(gift, helper):
        raise StoryError(explain_rejection(helper, obstacle, gift))

    world = tell(
        festival=FESTIVALS[params.festival],
        beer=BEERS[params.beer],
        orator_cfg=ORATORS[params.orator],
        helper_cfg=helper,
        obstacle=obstacle,
        gift=gift,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
        trait=params.trait,
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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = [p for p in cases if asp_ending(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} ending results differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (festival, beer, orator, helper, obstacle, gift) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:12}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.beer} at {p.festival} "
                f"({p.helper}, {p.obstacle}, {p.gift})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
