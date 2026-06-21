#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bath_dim_wizard_blower_quest_sound_effects.py
========================================================================

A small storyworld about a child in a bath-dim bathroom who turns bath time
into a wizard mystery quest. A small bath treasure goes missing, eerie sounds
seem to point to a secret place, and a safe little blower helps reveal the
answer.

The world model prefers only sensible combinations:
- the missing object must be light enough to drift or peek out when air moves it
- the chosen blower must reach the hiding place
- the blower must be strong enough for that hiding place

Stories are state-driven: fear rises in the dim room, curiosity beats fear,
a clue sound directs the quest, and relief arrives only when the missing object
is actually found.

Run it
------
    python storyworlds/worlds/gpt-5.4/bath_dim_wizard_blower_quest_sound_effects.py
    python storyworlds/worlds/gpt-5.4/bath_dim_wizard_blower_quest_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4/bath_dim_wizard_blower_quest_sound_effects.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/bath_dim_wizard_blower_quest_sound_effects.py --qa
    python storyworlds/worlds/gpt-5.4/bath_dim_wizard_blower_quest_sound_effects.py --trace
    python storyworlds/worlds/gpt-5.4/bath_dim_wizard_blower_quest_sound_effects.py --json
    python storyworlds/worlds/gpt-5.4/bath_dim_wizard_blower_quest_sound_effects.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
class Quest:
    id: str
    title: str
    opening: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    sparkle: str
    light: bool = True
    floaty: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Hideout:
    id: str
    label: str
    phrase: str
    sound: str
    onomat: str
    reveal: str
    need: str = "surface"
    difficulty: int = 1
    spooky: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Blower:
    id: str
    label: str
    phrase: str
    puff: str
    supports: set[str] = field(default_factory=set)
    power: int = 1
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


QUESTS = {
    "moon": Quest(
        id="moon",
        title="the Moon Key Quest",
        opening="Tonight the tub was a silver lake and the soap dish was a wizard tower.",
        ending="The quest did not feel spooky anymore. It felt solved.",
        tags={"quest", "mystery"},
    ),
    "star": Quest(
        id="star",
        title="the Star Door Quest",
        opening="Tonight the tub was a secret pool and the folded towel looked like a hill guarding treasure.",
        ending="The little mystery had turned into a true answer, and that made the room feel warm again.",
        tags={"quest", "mystery"},
    ),
    "pearl": Quest(
        id="pearl",
        title="the Pearl Ripple Quest",
        opening="Tonight the bathwater looked like a quiet pond, and every bubble seemed to hide a clue.",
        ending="What had felt strange in the dark now felt simple and friendly.",
        tags={"quest", "mystery"},
    ),
}

ITEMS = {
    "foam_key": LostItem(
        id="foam_key",
        label="foam key",
        phrase="a little foam key",
        sparkle="golden at the edges",
        light=True,
        floaty=True,
        tags={"foam", "bath_toy", "light"},
    ),
    "silver_star": LostItem(
        id="silver_star",
        label="silver star",
        phrase="a tiny silver star",
        sparkle="shiny as a spoon",
        light=True,
        floaty=True,
        tags={"star", "bath_toy", "light"},
    ),
    "cork_boat": LostItem(
        id="cork_boat",
        label="cork boat",
        phrase="a tiny cork boat",
        sparkle="with a brave little mast",
        light=True,
        floaty=True,
        tags={"boat", "bath_toy", "float"},
    ),
    "soap_stone": LostItem(
        id="soap_stone",
        label="soap stone",
        phrase="a heavy soap stone",
        sparkle="smooth and gray",
        light=False,
        floaty=False,
        tags={"heavy"},
    ),
}

HIDEOUTS = {
    "bubble_cove": Hideout(
        id="bubble_cove",
        label="bubble cove",
        phrase="under a hill of bubbles at the far side of the tub",
        sound="a soft plip-plip from the bubbles",
        onomat="plip-plip",
        reveal="The bubbles parted, and the lost thing peeked out like a secret moon.",
        need="surface",
        difficulty=1,
        spooky=1,
        tags={"bubbles", "water", "sound"},
    ),
    "curtain_fold": Hideout(
        id="curtain_fold",
        label="curtain fold",
        phrase="in the fold of the shower curtain near the tub",
        sound="a hushy swish from the curtain",
        onomat="swish-swish",
        reveal="The curtain fluttered aside, and the lost thing slipped into sight.",
        need="curtain",
        difficulty=1,
        spooky=2,
        tags={"curtain", "sound"},
    ),
    "corner_ring": Hideout(
        id="corner_ring",
        label="corner ring",
        phrase="in a sleepy wet corner where the tub met the wall",
        sound="a tiny drip-tik from the corner",
        onomat="drip-tik",
        reveal="A wet glimmer showed in the corner, and there was the missing treasure.",
        need="corner",
        difficulty=2,
        spooky=2,
        tags={"corner", "sound"},
    ),
    "drain_grate": Hideout(
        id="drain_grate",
        label="drain grate",
        phrase="caught deep against the drain grate",
        sound="a low glug from the drain",
        onomat="glug-glug",
        reveal="Nothing light enough could come free from that deep place with a little puff of air.",
        need="deep",
        difficulty=3,
        spooky=3,
        tags={"drain", "sound"},
    ),
}

BLOWERS = {
    "shell_blower": Blower(
        id="shell_blower",
        label="shell blower",
        phrase="a little shell blower",
        puff="fwoo",
        supports={"surface"},
        power=1,
        tags={"blower", "shell"},
    ),
    "dragon_blower": Blower(
        id="dragon_blower",
        label="dragon blower",
        phrase="a dragon blower",
        puff="fffwhoosh",
        supports={"surface", "curtain", "corner"},
        power=2,
        tags={"blower", "dragon"},
    ),
    "reed_blower": Blower(
        id="reed_blower",
        label="reed blower",
        phrase="a long reed blower",
        puff="whooo",
        supports={"corner", "curtain"},
        power=2,
        tags={"blower", "reed"},
    ),
}


@dataclass
class StoryParams:
    quest: str
    item: str
    hideout: str
    blower: str
    hero: str
    gender: str
    parent: str
    mood: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
MOODS = ["brave", "curious", "careful", "quiet", "bright-eyed"]


def can_retrieve(item: LostItem, hideout: Hideout, blower: Blower) -> bool:
    return item.light and item.floaty and hideout.need in blower.supports and blower.power >= hideout.difficulty


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for quest_id in QUESTS:
        for item_id, item in ITEMS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                for blower_id, blower in BLOWERS.items():
                    if can_retrieve(item, hideout, blower):
                        combos.append((quest_id, item_id, hideout_id, blower_id))
    return combos


def explain_rejection(item: LostItem, hideout: Hideout, blower: Blower) -> str:
    if not item.light or not item.floaty:
        return (
            f"(No story: {item.phrase} is too heavy or sinky for a gentle blower quest. "
            f"The mystery only works with a light bath toy that can drift or peek free.)"
        )
    if hideout.need not in blower.supports:
        wants = hideout.need
        can = ", ".join(sorted(blower.supports))
        return (
            f"(No story: the {blower.label} cannot reach {hideout.phrase}. "
            f"This hiding place needs a {wants} puff, but that blower supports: {can}.)"
        )
    if blower.power < hideout.difficulty:
        return (
            f"(No story: the {blower.label} is too gentle for {hideout.phrase}. "
            f"That hiding place needs more puff to make the clue show.)"
        )
    return "(No story: this combination does not make a sensible mystery quest.)"


def introduce(world: World, hero: Entity, parent: Entity, quest: Quest) -> None:
    world.say(
        f"At bath time, {hero.id}'s {parent.label_word} left only the night-light on, "
        f"so the bathroom felt bath-dim and full of small shadows."
    )
    world.say(
        f"{hero.id} sat in the warm water with a towel cape on the stool nearby and whispered that "
        f"{hero.pronoun()} was a wizard tonight, beginning {quest.title}."
    )
    world.say(quest.opening)


def set_treasure(world: World, hero: Entity, item: LostItem) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In one hand {hero.pronoun()} held {item.phrase}, {item.sparkle}, and called it the treasure "
        f"that would unlock the end of the quest."
    )


def lose_item(world: World, hero: Entity, item: LostItem) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"Then a little splash bumped {hero.pronoun('possessive')} wrist, and the {item.label} was gone."
    )
    world.say(
        f"{hero.id} looked through the steam and the dimness. The treasure had vanished so neatly that "
        f"it felt less like losing and more like a mystery."
    )


def hear_clue(world: World, hero: Entity, hideout: Hideout) -> None:
    hero.memes["fear"] += float(hideout.spooky)
    hero.memes["curiosity"] += 2.0
    world.say(
        f"Just then came {hideout.sound}: {hideout.onomat}! In the bath-dim room, the sound seemed to "
        f"say that something was hiding."
    )


def react(world: World, hero: Entity, parent: Entity) -> None:
    if hero.memes["fear"] > hero.memes["curiosity"]:
        world.say(
            f"{hero.id} hugged {hero.pronoun('possessive')} knees. "
            f'"Did a bathroom ghost take it?" {hero.pronoun()} asked.'
        )
    else:
        world.say(
            f"{hero.id}'s eyes grew round. "
            f'"That sounds like a clue," {hero.pronoun()} whispered.'
        )
    world.say(
        f"{parent.label_word.capitalize()} smiled and sat beside the tub. "
        f'"Mysteries sound stranger before we know what they mean," {parent.pronoun()} said.'
    )


def choose_tool(world: World, hero: Entity, blower: Blower) -> None:
    hero.memes["agency"] += 1
    world.say(
        f"Beside the soap dish lay {blower.phrase}, the safe little blower from bath play. "
        f'{hero.id} lifted it like a wizard tool. "I can use the blower," {hero.pronoun()} said.'
    )


def solve(world: World, hero: Entity, hideout: Hideout, blower: Blower, item_ent: Entity) -> None:
    item_ent.meters["found"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 2.0
    hero.memes["joy"] += 1.0
    world.say(
        f"{hero.id} aimed the {blower.label} toward {hideout.phrase} and blew: {blower.puff}!"
    )
    world.say(hideout.reveal)
    world.say(
        f"{hero.id} reached out, caught the {item_ent.label}, and laughed so hard that the mystery broke apart."
    )


def close_story(world: World, hero: Entity, parent: Entity, quest: Quest, blower: Blower) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f'"So that was it," said {parent.label_word}. "Not a ghost. Just water, cloth, and a hiding place."'
    )
    world.say(
        f"{hero.id} held the treasure high over the tub like a wizard who had solved a riddle instead of fighting a monster."
    )
    world.say(
        f"Soon the room sounded different. The taps were only tiny taps, the curtain was only a curtain, "
        f"and even the {blower.label} looked more playful than mysterious."
    )
    world.say(quest.ending)


def tell(
    quest: Quest,
    item: LostItem,
    hideout: Hideout,
    blower: Blower,
    hero_name: str = "Lily",
    gender: str = "girl",
    parent_type: str = "mother",
    mood: str = "curious",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, role="hero", label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item_ent = world.add(Entity(id="item", kind="thing", type="toy", label=item.label, phrase=item.phrase))

    hero.attrs["mood"] = mood

    if mood in {"careful", "quiet"}:
        hero.memes["fear"] += 1.0
    else:
        hero.memes["curiosity"] += 1.0

    introduce(world, hero, parent, quest)
    set_treasure(world, hero, item)

    world.para()
    lose_item(world, hero, item)
    hear_clue(world, hero, hideout)
    react(world, hero, parent)

    world.para()
    choose_tool(world, hero, blower)
    solve(world, hero, hideout, blower, item_ent)

    world.para()
    close_story(world, hero, parent, quest, blower)

    world.facts.update(
        quest=quest,
        item_cfg=item,
        hideout=hideout,
        blower=blower,
        hero=hero,
        parent=parent,
        item=item_ent,
        found=item_ent.meters["found"] >= THRESHOLD,
        sound=hideout.onomat,
    )
    return world


KNOWLEDGE = {
    "bath_dim": [
        (
            "What does bath-dim mean?",
            "Bath-dim means the bathroom is kept softly dark, with only a little light. In a dim room, ordinary sounds and shadows can feel more mysterious.",
        )
    ],
    "wizard": [
        (
            "What is a wizard in a pretend game?",
            "A wizard in a pretend game is someone who imagines using spells, clues, and brave thinking. Children often use pretend wizard play to turn a small problem into an adventure.",
        )
    ],
    "blower": [
        (
            "What is a blower?",
            "A blower is something that pushes air out. A small toy blower can make light things flutter or drift.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem where you do not know the answer yet. You solve it by noticing clues and thinking carefully.",
        )
    ],
    "bubbles": [
        (
            "Why do bubbles hide things in bathwater?",
            "Bubbles pile up into soft white hills that are hard to see through. A small toy can sit under them without being noticed right away.",
        )
    ],
    "curtain": [
        (
            "Why can a shower curtain make spooky sounds?",
            "A shower curtain is light and floppy, so water drops and little puffs of air can make it rustle. In a dim room, that rustle can sound bigger than it really is.",
        )
    ],
    "corner": [
        (
            "Why do corners make little dripping sounds?",
            "Corners can collect tiny drops of water. When those drops slide or tap, they can make sharp little sounds.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bath_dim", "wizard", "blower", "mystery", "bubbles", "curtain", "corner"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    hideout = f["hideout"]
    blower = f["blower"]
    quest = f["quest"]
    return [
        (
            f'Write a short Mystery-style story for a 3-to-5-year-old that includes the words '
            f'"bath-dim," "wizard," and "blower," and turns bath time into a quest.'
        ),
        (
            f"Tell a gentle quest story where {hero.id} plays a wizard in a bath-dim bathroom, "
            f"hears {hideout.onomat}, and solves the mystery of a missing {item.label} with a {blower.label}."
        ),
        (
            f"Write a child-facing mystery with sound effects where a missing bath treasure is found in "
            f"{hideout.phrase}, and end with the room feeling safe again."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    item = f["item_cfg"]
    hideout = f["hideout"]
    blower = f["blower"]
    quest = f["quest"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who pretended to be a wizard in the bath, and {hero.pronoun('possessive')} {pw}, who helped {hero.pronoun('object')} stay calm. Together they solved a small bath-time mystery.",
        ),
        (
            "What was the quest?",
            f"The quest was {quest.title}, and the missing treasure was {item.phrase}. The whole game turned bath time into a mystery to solve.",
        ),
        (
            "Why did the room feel mysterious?",
            f"The bathroom was bath-dim, so the little shadows and sounds seemed bigger than usual. That made the missing {item.label} feel like part of a real mystery.",
        ),
        (
            "What clue did the child hear?",
            f"{hero.id} heard {hideout.sound}: {hideout.onomat}. That sound pointed toward {hideout.phrase}, so the clue came from the hiding place itself.",
        ),
        (
            f"How did {hero.id} find the {item.label}?",
            f"{hero.id} used the {blower.label} and blew toward {hideout.phrase}. The little puff moved what was hiding it, and the {item.label} came into sight.",
        ),
        (
            "Was there really a ghost?",
            f"No. The mystery only felt spooky at first because the room was dim and the sound was strange. In the end, it was just an ordinary hiding place making an ordinary noise.",
        ),
        (
            "How did the story end?",
            f"{hero.id} found the treasure and felt relieved and brave. By the end, the taps, curtain, and blower all seemed friendly again because the mystery had been explained.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bath_dim", "wizard", "blower", "mystery"}
    hideout = f["hideout"]
    if hideout.id == "bubble_cove":
        tags.add("bubbles")
    if hideout.id == "curtain_fold":
        tags.add("curtain")
    if hideout.id == "corner_ring":
        tags.add("corner")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="moon",
        item="foam_key",
        hideout="bubble_cove",
        blower="shell_blower",
        hero="Lily",
        gender="girl",
        parent="mother",
        mood="curious",
    ),
    StoryParams(
        quest="star",
        item="silver_star",
        hideout="curtain_fold",
        blower="dragon_blower",
        hero="Ben",
        gender="boy",
        parent="father",
        mood="careful",
    ),
    StoryParams(
        quest="pearl",
        item="cork_boat",
        hideout="corner_ring",
        blower="reed_blower",
        hero="Maya",
        gender="girl",
        parent="mother",
        mood="brave",
    ),
]


ASP_RULES = r"""
retrievable(I, H, B) :- light(I), floaty(I), needs(H, N), supports(B, N), power(B, P), difficulty(H, D), P >= D.
valid(Q, I, H, B) :- quest(Q), item(I), hideout(H), blower(B), retrievable(I, H, B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for quest_id in QUESTS:
        lines.append(asp.fact("quest", quest_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.light:
            lines.append(asp.fact("light", item_id))
        if item.floaty:
            lines.append(asp.fact("floaty", item_id))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        lines.append(asp.fact("needs", hideout_id, hideout.need))
        lines.append(asp.fact("difficulty", hideout_id, hideout.difficulty))
    for blower_id, blower in BLOWERS.items():
        lines.append(asp.fact("blower", blower_id))
        for support in sorted(blower.supports):
            lines.append(asp.fact("supports", blower_id, support))
        lines.append(asp.fact("power", blower_id, blower.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bath-dim wizard mystery quest with a blower and sound effects."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--blower", choices=BLOWERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.hideout and args.blower:
        item = ITEMS[args.item]
        hideout = HIDEOUTS[args.hideout]
        blower = BLOWERS[args.blower]
        if not can_retrieve(item, hideout, blower):
            raise StoryError(explain_rejection(item, hideout, blower))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.item is None or combo[1] == args.item)
        and (args.hideout is None or combo[2] == args.hideout)
        and (args.blower is None or combo[3] == args.blower)
    ]
    if not combos:
        if args.item and args.hideout and args.blower:
            raise StoryError(
                explain_rejection(ITEMS[args.item], HIDEOUTS[args.hideout], BLOWERS[args.blower])
            )
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, item_id, hideout_id, blower_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    mood = rng.choice(MOODS)

    return StoryParams(
        quest=quest_id,
        item=item_id,
        hideout=hideout_id,
        blower=blower_id,
        hero=name,
        gender=gender,
        parent=parent,
        mood=mood,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.blower not in BLOWERS:
        raise StoryError(f"(Unknown blower: {params.blower})")

    item = ITEMS[params.item]
    hideout = HIDEOUTS[params.hideout]
    blower = BLOWERS[params.blower]
    if not can_retrieve(item, hideout, blower):
        raise StoryError(explain_rejection(item, hideout, blower))

    world = tell(
        quest=QUESTS[params.quest],
        item=item,
        hideout=hideout,
        blower=blower,
        hero_name=params.hero,
        gender=params.gender,
        parent_type=params.parent,
        mood=params.mood,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, item, hideout, blower) combos:\n")
        for quest_id, item_id, hideout_id, blower_id in combos:
            print(f"  {quest_id:6} {item_id:12} {hideout_id:13} {blower_id}")
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
            header = f"### {p.hero}: {p.quest} with {p.item} in {p.hideout} using {p.blower}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
