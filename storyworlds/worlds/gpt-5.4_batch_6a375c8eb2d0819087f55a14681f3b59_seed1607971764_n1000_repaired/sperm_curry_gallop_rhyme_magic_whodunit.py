#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sperm_curry_gallop_rhyme_magic_whodunit.py
=====================================================================

A small storyworld about a missing magic rhyme bell at a twilight fair.

This world rebuilds a gentle whodunit shape for young children:
a magical show cannot begin because an important bell is gone,
the children notice concrete clues around the fair,
they test a rhyme spell that reveals the hiding place,
and the "culprit" turns out to be someone who borrowed the bell
for a worried, kind-hearted reason and forgot to ask first.

The fair always includes the seed words in-story:
- a curry stall with warm steam,
- a pony that can gallop for the parade,
- a big sperm whale balloon over the harbor lane.

Run it
------
    python storyworlds/worlds/gpt-5.4/sperm_curry_gallop_rhyme_magic_whodunit.py
    python storyworlds/worlds/gpt-5.4/sperm_curry_gallop_rhyme_magic_whodunit.py --culprit cook
    python storyworlds/worlds/gpt-5.4/sperm_curry_gallop_rhyme_magic_whodunit.py --hideout whale_float
    python storyworlds/worlds/gpt-5.4/sperm_curry_gallop_rhyme_magic_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/sperm_curry_gallop_rhyme_magic_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/sperm_curry_gallop_rhyme_magic_whodunit.py --verify
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
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
class Suspect:
    id: str
    label: str
    type: str
    role_label: str
    clue_line: str
    interview_line: str
    worry_line: str
    reason: str
    apology: str
    can_hide: set[str] = field(default_factory=set)
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
class Hideout:
    id: str
    label: str
    place: str
    found_line: str
    reveal_line: str
    traits: set[str] = field(default_factory=set)
    allowed_suspects: set[str] = field(default_factory=set)
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
class Spell:
    id: str
    name: str
    chant: str
    effect: str
    works_on: set[str] = field(default_factory=set)
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


def _r_missing_bell_worry(world: World) -> list[str]:
    bell = world.get("bell")
    if bell.meters["missing"] < THRESHOLD:
        return []
    culprit_id = world.facts.get("culprit_id", "")
    if not culprit_id or culprit_id not in world.entities:
        return []
    culprit = world.get(culprit_id)
    sig = ("worry", culprit_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    culprit.memes["worry"] += 1
    hero = world.get("hero")
    hero.memes["curious"] += 1
    return []


def _r_collect_clue(world: World) -> list[str]:
    bell = world.get("bell")
    if bell.meters["missing"] < THRESHOLD:
        return []
    clue = world.get("clue")
    if clue.meters["noticed"] >= THRESHOLD:
        return []
    suspect = SUSPECTS[world.facts["culprit_id"]]
    sig = ("clue", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["noticed"] += 1
    clue.attrs["text"] = suspect.clue_line
    hero = world.get("hero")
    hero.meters["clues"] += 1
    return []


def _r_spell_reveal(world: World) -> list[str]:
    if world.facts.get("spell_cast") is not True:
        return []
    hideout = world.get("hideout")
    if hideout.meters["glowing"] >= THRESHOLD:
        return []
    bell = world.get("bell")
    sig = ("reveal", hideout.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hideout.meters["glowing"] += 1
    bell.meters["found"] += 1
    bell.meters["missing"] = 0.0
    hero = world.get("hero")
    helper = world.get("helper")
    culprit = world.get(world.facts["culprit_id"])
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    culprit.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_bell_worry", tag="social", apply=_r_missing_bell_worry),
    Rule(name="collect_clue", tag="evidence", apply=_r_collect_clue),
    Rule(name="spell_reveal", tag="magic", apply=_r_spell_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SUSPECTS = {
    "cook": Suspect(
        id="cook",
        label="Auntie Pema",
        type="woman",
        role_label="the curry cook",
        clue_line="A warm dot of yellow curry shone on the empty velvet stand.",
        interview_line='"I have been stirring the supper pot," Auntie Pema said, lifting a wooden spoon.',
        worry_line="Auntie Pema kept glancing toward the spice crates instead of the stage.",
        reason="she had borrowed the bell to call a lost kitten from behind the spice crates, and then the supper rush swept her away.",
        apology='"I should have asked first," Auntie Pema said. "I was trying to help, but borrowing in a hurry still needs asking."',
        can_hide={"spice_crate", "recipe_drawer"},
        tags={"curry", "cook"},
    ),
    "stable": Suspect(
        id="stable",
        label="Bram",
        type="boy",
        role_label="the pony keeper",
        clue_line="A soft straw thread and a tiny half-moon hoofprint lay by the stand.",
        interview_line='"Pebble wanted to gallop before the parade," Bram said, patting a small saddle.',
        worry_line="Bram answered quickly, but his eyes flicked toward the saddle bags and the hay loft.",
        reason="he had borrowed the bell to soothe Pebble the pony before the parade gallop, and then hid it away when the pony finally settled.",
        apology='"I meant to bring it right back," Bram whispered. "Next time I will ask before I borrow anything at all."',
        can_hide={"saddle_bag", "hay_loft"},
        tags={"gallop", "pony"},
    ),
    "painter": Suspect(
        id="painter",
        label="Oona",
        type="girl",
        role_label="the float painter",
        clue_line="A blue paint fleck sparkled there, and beside it stuck a tiny sperm whale sticker.",
        interview_line='"The harbor float still needs one last silver wave," Oona said, holding a paint rag.',
        worry_line="Oona smiled too brightly and stood a little in front of the paint chest and the sperm whale float.",
        reason="she had borrowed the bell to test how moon-glow paint would shimmer inside the big sperm whale float, and then forgot it there when someone called for more ribbons.",
        apology='"I was excited and thought only about the float," Oona said. "Magic things are still other people\'s things, and I must ask first."',
        can_hide={"paint_chest", "whale_float"},
        tags={"sperm_whale", "paint"},
    ),
}

HIDEOUTS = {
    "spice_crate": Hideout(
        id="spice_crate",
        label="the spice crate",
        place="behind the curry stall",
        found_line="The crate hummed softly, and under a folded sack of cinnamon sat the silver bell.",
        reveal_line="A ribbon of light slipped behind the curry stall and curled around the spice crate.",
        traits={"dark", "wood"},
        allowed_suspects={"cook"},
        tags={"curry", "crate"},
    ),
    "recipe_drawer": Hideout(
        id="recipe_drawer",
        label="the recipe drawer",
        place="under the cook's small table",
        found_line="The drawer popped open with a tink, and the silver bell rested on a stack of flour-dusted recipe cards.",
        reveal_line="Sparkles ran under the little cooking table and made the recipe drawer shine.",
        traits={"paper", "wood"},
        allowed_suspects={"cook"},
        tags={"curry", "paper"},
    ),
    "saddle_bag": Hideout(
        id="saddle_bag",
        label="the saddle bag",
        place="on Pebble's parade saddle",
        found_line="The bag gave a gentle jingle, and there inside the soft leather pocket lay the bell.",
        reveal_line="The rhyme spell twinkled around Pebble's saddle and tugged at one bulging saddle bag.",
        traits={"dark", "leather"},
        allowed_suspects={"stable"},
        tags={"gallop", "pony"},
    ),
    "hay_loft": Hideout(
        id="hay_loft",
        label="the hay loft",
        place="above the stable door",
        found_line="Golden hay rustled, and the silver bell winked from a neat little nest high in the loft.",
        reveal_line="A silver echo hopped up the stable wall and rang above the hay loft.",
        traits={"hay", "hollow"},
        allowed_suspects={"stable"},
        tags={"gallop", "stable"},
    ),
    "paint_chest": Hideout(
        id="paint_chest",
        label="the paint chest",
        place="beside the float brushes",
        found_line="The lid lifted with a sigh, and the silver bell gleamed between two jars of moon-blue paint.",
        reveal_line="Moony glitter danced toward the brushes and settled on the paint chest latch.",
        traits={"dark", "wood", "paint"},
        allowed_suspects={"painter"},
        tags={"sperm_whale", "paint"},
    ),
    "whale_float": Hideout(
        id="whale_float",
        label="the sperm whale float",
        place="at the harbor lane",
        found_line="Inside the smiling float, among silver paper waves, the bell shone like a small trapped star.",
        reveal_line="The spell sailed toward the huge sperm whale float and lit its painted smile from nose to tail.",
        traits={"hollow", "paint"},
        allowed_suspects={"painter"},
        tags={"sperm_whale", "float"},
    ),
}

SPELLS = {
    "glow_rhyme": Spell(
        id="glow_rhyme",
        name="Glow Rhyme",
        chant='"Bell of silver, moonbeam bright, show the borrower to the light."',
        effect="A thin ribbon of gold light slipped away from the stage.",
        works_on={"dark", "paint"},
        tags={"magic", "rhyme", "glow"},
    ),
    "echo_rhyme": Spell(
        id="echo_rhyme",
        name="Echo Rhyme",
        chant='"Little bell, if you can hear, sing from the place that hides you near."',
        effect="A clear answering ring bounced across the fair.",
        works_on={"wood", "hollow"},
        tags={"magic", "rhyme", "echo"},
    ),
    "flutter_rhyme": Spell(
        id="flutter_rhyme",
        name="Flutter Rhyme",
        chant='"Paper, straw, or leather thing, lift and rustle, help us sing."',
        effect="A whispering breeze stirred sacks, cards, and ribbons.",
        works_on={"paper", "hay", "leather"},
        tags={"magic", "rhyme", "flutter"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lila", "Tess", "Ava", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Oli", "Ben", "Milo", "Toby"]
HELPERS = [
    ("Uncle Sorin", "man"),
    ("Aunt May", "woman"),
    ("Grandpa Ash", "man"),
    ("Miss Elowen", "woman"),
]
TRAITS = ["careful", "bright", "curious", "thoughtful", "gentle", "keen"]


def valid_combo(culprit_id: str, hideout_id: str, spell_id: str) -> bool:
    if culprit_id not in SUSPECTS or hideout_id not in HIDEOUTS or spell_id not in SPELLS:
        return False
    suspect = SUSPECTS[culprit_id]
    hideout = HIDEOUTS[hideout_id]
    spell = SPELLS[spell_id]
    if hideout_id not in suspect.can_hide:
        return False
    if culprit_id not in hideout.allowed_suspects:
        return False
    return bool(hideout.traits & spell.works_on)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for culprit_id in SUSPECTS:
        for hideout_id in HIDEOUTS:
            for spell_id in SPELLS:
                if valid_combo(culprit_id, hideout_id, spell_id):
                    combos.append((culprit_id, hideout_id, spell_id))
    return sorted(combos)


@dataclass
class StoryParams:
    culprit: str
    hideout: str
    spell: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
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


def _do_missing(world: World) -> None:
    bell = world.get("bell")
    bell.meters["missing"] += 1
    propagate(world, narrate=False)


def _do_cast_spell(world: World) -> None:
    world.facts["spell_cast"] = True
    propagate(world, narrate=False)


def opening(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["wonder"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At twilight, {hero.id} walked through the Harbor Hush Fair with {helper.id}, "
        f"{helper.pronoun('possessive')} old magic helper. Lanterns bobbed over the path, "
        f"and the whole fair felt ready for a mystery."
    )
    world.say(
        "Warm curry steam curled from Auntie Pema's stall, Pebble the parade pony stamped "
        "and gave one eager gallop by the rail, and a giant sperm whale balloon nodded over "
        "the harbor lane as if it wanted to hear the music too."
    )
    world.say(
        "In the middle of everything stood the Moonstage, where the silver Rhyme Bell was meant "
        "to ring and wake the evening lights."
    )


def discover_loss(world: World, hero: Entity, helper: Entity) -> None:
    _do_missing(world)
    world.say(
        f"But when {helper.id} lifted the velvet cloth, the bell was gone."
    )
    world.say(
        f'"Oh dear," {helper.id} murmured. "No bell, no rhyme. No rhyme, no lantern glow."'
    )
    world.say(
        f"{hero.id}'s {hero.attrs['trait']} eyes swept over the empty stand. This was no smashing, "
        f"no breaking, and no mean trick. Someone had borrowed the bell and hidden it in a hurry."
    )


def notice_clue(world: World, hero: Entity) -> None:
    clue = world.get("clue")
    text = clue.attrs.get("text", "")
    world.say(f"{hero.id} bent close. {text}")
    world.say(
        f'"A clue," {hero.pronoun()} whispered. "If we follow what the stand remembers, '
        f'we can learn who touched the bell last."'
    )


def question_suspects(world: World, hero: Entity) -> None:
    culprit_id = world.facts["culprit_id"]
    for sid in ["cook", "stable", "painter"]:
        suspect_cfg = SUSPECTS[sid]
        ent = world.get(sid)
        if sid == culprit_id:
            ent.memes["nervous"] += 1
        else:
            ent.memes["steady"] += 1
    world.say(
        f"{hero.id} and {world.get('helper').id} asked the fair workers one by one."
    )
    world.say(SUSPECTS["cook"].interview_line)
    world.say(SUSPECTS["stable"].interview_line)
    world.say(SUSPECTS["painter"].interview_line)
    culprit = SUSPECTS[culprit_id]
    world.say(culprit.worry_line)
    world.get("hero").memos if False else None  # no-op to keep linters calm about attribute use patterns


def deduce(world: World, hero: Entity, helper: Entity) -> None:
    culprit = SUSPECTS[world.facts["culprit_id"]]
    clue_line = world.get("clue").attrs["text"]
    if culprit.id == "cook":
        reason = "The curry dot belonged near the cooking tents, not the stable or the floats."
    elif culprit.id == "stable":
        reason = "Only the pony lane would leave straw and a tiny hoofprint by the stand."
    else:
        reason = "The blue fleck and the little sperm whale sticker pointed straight to the harbor float."
    hero.memes["certainty"] += 1
    world.say(
        f'"I know our next step," {hero.id} said. "{clue_line.split(".")[0]}. {reason}"'
    )
    world.say(
        f'{helper.id} nodded. "Then we do not need to scold first. We need a rhyme that can find."'
    )


def cast_spell(world: World, hero: Entity, helper: Entity, spell: Spell, hideout: Hideout) -> None:
    _do_cast_spell(world)
    world.say(
        f"{helper.id} took {hero.id}'s hand, and together they spoke the {spell.name} in a soft rhyme:"
    )
    world.say(spell.chant)
    world.say(spell.effect)
    world.say(hideout.reveal_line)
    world.say(hideout.found_line)


def confession(world: World, hero: Entity, culprit: Entity, helper: Entity) -> None:
    suspect = SUSPECTS[culprit.id]
    culprit.memes["honesty"] += 1
    culprit.memes["worry"] = 0.0
    world.say(
        f'{culprit.id} stepped forward at once. "{helper.id}," {culprit.pronoun()} said, '
        f'"I took the bell because {suspect.reason}"'
    )
    world.say(suspect.apology)
    world.say(
        f'{hero.id} looked at {culprit.id} and nodded. "You were trying to help," '
        f'{hero.pronoun()} said. "But mysteries grow when people borrow in secret."'
    )


def resolution(world: World, hero: Entity, helper: Entity, culprit: Entity) -> None:
    bell = world.get("bell")
    bell.meters["ringing"] += 1
    bell.meters["returned"] += 1
    culprit.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{culprit.id} carried the bell back with both hands. {helper.id} rang it once, clear and bright."
    )
    world.say(
        "At once the lanterns woke in little waves of gold. The curry stall glowed like warm sunset, "
        "Pebble's mane shone before the parade gallop, and even the giant sperm whale balloon flashed "
        "with silver stars along its side."
    )
    world.say(
        f"After that, the fair had a new rule that everyone liked: ask first, borrow second, and let "
        f"the magic rhyme stay merry. {hero.id} smiled up at the shining paths, pleased that the mystery "
        f"had ended with the truth and a kinder habit."
    )


def tell(
    culprit_cfg: Suspect,
    hideout_cfg: Hideout,
    spell_cfg: Spell,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[trait],
            attrs={"trait": trait},
            tags={"child"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
            traits=["calm", "magical"],
            attrs={},
            tags={"adult", "magic"},
        )
    )
    bell = world.add(
        Entity(
            id="bell",
            kind="thing",
            type="bell",
            label="the silver Rhyme Bell",
            role="bell",
            traits=["magic"],
            attrs={},
            tags={"magic", "rhyme"},
        )
    )
    world.add(
        Entity(
            id="clue",
            kind="thing",
            type="clue",
            label="the clue",
            role="clue",
            attrs={"text": ""},
            tags={"clue"},
        )
    )
    world.add(
        Entity(
            id="hideout",
            kind="thing",
            type="hideout",
            label=hideout_cfg.label,
            role="hideout",
            traits=sorted(hideout_cfg.traits),
            attrs={"place": hideout_cfg.place},
            tags=set(hideout_cfg.tags),
        )
    )
    for sid, scfg in SUSPECTS.items():
        world.add(
            Entity(
                id=sid,
                kind="character",
                type=scfg.type,
                label=scfg.label,
                role="suspect",
                traits=[],
                attrs={"role_label": scfg.role_label},
                tags=set(scfg.tags),
            )
        )

    world.facts.update(
        culprit_id=culprit_cfg.id,
        hideout_id=hideout_cfg.id,
        spell_id=spell_cfg.id,
        spell_cast=False,
        hero=hero,
        helper=helper,
        bell=bell,
        clue_text="",
        suspect_order=["cook", "stable", "painter"],
    )

    opening(world, hero, helper)
    world.para()
    discover_loss(world, hero, helper)
    notice_clue(world, hero)
    world.para()
    question_suspects(world, hero)
    deduce(world, hero, helper)
    world.para()
    cast_spell(world, hero, helper, spell_cfg, hideout_cfg)
    world.para()
    confession(world, hero, world.get(culprit_cfg.id), helper)
    resolution(world, hero, helper, world.get(culprit_cfg.id))

    world.facts.update(
        culprit=world.get(culprit_cfg.id),
        culprit_cfg=culprit_cfg,
        hideout=world.get("hideout"),
        hideout_cfg=hideout_cfg,
        spell_cfg=spell_cfg,
        solved=bell.meters["found"] >= THRESHOLD,
        returned=bell.meters["returned"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "curry": [
        (
            "What is curry?",
            "Curry is a dish with warm spices that can smell strong and cozy. Different curries can be mild or spicy, and people cook them in many ways.",
        )
    ],
    "gallop": [
        (
            "What does gallop mean?",
            "Gallop means a horse or pony runs in a fast, springy way. You can often hear it as a quick drumming of hooves.",
        )
    ],
    "sperm_whale": [
        (
            "What is a sperm whale?",
            "A sperm whale is a very large whale that lives in the ocean. It has a big square head and dives deep underwater.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair or group of words that sound alike at the end. Rhymes can make songs and spells easier to remember.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic in a story is a pretend power that can make surprising things happen. It helps a tale feel wondrous, even when the lesson is about ordinary kindness.",
        )
    ],
    "whodunit": [
        (
            "What is a whodunit?",
            "A whodunit is a mystery where people try to figure out who did something. The fun comes from noticing clues and putting them together.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand something hidden. It might be a mark, a smell, or an object left behind.",
        )
    ],
    "borrow": [
        (
            "Why should you ask before borrowing something?",
            "You should ask first because the thing belongs to someone else. Asking keeps trust strong and stops small mix-ups from turning into big worries.",
        )
    ],
}
KNOWLEDGE_ORDER = ["whodunit", "clue", "magic", "rhyme", "curry", "gallop", "sperm_whale", "borrow"]


def generation_prompts(world: World) -> list[str]:
    culprit = world.facts["culprit_cfg"]
    hideout = world.facts["hideout_cfg"]
    spell = world.facts["spell_cfg"]
    hero = world.facts["hero"]
    return [
        'Write a gentle whodunit for a 3-to-5-year-old about a missing magic bell at a fair. Include the words "sperm", "curry", and "gallop".',
        f"Tell a child-friendly mystery where {hero.id} notices a clue, uses a magic rhyme, and finds the missing bell in {hideout.label}.",
        f"Write a soft magical mystery where {culprit.label}, {culprit.role_label}, borrowed a bell without asking and must tell the truth kindly.",
        f"Create a rhyming whodunit at a harbor fair where a spell called the {spell.name} helps solve the case.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    culprit_cfg = world.facts["culprit_cfg"]
    hideout_cfg = world.facts["hideout_cfg"]
    spell_cfg = world.facts["spell_cfg"]
    clue_text = world.get("clue").attrs["text"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who helps {helper.id} solve a small fair mystery. They need to find the silver Rhyme Bell before the evening lights can wake.",
        ),
        (
            "What was missing?",
            "The silver Rhyme Bell was missing from the Moonstage. Without it, the lantern show could not begin.",
        ),
        (
            "What clue did they find?",
            f"They found this clue on the empty stand: {clue_text} That clue pointed them toward the person who had touched the bell last.",
        ),
        (
            f"How did {hero.id} solve the mystery?",
            f"{hero.id} listened to the suspects, matched the clue to the right part of the fair, and then used the {spell_cfg.name}. The rhyme spell revealed {hideout_cfg.label}, where the bell had been hidden.",
        ),
        (
            f"Why had {culprit_cfg.label} taken the bell?",
            f"{culprit_cfg.label} had not taken it to be mean. {culprit_cfg.reason[0].upper()}{culprit_cfg.reason[1:]}",
        ),
        (
            "How did the story end?",
            f"The bell was returned, the lanterns lit up, and the fair learned a better rule about borrowing. The ending proves the change because the mystery is solved with truth, and everyone can enjoy the glowing fair together again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    culprit = world.facts["culprit_cfg"]
    hideout = world.facts["hideout_cfg"]
    spell = world.facts["spell_cfg"]
    tags = {"whodunit", "clue", "borrow"} | set(culprit.tags) | set(hideout.tags) | set(spell.tags)
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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.traits:
            bits.append(f"traits={list(e.traits)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:11} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        culprit="cook",
        hideout="spice_crate",
        spell="glow_rhyme",
        hero_name="Mira",
        hero_gender="girl",
        helper_name="Uncle Sorin",
        helper_gender="man",
        trait="curious",
        seed=101,
    ),
    StoryParams(
        culprit="cook",
        hideout="recipe_drawer",
        spell="flutter_rhyme",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Aunt May",
        helper_gender="woman",
        trait="bright",
        seed=102,
    ),
    StoryParams(
        culprit="stable",
        hideout="saddle_bag",
        spell="flutter_rhyme",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Grandpa Ash",
        helper_gender="man",
        trait="thoughtful",
        seed=103,
    ),
    StoryParams(
        culprit="stable",
        hideout="hay_loft",
        spell="echo_rhyme",
        hero_name="Finn",
        hero_gender="boy",
        helper_name="Miss Elowen",
        helper_gender="woman",
        trait="keen",
        seed=104,
    ),
    StoryParams(
        culprit="painter",
        hideout="whale_float",
        spell="echo_rhyme",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Uncle Sorin",
        helper_gender="man",
        trait="gentle",
        seed=105,
    ),
]


def explain_rejection(culprit_id: str, hideout_id: str, spell_id: str) -> str:
    culprit = SUSPECTS.get(culprit_id)
    hideout = HIDEOUTS.get(hideout_id)
    spell = SPELLS.get(spell_id)
    if culprit is None or hideout is None or spell is None:
        return "(No story: one of the requested options does not exist in this world.)"
    if hideout_id not in culprit.can_hide or culprit_id not in hideout.allowed_suspects:
        return (
            f"(No story: {culprit.label} would not reasonably hide the bell in {hideout.label}. "
            f"Pick a hideout linked to that suspect's part of the fair.)"
        )
    if not (hideout.traits & spell.works_on):
        return (
            f"(No story: the {spell.name} does not fit {hideout.label}. "
            f"Choose a rhyme whose magic can work on {sorted(hideout.traits)}.)"
        )
    return "(No story: the requested combination is unreasonable.)"


ASP_RULES = r"""
suspect_can_hide(S,H) :- suspect(S), hideout(H), has_access(S,H).
spell_fits(H,Sp) :- hideout(H), spell(Sp), hideout_trait(H,T), works_on(Sp,T).
valid(S,H,Sp) :- suspect_can_hide(S,H), spell_fits(H,Sp).

solved(S,H,Sp) :- valid(S,H,Sp).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for hid in sorted(suspect.can_hide):
            lines.append(asp.fact("has_access", sid, hid))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        for sid in sorted(hideout.allowed_suspects):
            lines.append(asp.fact("has_access", sid, hid))
        for tr in sorted(hideout.traits):
            lines.append(asp.fact("hideout_trait", hid, tr))
    for spid, spell in SPELLS.items():
        lines.append(asp.fact("spell", spid))
        for tr in sorted(spell.works_on):
            lines.append(asp.fact("works_on", spid, tr))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_solved(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_suspect", params.culprit),
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_spell", params.spell),
            "chosen_valid :- valid(S,H,Sp), chosen_suspect(S), chosen_hideout(H), chosen_spell(Sp).",
            "solved_case :- chosen_valid.",
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show solved_case/0."))
    return bool(model)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny magical whodunit about a missing rhyme bell. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--culprit", choices=sorted(SUSPECTS))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--spell", choices=sorted(SPELLS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid culprit/hideout/spell combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run generation smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.hideout and args.spell and not valid_combo(args.culprit, args.hideout, args.spell):
        raise StoryError(explain_rejection(args.culprit, args.hideout, args.spell))

    combos = [
        c
        for c in valid_combos()
        if (args.culprit is None or c[0] == args.culprit)
        and (args.hideout is None or c[1] == args.hideout)
        and (args.spell is None or c[2] == args.spell)
    ]
    if not combos:
        culprit_id = args.culprit or next(iter(SUSPECTS))
        hideout_id = args.hideout or next(iter(HIDEOUTS))
        spell_id = args.spell or next(iter(SPELLS))
        raise StoryError(explain_rejection(culprit_id, hideout_id, spell_id))

    culprit_id, hideout_id, spell_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name, helper_gender = rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        culprit=culprit_id,
        hideout=hideout_id,
        spell=spell_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.culprit not in SUSPECTS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(No story: unknown hideout '{params.hideout}'.)")
    if params.spell not in SPELLS:
        raise StoryError(f"(No story: unknown spell '{params.spell}'.)")
    if not valid_combo(params.culprit, params.hideout, params.spell):
        raise StoryError(explain_rejection(params.culprit, params.hideout, params.spell))

    world = tell(
        culprit_cfg=SUSPECTS[params.culprit],
        hideout_cfg=HIDEOUTS[params.hideout],
        spell_cfg=SPELLS[params.spell],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_solved(params) != valid_combo(params.culprit, params.hideout, params.spell):
            bad += 1
    if bad == 0:
        print(f"OK: solved-case parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} solved-case checks differ.")

    try:
        smoke = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(smoke, trace=False, qa=True, header="### smoke")
        if not smoke.story.strip():
            raise StoryError("smoke story was empty")
        print("OK: generation/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show solved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (culprit, hideout, spell) combos:\n")
        for culprit_id, hideout_id, spell_id in combos:
            print(f"  {culprit_id:8} {hideout_id:13} {spell_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name}: culprit={p.culprit}, hideout={p.hideout}, spell={p.spell}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
