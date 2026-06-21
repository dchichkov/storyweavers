#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bra_magic_conflict_animal_story.py
==============================================================

A small animal-story world about a child who spots a clean bra on the laundry
line and wants to use it in a magical game. The conflict is about borrowing
without asking; the magic turns that choice into a real problem, and the ending
shows the safer, kinder way forward.

Run it
------
    python storyworlds/worlds/gpt-5.4/bra_magic_conflict_animal_story.py
    python storyworlds/worlds/gpt-5.4/bra_magic_conflict_animal_story.py --magic moon_glitter
    python storyworlds/worlds/gpt-5.4/bra_magic_conflict_animal_story.py --response chase
    python storyworlds/worlds/gpt-5.4/bra_magic_conflict_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/bra_magic_conflict_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bra_magic_conflict_animal_story.py --verify
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
SENSE_MIN = 2
BOLDNESS_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    species: str = ""
    age: int = 0
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt"}.get(self.type, self.type)


@dataclass
class PlayTheme:
    id: str
    scene: str
    dream: str
    use_for_bra: str
    safe_item: str
    finale: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicKind:
    id: str
    sparkle: str
    effect: str
    trouble: str
    strength: int
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.characters() if e.role in {"hero", "helper"}]

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


def _r_magic_lifts(world: World) -> list[str]:
    out: list[str] = []
    bra = world.entities.get("bra")
    if bra is None:
        return out
    if bra.meters["enchanted"] < THRESHOLD:
        return out
    sig = ("lift", "bra")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bra.meters["flying"] += 1
    line = world.get("line")
    basket = world.get("basket")
    line.meters["tangled"] += 1
    basket.meters["spilled"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__lift__")
    return out


CAUSAL_RULES = [
    Rule(name="magic_lifts", tag="physical", apply=_r_magic_lifts),
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
        for sent in produced:
            world.say(sent)
    return produced


def older_helper_stops(hero_age: int, helper_age: int, relation: str, trait: str) -> bool:
    if relation != "siblings":
        return False
    if helper_age <= hero_age:
        return False
    return trait in CAUTIOUS_TRAITS


def severity_of(magic: MagicKind, delay: int) -> int:
    return magic.strength + delay


def is_contained(response: Response, magic: MagicKind, delay: int) -> bool:
    return response.power >= severity_of(magic, delay)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combo(magic_id: str, response_id: str) -> bool:
    return magic_id in MAGICS and response_id in RESPONSES and RESPONSES[response_id].sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for mid in MAGICS:
        for rid, resp in RESPONSES.items():
            if resp.sense >= SENSE_MIN:
                combos.append((mid, rid))
    return combos


def explain_response(rid: str) -> str:
    if rid not in RESPONSES:
        return f"(No story: unknown response '{rid}'.)"
    resp = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={resp.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def predict_trouble(world: World, magic: MagicKind) -> dict:
    sim = world.copy()
    bra = sim.get("bra")
    bra.meters["enchanted"] += 1
    bra.meters["borrowed"] += 1
    propagate(sim, narrate=False)
    return {
        "flying": bra.meters["flying"] >= THRESHOLD,
        "tangled": sim.get("line").meters["tangled"] >= THRESHOLD,
        "spilled": sim.get("basket").meters["spilled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, theme: PlayTheme) -> None:
    world.say(
        f"In a sunny forest yard, {hero.id} the little {hero.species} and {helper.id} the "
        f"{helper.species} were playing {theme.scene}. They dreamed of {theme.dream}."
    )


def show_laundry(world: World, owner: Entity) -> None:
    world.say(
        f"On the clothesline nearby hung socks, aprons, and {owner.id}'s clean bra, white as a cloud."
    )


def temptation(world: World, hero: Entity, theme: PlayTheme) -> None:
    hero.memes["desire"] += 1
    hero.memes["boldness"] += 1
    world.say(
        f'{hero.id} pointed at the bra. "That would be perfect {theme.use_for_bra}," {hero.pronoun()} said.'
    )


def warning(world: World, helper: Entity, hero: Entity, owner: Entity, magic: MagicKind) -> None:
    pred = predict_trouble(world, magic)
    helper.memes["caution"] += 1
    world.facts["predicted"] = pred
    clause = ""
    if pred["tangled"] or pred["spilled"]:
        clause = " If magic touches it, the whole line could twist and the basket could tip."
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "It is {owner.id}\'s bra, '
        f'not a game thing. We should ask first.{clause}"'
    )


def defy(world: World, hero: Entity, helper: Entity, magic: MagicKind) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"Just one tiny spell," {hero.id} said. {helper.id} stayed close, but {hero.id} '
        f'dusted the bra with {magic.sparkle}.'
    )


def back_down(world: World, hero: Entity, helper: Entity, owner: Entity, theme: PlayTheme) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} looked at the bra, then at {helper.id}'s serious face, and let out a little sigh."
    )
    world.say(
        f'"You are right," {hero.pronoun()} said. "We should not borrow {owner.id}\'s bra without asking."'
    )
    world.say(
        f"They left it fluttering on the line and went to ask for {theme.safe_item} instead."
    )


def ignite_magic(world: World, hero: Entity, magic: MagicKind) -> None:
    bra = world.get("bra")
    bra.meters["borrowed"] += 1
    bra.meters["enchanted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At once, {magic.effect} The bra puffed and billowed like two white sails."
    )
    world.say(magic.trouble)


def alarm(world: World, helper: Entity, guardian: Entity) -> None:
    world.say(f'"{guardian.label_word.capitalize()}! Help!" cried {helper.id}.')


def rescue(world: World, guardian: Entity, response: Response) -> None:
    bra = world.get("bra")
    line = world.get("line")
    basket = world.get("basket")
    bra.meters["flying"] = 0.0
    bra.meters["enchanted"] = 0.0
    line.meters["tangled"] = 0.0
    basket.meters["spilled"] = 0.0
    world.say(
        f"{guardian.id} hurried over and {response.text}."
    )


def rescue_fail(world: World, guardian: Entity, response: Response) -> None:
    world.get("yard").meters["chase"] += 1
    world.say(
        f"{guardian.id} tried to help and {response.fail}."
    )
    world.say(
        "The enchanted bra skimmed over the currant bushes and dragged half the wash into the grass."
    )


def apology(world: World, hero: Entity, owner: Entity, magic: MagicKind) -> None:
    hero.memes["lesson"] += 1
    hero.memes["shame"] += 1
    world.say(
        f'{hero.id} folded {hero.pronoun("possessive")} ears. "I am sorry, {owner.id}," {hero.pronoun()} whispered.'
    )
    world.say(
        f'{owner.id} gave {hero.pronoun("object")} a gentle hug. "Thank you for telling the truth," '
        f'{owner.pronoun()} said. "{magic.lesson}"'
    )


def gift_safe_item(world: World, owner: Entity, hero: Entity, helper: Entity, theme: PlayTheme) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {owner.id} smiled and brought out {theme.safe_item}. It was old, sturdy, and meant for play."
    )
    world.say(
        f"Soon {hero.id} and {helper.id} were {theme.finale}, while the clean bra stayed right where it belonged on the line."
    )


def chase_end(world: World, owner: Entity, hero: Entity, helper: Entity, theme: PlayTheme) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"By the time they finally caught the bra, everyone was panting and the wash needed doing again."
    )
    world.say(
        f'{owner.id} was not cross, only tired. "{theme.safe_item.capitalize()} is for games. A clean bra is not," '
        f'{owner.pronoun()} said.'
    )
    world.say(
        f"After that, {hero.id} and {helper.id} always asked before using anything from the laundry line."
    )


def tell(
    theme: PlayTheme,
    magic: MagicKind,
    response: Response,
    hero_name: str = "Pip",
    hero_species: str = "rabbit",
    hero_type: str = "boy",
    helper_name: str = "Moss",
    helper_species: str = "mouse",
    helper_type: str = "girl",
    owner_name: str = "Aunt Bramble",
    owner_species: str = "badger",
    owner_type: str = "aunt",
    trait: str = "careful",
    relation: str = "siblings",
    hero_age: int = 5,
    helper_age: int = 7,
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        species=hero_species,
        role="hero",
        age=hero_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        species=helper_species,
        role="helper",
        age=helper_age,
        attrs={"relation": relation, "trait": trait},
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_type,
        species=owner_species,
        role="owner",
    ))
    world.add(Entity(id="yard", type="place", label="yard"))
    world.add(Entity(id="line", type="clothesline", label="clothesline"))
    world.add(Entity(id="basket", type="basket", label="laundry basket"))
    world.add(Entity(
        id="bra",
        type="bra",
        label="bra",
        phrase=f"{owner.id}'s clean bra",
        owner=owner.id,
        tags={"bra", "laundry"},
    ))
    hero.memes["boldness"] = BOLDNESS_INIT
    helper.memes["caution"] = 5.0 if trait in CAUTIOUS_TRAITS else 3.0

    introduce(world, hero, helper, theme)
    show_laundry(world, owner)

    world.para()
    temptation(world, hero, theme)
    warning(world, helper, hero, owner, magic)

    averted = older_helper_stops(hero_age, helper_age, relation, trait)
    if averted:
        back_down(world, hero, helper, owner, theme)
        world.para()
        gift_safe_item(world, owner, hero, helper, theme)
        outcome = "averted"
    else:
        defy(world, hero, helper, magic)
        world.para()
        ignite_magic(world, hero, magic)
        alarm(world, helper, owner)

        contained = is_contained(response, magic, delay)
        world.para()
        if contained:
            rescue(world, owner, response)
            apology(world, hero, owner, magic)
            world.para()
            gift_safe_item(world, owner, hero, helper, theme)
            outcome = "contained"
        else:
            rescue_fail(world, owner, response)
            chase_end(world, owner, hero, helper, theme)
            outcome = "runaway"

    world.facts.update(
        hero=hero,
        helper=helper,
        owner=owner,
        theme=theme,
        magic=magic,
        response=response,
        relation=relation,
        averted=(outcome == "averted"),
        outcome=outcome,
        delay=delay,
        severity=severity_of(magic, delay) if outcome != "averted" else 0,
        bra_borrowed=world.get("bra").meters["borrowed"] >= THRESHOLD or outcome == "averted",
    )
    return world


THEMES = {
    "cloud_ship": PlayTheme(
        id="cloud_ship",
        scene="a make-believe cloud ship",
        dream="sailing to the moonberry hill",
        use_for_bra="as the ship's moon-sail",
        safe_item="an old picnic cloth",
        finale="racing their cloud ship between daisy islands",
        tags={"play", "sharing"},
    ),
    "firefly_show": PlayTheme(
        id="firefly_show",
        scene="a firefly parade",
        dream="making the dusk sparkle brighter than lanterns",
        use_for_bra="as a grand parade banner",
        safe_item="a strip of yellow bunting",
        finale="waving their bright banner while fireflies blinked around them",
        tags={"play", "night"},
    ),
    "bird_wings": PlayTheme(
        id="bird_wings",
        scene="a bird-queen game",
        dream="gliding over the clover patch like swallows",
        use_for_bra="for magic wings",
        safe_item="a pair of soft costume wings",
        finale="swooping in little circles over the clover patch",
        tags={"play", "flight"},
    ),
}

MAGICS = {
    "moon_glitter": MagicKind(
        id="moon_glitter",
        sparkle="moon glitter",
        effect="silver dust flashed in the air, and sleepy moon-magic woke inside the cloth.",
        trouble="A wind curled under it, the clothesline jerked sideways, and the laundry basket tipped with a soft thump.",
        strength=2,
        lesson="Magic is not a good excuse for taking what is not yours",
        tags={"magic", "moon"},
    ),
    "thistledown": MagicKind(
        id="thistledown",
        sparkle="a pinch of thistledown charm",
        effect="The tiny fluff spun in circles, and the cloth leapt as if it had remembered how to dance.",
        trouble="The bra skimmed up from the line, snagged two socks, and sent clothespins pattering across the path.",
        strength=1,
        lesson="Even playful magic needs kind manners",
        tags={"magic", "wind"},
    ),
    "star_hum": MagicKind(
        id="star_hum",
        sparkle="a star-hum whisper",
        effect="A bright humming note rang out, and the cloth swelled full of sparkling air.",
        trouble="It bobbed over their heads, tangled the line, and showered clean washing into the grass.",
        strength=2,
        lesson="A borrowed thing must be asked for before it is touched",
        tags={"magic", "stars"},
    ),
}

RESPONSES = {
    "untie_song": Response(
        id="untie_song",
        sense=3,
        power=3,
        text="sang the old untie song, and the knots loosened while the magic folded itself away",
        fail="sang the untie song, but the spell had already blown too far across the yard",
        qa_text="used the untie song to calm the spell and loosen the knots",
        tags={"song", "magic_fix"},
    ),
    "dew_wand": Response(
        id="dew_wand",
        sense=3,
        power=4,
        text="touched the line with a dewdrop wand, and the sparkle fizzled into harmless mist",
        fail="tapped with the dew wand, but the bra was already skipping beyond the currant bushes",
        qa_text="used a dewdrop wand to turn the spell into harmless mist",
        tags={"wand", "magic_fix"},
    ),
    "wind_polite": Response(
        id="wind_polite",
        sense=2,
        power=2,
        text='bowed to the breeze and said, "Please rest now," and the wind settled enough for the bra to drift down',
        fail='asked the breeze politely to rest, but the gusts were still too wild to listen',
        qa_text='asked the wind to rest and brought the bra drifting down',
        tags={"wind", "magic_fix"},
    ),
    "chase": Response(
        id="chase",
        sense=1,
        power=1,
        text="ran after the bra with a washing basket",
        fail="ran after it with a washing basket, but chasing only stirred the spell faster",
        qa_text="ran after the flying bra with a basket",
        tags={"chase"},
    ),
}

NAMES = {
    "rabbit": ["Pip", "Mallow", "Nib", "Bramble"],
    "mouse": ["Moss", "Peep", "Tansy", "Dot"],
    "fox": ["Fern", "Russet", "Tumble", "Soot"],
    "squirrel": ["Hazel", "Nutmeg", "Skip", "Pine"],
}
SPECIES = ["rabbit", "mouse", "fox", "squirrel"]
TRAITS = ["careful", "steady", "sensible", "curious", "brisk", "bright"]


@dataclass
class StoryParams:
    theme: str
    magic: str
    response: str
    hero_name: str
    hero_species: str
    hero_type: str
    helper_name: str
    helper_species: str
    helper_type: str
    owner_name: str
    owner_species: str
    owner_type: str
    trait: str
    relation: str = "siblings"
    hero_age: int = 5
    helper_age: int = 7
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "bra": [
        (
            "What is a bra?",
            "A bra is a piece of clothing that grown-ups may wear under their clothes. Like other clothes, it belongs to someone and should not be borrowed without asking."
        )
    ],
    "laundry": [
        (
            "What is a clothesline for?",
            "A clothesline is a line where wet clothes hang to dry in the air. Clean laundry should be handled gently so it stays neat."
        )
    ],
    "magic": [
        (
            "Why can magic be a problem in stories?",
            "Magic can make small choices turn into big problems very quickly. That is why characters still need to be careful and kind."
        )
    ],
    "asking": [
        (
            "Why should you ask before using someone else's things?",
            "Asking shows respect for the other person and helps you learn whether the thing is meant for sharing. It can also stop accidents before they start."
        )
    ],
    "apology": [
        (
            "What makes an apology real?",
            "A real apology tells the truth about what happened and shows you understand the trouble you caused. Then you try to make things better."
        )
    ],
    "wand": [
        (
            "What is a wand in a make-believe story?",
            "A wand is a magic tool that can point, sparkle, or cast a spell. In stories, wise characters use it gently and carefully."
        )
    ],
    "song": [
        (
            "Why do songs calm characters in some stories?",
            "A soft song can help everyone slow down and listen. In magical tales, a calm song often helps settle wild feelings or wild spells."
        )
    ],
    "wind": [
        (
            "What is a gust of wind?",
            "A gust of wind is a quick, strong push of moving air. It can lift light things and blow them about."
        )
    ],
}
KNOWLEDGE_ORDER = ["bra", "laundry", "magic", "asking", "apology", "wand", "song", "wind"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    theme = f["theme"]
    magic = f["magic"]
    if f["outcome"] == "averted":
        return [
            f'Write a gentle animal story for a 3-to-5-year-old that includes the word "bra", a magical temptation, and an older helper who stops the trouble before it begins.',
            f"Tell a story where {hero.id} wants to use a clean bra in {theme.scene}, but {helper.id} insists they ask first and the ending stays warm and safe.",
            f'Write a child-facing animal tale where magic is present but kindness wins before the spell is used, and the lesson is about asking before borrowing.',
        ]
    if f["outcome"] == "contained":
        return [
            f'Write a short animal story that includes the word "bra", a small magical accident, and a calm grown-up who fixes the trouble.',
            f"Tell a forest-yard story where {hero.id} ignores a warning, uses {magic.sparkle} on a bra, and then learns to apologize after the magic is put right.",
            f'Write a TinyStories-style animal tale with clear conflict, a magical turn, and a kind ending that shows what changed.',
        ]
    return [
        f'Write an animal story that includes the word "bra", a magical mistake, and a lesson about borrowing without asking.',
        f"Tell a story where a child animal enchants a bra from the laundry line, the trouble runs across the yard, and everyone learns to ask first next time.",
        f'Write a gentle cautionary tale with magic, conflict, and a final lesson about respecting other people\'s things.',
    ]


def pair_noun(hero: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        return "two young siblings"
    return "two young friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    owner = f["owner"]
    theme = f["theme"]
    magic = f["magic"]
    response = f["response"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, helper, relation)}, {hero.id} the {hero.species} and {helper.id} the {helper.species}, and {owner.id} who was caring for the laundry."
        ),
        (
            "Why did the bra matter in the story?",
            f"The clean bra hanging on the line looked useful for {theme.scene}, so it became the thing {hero.id} wanted to borrow. That choice mattered because it belonged to {owner.id}, not to the game."
        ),
        (
            f"What warning did {helper.id} give?",
            f"{helper.id} said they should not use the bra without asking first. {helper.pronoun().capitalize()} also warned that magic could turn one borrowed thing into a bigger mess."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the problem solved before any spell happened?",
                f"{hero.id} listened to {helper.id} and backed away from the bra. Then they asked for {theme.safe_item}, which gave them something meant for play."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with the children playing their game using {theme.safe_item} instead of the bra. The ending image shows that the clean bra stayed safe on the line."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What went wrong after {hero.id} used the magic?",
                f"The spell made the bra lift and billow, and the laundry line and basket got into trouble. The magic turned a borrowing mistake into a real mess that frightened the children."
            )
        )
        qa.append(
            (
                f"How did {owner.id} fix the problem?",
                f"{owner.id} {response.qa_text}. That worked because the help came quickly enough to calm the spell before the whole yard turned into a chase."
            )
        )
        qa.append(
            (
                f"What did {hero.id} learn?",
                f"{hero.id} learned to tell the truth, say sorry, and ask before using something that belongs to someone else. The apology mattered because the trouble started with borrowing without permission."
            )
        )
    else:
        qa.append(
            (
                f"Why did the magic become such a big problem?",
                f"The spell got a head start, so the bra flew beyond the easy reach of the first fix. That made the yard messy and showed how quickly a playful choice can grow into hard work."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"Everyone finally caught the enchanted bra, but only after a tiring chase and more laundry to do. The ending proves the lesson because the children promised to ask before touching the wash again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bra", "laundry", "asking", "magic"}
    outcome = f["outcome"]
    if outcome == "contained":
        tags.add("apology")
    if f["response"].id == "dew_wand":
        tags.add("wand")
    if f["response"].id == "untie_song":
        tags.add("song")
    if f["magic"].id in {"moon_glitter", "thistledown", "star_hum"}:
        tags.add("wind")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.species:
            bits.append(f"species={ent.species}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="cloud_ship",
        magic="moon_glitter",
        response="dew_wand",
        hero_name="Pip",
        hero_species="rabbit",
        hero_type="boy",
        helper_name="Moss",
        helper_species="mouse",
        helper_type="girl",
        owner_name="Aunt Bramble",
        owner_species="badger",
        owner_type="aunt",
        trait="careful",
        relation="siblings",
        hero_age=5,
        helper_age=7,
        delay=0,
    ),
    StoryParams(
        theme="firefly_show",
        magic="thistledown",
        response="wind_polite",
        hero_name="Fern",
        hero_species="fox",
        hero_type="girl",
        helper_name="Pine",
        helper_species="squirrel",
        helper_type="boy",
        owner_name="Aunt Hazel",
        owner_species="rabbit",
        owner_type="aunt",
        trait="bright",
        relation="friends",
        hero_age=6,
        helper_age=6,
        delay=0,
    ),
    StoryParams(
        theme="bird_wings",
        magic="star_hum",
        response="wind_polite",
        hero_name="Nib",
        hero_species="rabbit",
        hero_type="boy",
        helper_name="Dot",
        helper_species="mouse",
        helper_type="girl",
        owner_name="Aunt Sedge",
        owner_species="fox",
        owner_type="aunt",
        trait="steady",
        relation="siblings",
        hero_age=7,
        helper_age=5,
        delay=1,
    ),
    StoryParams(
        theme="cloud_ship",
        magic="thistledown",
        response="untie_song",
        hero_name="Hazel",
        hero_species="squirrel",
        hero_type="girl",
        helper_name="Peep",
        helper_species="mouse",
        helper_type="girl",
        owner_name="Aunt Clover",
        owner_species="rabbit",
        owner_type="aunt",
        trait="sensible",
        relation="siblings",
        hero_age=4,
        helper_age=7,
        delay=0,
    ),
]


def outcome_of(params: StoryParams) -> str:
    if older_helper_stops(params.hero_age, params.helper_age, params.relation, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], MAGICS[params.magic], params.delay) else "runaway"


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(M, R) :- magic(M), response(R), sensible(R).

older_helper_stops :- relation(siblings), helper_age(HA), hero_age(HO), HA > HO, cautious_trait(T), trait(T).
severity(V) :- chosen_magic(M), strength(M, S), delay(D), V = S + D.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(averted) :- older_helper_stops.
outcome(contained) :- not older_helper_stops, contained.
outcome(runaway) :- not older_helper_stops, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid, magic in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("strength", mid, magic.strength))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_magic", params.magic),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolution at seed {s}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal-story world: a magical borrowing mistake with a bra on the laundry line."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the magic runs before help fully acts")
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from ASP")
    ap.add_argument("--verify", action="store_true", help="verify ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def pick_name(rng: random.Random, species: str, avoid: str = "") -> str:
    pool = [n for n in NAMES[species] if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and args.response in RESPONSES and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.magic is None or combo[0] == args.magic)
        and (args.response is None or combo[1] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    magic_id, response_id = rng.choice(sorted(combos))
    theme_id = args.theme or rng.choice(sorted(THEMES))
    relation = args.relation or rng.choice(["siblings", "friends"])
    hero_species = rng.choice(SPECIES)
    helper_species = rng.choice([s for s in SPECIES if s != hero_species] + [hero_species])
    hero_name = pick_name(rng, hero_species)
    helper_name = pick_name(rng, helper_species, avoid=hero_name)
    owner_species = rng.choice([s for s in SPECIES if s != hero_species] + [hero_species])
    owner_name = "Aunt " + rng.choice(["Bramble", "Hazel", "Clover", "Sedge", "Willow"])
    hero_type = rng.choice(["boy", "girl"])
    helper_type = rng.choice(["boy", "girl"])
    trait = rng.choice(TRAITS)
    hero_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        theme=theme_id,
        magic=magic_id,
        response=response_id,
        hero_name=hero_name,
        hero_species=hero_species,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_species=helper_species,
        helper_type=helper_type,
        owner_name=owner_name,
        owner_species=owner_species,
        owner_type="aunt",
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(No story: unknown theme '{params.theme}'.)")
    if params.magic not in MAGICS:
        raise StoryError(f"(No story: unknown magic '{params.magic}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        theme=THEMES[params.theme],
        magic=MAGICS[params.magic],
        response=RESPONSES[params.response],
        hero_name=params.hero_name,
        hero_species=params.hero_species,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        helper_species=params.helper_species,
        helper_type=params.helper_type,
        owner_name=params.owner_name,
        owner_species=params.owner_species,
        owner_type=params.owner_type,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (magic, response) combos:\n")
        for magic_id, response_id in combos:
            print(f"  {magic_id:12} {response_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.helper_name}: {p.magic} / {p.response} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
