#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/paddy_magic_conflict_heartwarming.py
===============================================================

A standalone story world about Paddy, a parade of little paper boats, and a
small piece of magic that can either be hoarded or shared.

Premise
-------
Paddy and a friend are getting ready for an evening river parade. The friend has
a real problem with their paper boat: a torn sail, a leaky hull, or a missing
glow. Paddy happens to have the one magical item that can fix it. At first,
Paddy wants to keep the magic for his own boat because he wants his own entry to
look extra special. That selfish impulse creates the conflict. Then an older
helper or Paddy's own kinder feelings turn the story toward repair, apology, and
a warm shared ending.

Why the reasonableness constraint exists
----------------------------------------
This world refuses to tell stories where the chosen magic cannot honestly solve
the chosen mishap. Moon thread can mend paper tears; a patch pearl can seal a
leak; a glow seed can relight a dark little lantern-boat. If the world let any
magic fix any problem, the middle turn would feel fake instead of earned.

Run it
------
    python storyworlds/worlds/gpt-5.4/paddy_magic_conflict_heartwarming.py
    python storyworlds/worlds/gpt-5.4/paddy_magic_conflict_heartwarming.py --theme moonparade --magic moon_thread --mishap torn_sail
    python storyworlds/worlds/gpt-5.4/paddy_magic_conflict_heartwarming.py --magic glow_seed --mishap leaking_hull
    python storyworlds/worlds/gpt-5.4/paddy_magic_conflict_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/paddy_magic_conflict_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/paddy_magic_conflict_heartwarming.py --trace --seed 11
    python storyworlds/worlds/gpt-5.4/paddy_magic_conflict_heartwarming.py --verify
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

KIND_TRAITS = {"kind", "gentle", "thoughtful", "patient"}
QUICK_HELP_MIN = 5


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Theme:
    id: str
    place: str
    festival: str
    water: str
    lights: str
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
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    spark: str
    fix_text: str
    qa_fix: str
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
class Mishap:
    id: str
    label: str
    trouble: str
    cannot: str
    need: str
    worry_text: str
    fixed_text: str
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
class HelperCfg:
    id: str
    type: str
    entrance: str
    guidance: str
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


def _r_problem_blocks(world: World) -> list[str]:
    out: list[str] = []
    friend_boat = world.get("friend_boat")
    problem_keys = ("torn", "leaking", "dark")
    if any(friend_boat.meters[k] >= THRESHOLD for k in problem_keys):
        sig = ("problem", "friend_boat")
        if sig not in world.fired:
            world.fired.add(sig)
            friend_boat.meters["ready"] = 0.0
            friend_boat.meters["left_out_risk"] += 1
            friend = world.get("Friend")
            friend.memes["worry"] += 1
            out.append("__problem__")
    return out


def _r_repair_clears(world: World) -> list[str]:
    out: list[str] = []
    boat = world.get("friend_boat")
    if boat.meters["mended"] < THRESHOLD:
        return out
    sig = ("repair", "friend_boat")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boat.meters["torn"] = 0.0
    boat.meters["leaking"] = 0.0
    boat.meters["dark"] = 0.0
    boat.meters["ready"] = 1.0
    boat.meters["left_out_risk"] = 0.0
    friend = world.get("Friend")
    friend.memes["worry"] = 0.0
    friend.memes["relief"] += 1
    out.append("__repaired__")
    return out


def _r_quarrel(world: World) -> list[str]:
    out: list[str] = []
    paddy = world.get("Paddy")
    friend = world.get("Friend")
    if paddy.memes["hoarding"] < THRESHOLD or friend.memes["hurt"] < THRESHOLD:
        return out
    sig = ("quarrel", "kids")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    paddy.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    out.append("__quarrel__")
    return out


def _r_warmth(world: World) -> list[str]:
    out: list[str] = []
    paddy = world.get("Paddy")
    friend = world.get("Friend")
    own_boat = world.get("paddy_boat")
    friend_boat = world.get("friend_boat")
    if (
        own_boat.meters["ready"] >= THRESHOLD
        and friend_boat.meters["ready"] >= THRESHOLD
        and paddy.memes["shared"] >= THRESHOLD
        and paddy.memes["apology"] >= THRESHOLD
    ):
        sig = ("warmth", "ending")
        if sig in world.fired:
            return out
        world.fired.add(sig)
        paddy.memes["warmth"] += 1
        friend.memes["warmth"] += 1
        out.append("__warmth__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="problem_blocks", tag="physical", apply=_r_problem_blocks),
    Rule(name="repair_clears", tag="physical", apply=_r_repair_clears),
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="warmth", tag="emotional", apply=_r_warmth),
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


THEMES = {
    "moonparade": Theme(
        id="moonparade",
        place="the little bridge over the stream",
        festival="the moon parade",
        water="the stream",
        lights="round lanterns hung like moons along the rail",
        sendoff="The boats drifted in a silver line under the evening sky.",
        tags={"parade", "stream"},
    ),
    "frognight": Theme(
        id="frognight",
        place="the duck pond path",
        festival="frog night",
        water="the pond",
        lights="tiny jar lights blinked by the reeds",
        sendoff="The boats bobbed past the reeds while frogs croaked like soft drums.",
        tags={"parade", "pond"},
    ),
    "harvestglow": Theme(
        id="harvestglow",
        place="the old canal gate",
        festival="the harvest glow walk",
        water="the canal",
        lights="paper stars shone from every fence post",
        sendoff="The boats slid along the dark water as if the stars had come down to visit.",
        tags={"parade", "canal"},
    ),
}

MAGIC = {
    "moon_thread": MagicItem(
        id="moon_thread",
        label="moon thread",
        phrase="a silver spool of moon thread",
        effect="tear",
        spark="The thread flashed once, thin and bright as a moonbeam.",
        fix_text="stitched the torn paper together with three tiny shining loops",
        qa_fix="used moon thread to stitch the torn sail back together",
        tags={"magic", "repair"},
    ),
    "patch_pearl": MagicItem(
        id="patch_pearl",
        label="patch pearl",
        phrase="a round patch pearl",
        effect="leak",
        spark="The pearl gave one plump, watery blink.",
        fix_text="pressed the pearl to the damp seam, and the leak sealed itself smooth",
        qa_fix="used the patch pearl to seal the leak in the boat",
        tags={"magic", "repair"},
    ),
    "glow_seed": MagicItem(
        id="glow_seed",
        label="glow seed",
        phrase="a warm little glow seed",
        effect="dark",
        spark="The seed opened like a tiny flower of light.",
        fix_text="tucked the glow seed inside, and the little boat filled with soft gold light",
        qa_fix="shared the glow seed so the dark boat could shine again",
        tags={"magic", "light"},
    ),
}

MISHAPS = {
    "torn_sail": Mishap(
        id="torn_sail",
        label="torn sail",
        trouble="the paper sail had ripped down one side",
        cannot="it kept folding sadly instead of standing tall",
        need="tear",
        worry_text="Without a whole sail, the boat would look droopy in the parade.",
        fixed_text="The sail stood up straight again, neat and bright.",
        tags={"boat", "tear"},
    ),
    "leaking_hull": Mishap(
        id="leaking_hull",
        label="leaking hull",
        trouble="a wet seam in the bottom had started to leak",
        cannot="it would take in water before it reached the lanterns",
        need="leak",
        worry_text="A leaking boat could sink before the song at the bridge was done.",
        fixed_text="The hull stopped weeping water and sat proud on the stream.",
        tags={"boat", "leak"},
    ),
    "dark_lantern": Mishap(
        id="dark_lantern",
        label="dark lantern",
        trouble="the small light inside had gone dark",
        cannot="the boat looked plain beside the glowing ones",
        need="dark",
        worry_text="Without a glow, the boat would disappear into the evening water.",
        fixed_text="A gentle light bloomed inside the boat and made its paper walls shine.",
        tags={"boat", "light"},
    ),
}

HELPERS = {
    "grandmother": HelperCfg(
        id="grandmother",
        type="grandmother",
        entrance="Grandma came along the path with a basket of ribbons on her arm.",
        guidance="A lovely parade is not made by one bright boat alone.",
        tags={"grandma"},
    ),
    "grandfather": HelperCfg(
        id="grandfather",
        type="grandfather",
        entrance="Grandpa looked up from tying the rail lanterns and noticed their faces.",
        guidance="A bright heart can carry more than one boat at a time.",
        tags={"grandpa"},
    ),
    "aunt": HelperCfg(
        id="aunt",
        type="aunt",
        entrance="Auntie came from the table of tea cakes and bent down beside them.",
        guidance="Magic looks smaller when you clench it, and bigger when you share it.",
        tags={"aunt"},
    ),
}

FRIEND_NAMES = ["Mina", "Tao", "Nell", "Rafi", "June", "Eli", "Sana", "Kit"]
TRAITS = ["kind", "gentle", "thoughtful", "patient", "proud", "stubborn", "hasty", "showy"]
FRIEND_GENDERS = ["girl", "boy"]
PADDY_GENDERS = ["girl", "boy"]


def can_fix(magic: MagicItem, mishap: Mishap) -> bool:
    return magic.effect == mishap.need


def kindness_score(trait: str, helper: str) -> int:
    base = 6 if trait in KIND_TRAITS else 3
    if helper == "grandmother":
        base += 1
    return base


def quick_share(trait: str, helper: str) -> bool:
    return kindness_score(trait, helper) >= QUICK_HELP_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for magic_id, magic in MAGIC.items():
            for mishap_id, mishap in MISHAPS.items():
                if can_fix(magic, mishap):
                    combos.append((theme_id, magic_id, mishap_id))
    return combos


def predict_left_out(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    friend = sim.get("Friend")
    boat = sim.get("friend_boat")
    return {
        "ready": boat.meters["ready"] >= THRESHOLD,
        "left_out_risk": boat.meters["left_out_risk"],
        "worry": friend.memes["worry"],
    }


def introduce(world: World, paddy: Entity, friend: Entity, theme: Theme) -> None:
    for child in (paddy, friend):
        child.memes["joy"] += 1
    world.say(
        f"Paddy and {friend.id} hurried to {theme.place} for {theme.festival}. "
        f"{theme.lights}, and everyone had brought a little paper boat to set on {theme.water}."
    )
    world.say(
        f"Paddy carried a blue boat with a curled paper moon on the front. "
        f"{friend.id} carried a boat painted with careful little stars."
    )


def reveal_mishap(world: World, friend: Entity, mishap: Mishap) -> None:
    boat = world.get("friend_boat")
    if mishap.need == "tear":
        boat.meters["torn"] += 1
    elif mishap.need == "leak":
        boat.meters["leaking"] += 1
    elif mishap.need == "dark":
        boat.meters["dark"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {friend.id} knelt at the edge of the path, {friend.pronoun('possessive')} face fell. "
        f"{friend.pronoun('possessive').capitalize()} boat had trouble: {mishap.trouble}, and {mishap.cannot}."
    )
    world.say(mishap.worry_text)


def show_magic(world: World, paddy: Entity, magic: MagicItem) -> None:
    paddy.memes["pride"] += 1
    world.say(
        f"Paddy slipped a hand into {paddy.pronoun('possessive')} pocket and felt {magic.phrase}. "
        f"It was family magic, saved for small true needs."
    )
    world.say(
        f'"I could use {magic.label} on my own boat," Paddy said softly. '
        f'"It would make mine the prettiest on the water."'
    )


def ask_for_help(world: World, friend: Entity, magic: MagicItem) -> None:
    friend.memes["hope"] += 1
    world.say(
        f'{friend.id} looked up. "Do you think {magic.label} could help mine?" '
        f'{friend.pronoun().capitalize()} asked.'
    )


def warn(world: World, helper: Entity, friend: Entity) -> None:
    pred = predict_left_out(world)
    world.facts["predicted_left_out_risk"] = pred["left_out_risk"]
    world.facts["predicted_worry"] = pred["worry"]
    world.say(helper.attrs["entrance"])
    world.say(
        f'{helper.label_word.capitalize()} saw the broken boat and the small pause between the children. '
        f'"If one child has to stand and watch while the other cheers, the water will not feel festive for long," '
        f'{helper.pronoun()} said.'
    )


def share_early(world: World, paddy: Entity, friend: Entity, helper: Entity) -> None:
    paddy.memes["generosity"] += 1
    paddy.memes["shared"] += 1
    paddy.memes["apology"] += 1
    friend.memes["hurt"] = 0.0
    world.say(
        f'Paddy looked from {paddy.pronoun("possessive")} own boat to {friend.id}\'s and remembered '
        f'what {helper.label_word} had said. The wanting in Paddy\'s chest softened.'
    )
    world.say(
        f'"You should not be left out," Paddy said. "I am sorry I thought about keeping it all for myself."'
    )


def hoard(world: World, paddy: Entity, friend: Entity) -> None:
    paddy.memes["hoarding"] += 1
    friend.memes["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Maybe I should save it," Paddy said, closing {paddy.pronoun("possessive")} fingers around the magic. '
        f'"What if my boat needs to be extra special?"'
    )
    world.say(
        f'{friend.id} lowered {friend.pronoun("possessive")} eyes. "I only wanted to float beside you," '
        f'{friend.pronoun()} said.'
    )


def quarrel(world: World, paddy: Entity, friend: Entity, helper: Entity) -> None:
    world.say(
        f'The words landed badly. Paddy felt hot in the face, and {friend.id} stepped back with the broken boat pressed to '
        f'{friend.pronoun("possessive")} coat.'
    )
    world.say(
        f'{helper.label_word.capitalize()} did not scold. {helper.pronoun().capitalize()} only said, '
        f'"{helper.attrs["guidance"]}"'
    )


def soften(world: World, paddy: Entity, friend: Entity) -> None:
    paddy.memes["guilt"] += 1
    paddy.memes["shared"] += 1
    paddy.memes["apology"] += 1
    paddy.memes["generosity"] += 1
    friend.memes["hurt"] = 0.0
    friend.memes["hope"] += 1
    world.say(
        f'Paddy looked at {friend.id}\'s hands holding the broken boat very carefully, as if it still mattered. '
        f'That made the selfish feeling seem small.'
    )
    world.say(
        f'"Wait," Paddy said, opening {paddy.pronoun("possessive")} hand. '
        f'"I was wrong. Let us fix yours first, and then we will send them together."'
    )


def mend(world: World, paddy: Entity, friend: Entity, magic: MagicItem, mishap: Mishap) -> None:
    boat = world.get("friend_boat")
    boat.meters["mended"] += 1
    propagate(world, narrate=False)
    world.say(magic.spark)
    world.say(
        f'Paddy touched the magic to the boat. It {magic.fix_text}. {mishap.fixed_text}'
    )
    world.say(
        f'{friend.id} let out a happy little breath and hugged the boat against {friend.pronoun("possessive")} sweater.'
    )


def launch(world: World, paddy: Entity, friend: Entity, theme: Theme) -> None:
    world.get("paddy_boat").meters["ready"] = 1.0
    paddy.memes["joy"] += 1
    friend.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Together they crouched by {theme.water} and set both boats down at the same time.'
    )
    world.say(
        f'{theme.sendoff} Paddy\'s boat sailed on one side, and {friend.id}\'s sailed on the other, close enough to seem like friends.'
    )
    world.say(
        f'Paddy and {friend.id} leaned on each other\'s shoulders and watched until the lights looked like two tiny stars going home.'
    )


def tell(
    theme: Theme,
    magic: MagicItem,
    mishap: Mishap,
    helper_cfg: HelperCfg,
    paddy_gender: str = "boy",
    friend_name: str = "Mina",
    friend_gender: str = "girl",
    trait: str = "kind",
) -> World:
    world = World()
    paddy = world.add(
        Entity(
            id="Paddy",
            kind="character",
            type=paddy_gender,
            role="hero",
            traits=[trait],
            attrs={},
            tags={"paddy"},
        )
    )
    friend = world.add(
        Entity(
            id="Friend",
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            attrs={"name": friend_name},
            tags={"friend"},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_cfg.type,
            role="helper",
            attrs={"entrance": helper_cfg.entrance, "guidance": helper_cfg.guidance},
            tags=set(helper_cfg.tags),
        )
    )
    paddy_boat = world.add(
        Entity(
            id="paddy_boat",
            type="boat",
            label="Paddy's boat",
            owner="Paddy",
            tags={"boat"},
        )
    )
    friend_boat = world.add(
        Entity(
            id="friend_boat",
            type="boat",
            label=f"{friend_name}'s boat",
            owner="Friend",
            tags={"boat"},
        )
    )
    paddy_boat.meters["ready"] = 1.0
    friend_boat.meters["ready"] = 1.0
    for ent in (paddy, friend, helper, paddy_boat, friend_boat):
        ent.attrs = dict(ent.attrs)

    introduce(world, paddy, friend, theme)

    world.para()
    reveal_mishap(world, friend, mishap)
    show_magic(world, paddy, magic)
    ask_for_help(world, friend, magic)
    warn(world, helper, friend)

    early = quick_share(trait, helper_cfg.id)
    if early:
        world.para()
        share_early(world, paddy, friend, helper)
        mend(world, paddy, friend, magic, mishap)
        outcome = "early_share"
    else:
        world.para()
        hoard(world, paddy, friend)
        quarrel(world, paddy, friend, helper)
        soften(world, paddy, friend)
        mend(world, paddy, friend, magic, mishap)
        outcome = "after_quarrel"

    world.para()
    launch(world, paddy, friend, theme)

    world.facts.update(
        theme=theme,
        magic=magic,
        mishap=mishap,
        helper_cfg=helper_cfg,
        paddy=paddy,
        friend=friend,
        friend_name=friend_name,
        helper=helper,
        paddy_boat=paddy_boat,
        friend_boat=friend_boat,
        outcome=outcome,
        fixed=friend_boat.meters["mended"] >= THRESHOLD,
        quick=early,
        repaired_with=magic.id,
        conflict=outcome == "after_quarrel",
        shared=paddy.memes["shared"] >= THRESHOLD,
        warmth=paddy.memes["warmth"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "magic": [
        (
            "What is magic in a story like this?",
            "Magic in a story is something special that can do a wonderful thing ordinary hands cannot do. It still matters how a person chooses to use it."
        )
    ],
    "repair": [
        (
            "What does it mean to repair something?",
            "To repair something means to fix what is broken so it can be used again. Careful fixing can save a treasured thing."
        )
    ],
    "light": [
        (
            "Why is a little light important on dark water?",
            "A little light helps people see where something is and makes it glow in the night. On dark water, light also makes a boat feel part of the celebration."
        )
    ],
    "boat": [
        (
            "Why can a paper boat need gentle handling?",
            "Paper boats are light and pretty, but they can tear, get soggy, or bend easily. Gentle hands help them stay whole."
        )
    ],
    "tear": [
        (
            "What happens when paper tears?",
            "When paper tears, a rip opens in it and it becomes weaker. A torn piece may fold or flap instead of holding its shape."
        )
    ],
    "leak": [
        (
            "What is a leak in a little boat?",
            "A leak is a place where water can slip into the boat. If too much water gets in, the boat may sink."
        )
    ],
    "grandma": [
        (
            "How can a grandma help during a disagreement?",
            "A grandma can help children slow down and see each other's feelings. Kind words from a calm grown-up often make room for a better choice."
        )
    ],
    "grandpa": [
        (
            "How can a grandpa help when children argue?",
            "A grandpa can remind children what really matters and help them think past the first angry feeling. That can turn an argument into a chance to be generous."
        )
    ],
    "aunt": [
        (
            "Why is a calm aunt useful in a conflict?",
            "A calm aunt can notice hurt feelings and guide children without shouting. Gentle guidance helps children choose kindness for themselves."
        )
    ],
}
KNOWLEDGE_ORDER = ["magic", "repair", "boat", "tear", "leak", "light", "grandma", "grandpa", "aunt"]


@dataclass
class StoryParams:
    theme: str
    magic: str
    mishap: str
    helper: str
    paddy_gender: str
    friend_name: str
    friend_gender: str
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


CURATED = [
    StoryParams(
        theme="moonparade",
        magic="moon_thread",
        mishap="torn_sail",
        helper="grandmother",
        paddy_gender="boy",
        friend_name="Mina",
        friend_gender="girl",
        trait="kind",
    ),
    StoryParams(
        theme="frognight",
        magic="patch_pearl",
        mishap="leaking_hull",
        helper="grandfather",
        paddy_gender="girl",
        friend_name="Tao",
        friend_gender="boy",
        trait="proud",
    ),
    StoryParams(
        theme="harvestglow",
        magic="glow_seed",
        mishap="dark_lantern",
        helper="aunt",
        paddy_gender="boy",
        friend_name="June",
        friend_gender="girl",
        trait="thoughtful",
    ),
    StoryParams(
        theme="moonparade",
        magic="patch_pearl",
        mishap="leaking_hull",
        helper="grandmother",
        paddy_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        trait="stubborn",
    ),
    StoryParams(
        theme="frognight",
        magic="glow_seed",
        mishap="dark_lantern",
        helper="grandfather",
        paddy_gender="boy",
        friend_name="Sana",
        friend_gender="girl",
        trait="gentle",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    magic = f["magic"]
    mishap = f["mishap"]
    friend_name = f["friend_name"]
    if f["outcome"] == "after_quarrel":
        return [
            f'Write a heartwarming magic story for a 3-to-5-year-old that includes the word "paddy" and a small conflict about sharing. Set it during {theme.festival}.',
            f"Tell a gentle story where Paddy has {magic.label}, {friend_name}'s boat has a {mishap.label}, and Paddy first makes a selfish choice before fixing it.",
            f"Write a story about a child learning that sharing magic can mend both a broken thing and a hurt feeling.",
        ]
    return [
        f'Write a heartwarming magic story for a 3-to-5-year-old that includes the word "paddy" and ends with two children sending boats onto the water together.',
        f"Tell a gentle story set at {theme.festival} where Paddy uses {magic.label} to help a friend's boat after a small moment of temptation.",
        f"Write a warm story where a child chooses kindness over showing off, and the ending image is two little boats floating side by side.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    paddy = f["paddy"]
    friend = f["friend"]
    helper = f["helper"]
    theme = f["theme"]
    magic = f["magic"]
    mishap = f["mishap"]
    friend_name = f["friend_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Paddy and {friend_name}, two children getting ready for {theme.festival}. A loving {helper.label_word} also helps them choose a kinder path."
        ),
        (
            f"What problem did {friend_name}'s boat have?",
            f"{friend_name}'s boat had a {mishap.label}. Because of that problem, the boat was not ready to join the parade, and {friend_name} began to worry about being left out."
        ),
        (
            "Why was there a conflict?",
            f"The conflict started because Paddy had the magic that could help, but first wanted to keep it for Paddy's own boat. That hurt {friend_name}'s feelings because the broken boat needed help more than Paddy's boat needed extra sparkle."
        ),
    ]
    if f["outcome"] == "after_quarrel":
        qa.append(
            (
                "How did the conflict change?",
                f"At first Paddy held the magic back and the children had a small quarrel. Then Paddy saw how carefully {friend_name} was holding the damaged boat, felt sorry, and chose to share instead."
            )
        )
    else:
        qa.append(
            (
                "What made Paddy change course?",
                f"Paddy listened to {helper.label_word}'s gentle warning and looked again at {friend_name}'s worried face. That helped Paddy see that being together mattered more than having the prettiest boat."
            )
        )
    qa.append(
        (
            f"How did Paddy fix {friend_name}'s boat?",
            f"Paddy {magic.qa_fix}. The magic solved the real problem, so the boat became ready for the water again."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The two children set both boats on {theme.water} together and watched them float side by side. That ending shows the change clearly, because the magic repaired the boat and Paddy's kindness repaired the friendship too."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["magic"].tags) | set(f["mishap"].tags) | set(f["helper"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(magic: MagicItem, mishap: Mishap) -> str:
    return (
        f"(No story: {magic.label} fixes {magic.effect} problems, but {mishap.label} needs {mishap.need} magic. "
        f"The middle turn only works when the magic can honestly mend the mishap.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "early_share" if quick_share(params.trait, params.helper) else "after_quarrel"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
fixable(M, H) :- magic(M), mishap(H), effect(M, E), need(H, E).
valid(T, M, H) :- theme(T), fixable(M, H).

% --- outcome model ---------------------------------------------------------
kind_score(6) :- trait(T), kind_trait(T).
kind_score(3) :- trait(T), not kind_trait(T).
helper_bonus(1) :- chosen_helper(grandmother).
helper_bonus(0) :- chosen_helper(H), H != grandmother.
total_score(S + B) :- kind_score(S), helper_bonus(B).
quick_share :- total_score(T), quick_help_min(M), T >= M.

outcome(early_share) :- quick_share.
outcome(after_quarrel) :- not quick_share.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for magic_id, magic in MAGIC.items():
        lines.append(asp.fact("magic", magic_id))
        lines.append(asp.fact("effect", magic_id, magic.effect))
    for mishap_id, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mishap_id))
        lines.append(asp.fact("need", mishap_id, mishap.need))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for trait in sorted(KIND_TRAITS):
        lines.append(asp.fact("kind_trait", trait))
    lines.append(asp.fact("quick_help_min", QUICK_HELP_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Paddy, a little magic repair, a small conflict, and a heartwarming shared ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--paddy-gender", choices=PADDY_GENDERS)
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=FRIEND_GENDERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.magic and args.mishap:
        magic = MAGIC[args.magic]
        mishap = MISHAPS[args.mishap]
        if not can_fix(magic, mishap):
            raise StoryError(explain_rejection(magic, mishap))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.magic is None or combo[1] == args.magic)
        and (args.mishap is None or combo[2] == args.mishap)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, magic_id, mishap_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    paddy_gender = args.paddy_gender or rng.choice(PADDY_GENDERS)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    friend_gender = args.friend_gender or rng.choice(FRIEND_GENDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        theme=theme_id,
        magic=magic_id,
        mishap=mishap_id,
        helper=helper_id,
        paddy_gender=paddy_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        magic = MAGIC[params.magic]
        mishap = MISHAPS[params.mishap]
        helper = HELPERS[params.helper]
    except KeyError as exc:
        raise StoryError(f"(Invalid story parameter: {exc.args[0]})") from None

    if not can_fix(magic, mishap):
        raise StoryError(explain_rejection(magic, mishap))
    if params.trait not in TRAITS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if params.paddy_gender not in PADDY_GENDERS:
        raise StoryError(f"(Invalid paddy gender: {params.paddy_gender})")
    if params.friend_gender not in FRIEND_GENDERS:
        raise StoryError(f"(Invalid friend gender: {params.friend_gender})")

    world = tell(
        theme=theme,
        magic=magic,
        mishap=mishap,
        helper_cfg=helper,
        paddy_gender=params.paddy_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        trait=params.trait,
    )
    if "Paddy" not in world.render():
        raise StoryError("(Story generation failed to include Paddy in the text.)")

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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test generate()/emit() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

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
        print(f"{len(combos)} compatible (theme, magic, mishap) combos:\n")
        for theme, magic, mishap in combos:
            print(f"  {theme:12} {magic:12} {mishap}")
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
            header = f"### Paddy with {p.magic} for {p.mishap} at {p.theme} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
