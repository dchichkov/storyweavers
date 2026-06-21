#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jumble_lesson_learned_mystery_to_solve_whodunit.py
=============================================================================

A standalone story world about a small child-facing whodunit: a treasured object
goes missing in a cheerful jumble, a young sleuth follows a clue, and the ending
teaches that it is better to look carefully and ask kindly than to blame too fast.

Run it
------
    python storyworlds/worlds/gpt-5.4/jumble_lesson_learned_mystery_to_solve_whodunit.py
    python storyworlds/worlds/gpt-5.4/jumble_lesson_learned_mystery_to_solve_whodunit.py --place classroom --item notebook --culprit friend
    python storyworlds/worlds/gpt-5.4/jumble_lesson_learned_mystery_to_solve_whodunit.py --place classroom --item medal --culprit puppy
    python storyworlds/worlds/gpt-5.4/jumble_lesson_learned_mystery_to_solve_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/jumble_lesson_learned_mystery_to_solve_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/jumble_lesson_learned_mystery_to_solve_whodunit.py --verify
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

# Make shared result containers importable when run directly from this nested dir.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HASTY_TRAITS = {"hasty", "impulsive"}
PATIENT_TRAITS = {"patient", "careful", "curious"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"dog", "puppy", "cat", "kitten"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    event: str
    spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    tag: str
    event_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    name: str
    type: str
    label: str
    desire_tag: str
    clue: str
    clue_kind: str
    spot: str
    move_text: str
    explanation: str
    apology: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    find_text: str
    tidy_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    culprit: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_hidden(world: World) -> list[str]:
    item = world.get("item")
    room = world.get("room")
    if item.meters["misplaced"] >= THRESHOLD and room.meters["jumble"] >= THRESHOLD:
        sig = ("hidden", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["hidden"] += 1
    return []


def _r_worry(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if hero.memes["wants_item"] >= THRESHOLD and item.meters["hidden"] >= THRESHOLD:
        sig = ("worry", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    out: list[str] = []
    for eid in ("hero", "friend", "culprit"):
        if eid not in world.entities:
            continue
        ent = world.get(eid)
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["relief"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="hidden", tag="physical", apply=_r_hidden),
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                # harmlessly continue; fixpoint is governed by fired signatures
                pass
        before = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) > before:
            changed = True
    if narrate:
        for text in produced:
            world.say(text)
    return produced


PLACES = {
    "living_room": Place(
        id="living_room",
        label="the living room",
        opening="The living room was full of cushions, picture books, and toy blocks in a happy jumble.",
        event="family story time",
        spots={"basket", "fort", "cushion"},
        tags={"room", "tidy"},
    ),
    "classroom": Place(
        id="classroom",
        label="the classroom",
        opening="The classroom was bright, and the reading corner had grown into a cheerful jumble of crayons, papers, and half-built projects.",
        event="show-and-tell circle",
        spots={"book_bin", "cubby", "art_shelf"},
        tags={"school", "tidy"},
    ),
    "bedroom": Place(
        id="bedroom",
        label="the bedroom",
        opening="The bedroom floor was a patchwork of blankets, blocks, and socks, all in one cozy jumble.",
        event="bedtime treasure parade",
        spots={"basket", "fort", "toy_box"},
        tags={"room", "tidy"},
    ),
}

ITEMS = {
    "ribbon": Item(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon with a satin loop",
        tag="soft",
        event_use="wear on the front of the parade coat",
        tags={"soft", "award"},
    ),
    "scarf": Item(
        id="scarf",
        label="yellow scarf",
        phrase="a yellow scarf with tiny suns on it",
        tag="soft",
        event_use="wrap around the shoulders for the big entrance",
        tags={"soft", "clothes"},
    ),
    "medal": Item(
        id="medal",
        label="gold medal",
        phrase="a gold medal that clinked when it moved",
        tag="shiny",
        event_use="hang proudly for everyone to see",
        tags={"shiny", "award"},
    ),
    "badge": Item(
        id="badge",
        label="star badge",
        phrase="a star badge with a bright silver pin",
        tag="shiny",
        event_use="pin on before the mystery game begins",
        tags={"shiny", "special"},
    ),
    "notebook": Item(
        id="notebook",
        label="red notebook",
        phrase="a red notebook full of careful drawings",
        tag="flat",
        event_use="show the pictures during the circle",
        tags={"paper", "drawing"},
    ),
    "map": Item(
        id="map",
        label="treasure map",
        phrase="a treasure map folded into neat squares",
        tag="flat",
        event_use="unfold at the very start of the hunt",
        tags={"paper", "adventure"},
    ),
}

SPOTS = {
    "basket": Spot(
        id="basket",
        label="basket by the rug",
        phrase="the basket by the rug",
        find_text="nestled under a blanket in the basket by the rug",
        tidy_fix="They gave the basket one clear job: soft things only.",
        tags={"basket", "tidy"},
    ),
    "fort": Spot(
        id="fort",
        label="blanket fort",
        phrase="the blanket fort",
        find_text="propped proudly inside the blanket fort",
        tidy_fix="They folded the blankets and left one fort shelf just for building pieces.",
        tags={"fort", "tidy"},
    ),
    "cushion": Spot(
        id="cushion",
        label="sofa cushion",
        phrase="the sofa cushion",
        find_text="slipped under the sofa cushion where only a corner peeked out",
        tidy_fix="They patted the cushions flat and made a small tray for special things.",
        tags={"sofa", "tidy"},
    ),
    "book_bin": Spot(
        id="book_bin",
        label="book bin",
        phrase="the book bin",
        find_text="resting between two tall picture books in the book bin",
        tidy_fix="They put labels on the bins so papers would not disappear into the wrong one.",
        tags={"books", "tidy"},
    ),
    "cubby": Spot(
        id="cubby",
        label="cubby",
        phrase="the cubby",
        find_text="tucked into the cubby behind a stack of folders",
        tidy_fix="They straightened the cubby and promised to say out loud when something was put away for safekeeping.",
        tags={"school", "tidy"},
    ),
    "art_shelf": Spot(
        id="art_shelf",
        label="art shelf",
        phrase="the art shelf",
        find_text="lying flat on the art shelf beneath a pile of colored paper",
        tidy_fix="They stacked the paper neatly and left a special tray for important drawings.",
        tags={"art", "tidy"},
    ),
    "toy_box": Spot(
        id="toy_box",
        label="toy box",
        phrase="the toy box",
        find_text="hidden in the toy box under a cardboard dragon",
        tidy_fix="They sorted the toy box so treasures would not vanish under the toys again.",
        tags={"toys", "tidy"},
    ),
}

CULPRITS = {
    "puppy": Culprit(
        id="puppy",
        name="Pip",
        type="puppy",
        label="Pip the puppy",
        desire_tag="soft",
        clue="tiny muddy paw prints",
        clue_kind="pawprints",
        spot="basket",
        move_text="had trotted off with it to make his bed feel softer",
        explanation="Pip had found something soft and dragged it away because he was making a cozy little nest.",
        apology="Pip wagged hard as if he wished he could say sorry in words.",
        tags={"dog", "clue", "soft"},
    ),
    "brother": Culprit(
        id="brother",
        name="Owen",
        type="boy",
        label="Owen",
        desire_tag="shiny",
        clue="a crooked trail of toy blocks leading away",
        clue_kind="blocks",
        spot="fort",
        move_text="had borrowed it as the shining prize for his fort",
        explanation="Owen had seen the bright shine and thought it would make the fort look grander for one minute.",
        apology="Owen's cheeks turned pink, and he said he should have asked first.",
        tags={"sibling", "clue", "shiny"},
    ),
    "friend": Culprit(
        id="friend",
        name="Mina",
        type="girl",
        label="Mina",
        desire_tag="flat",
        clue="a paper star sticker stuck to the shelf edge",
        clue_kind="sticker",
        spot="book_bin",
        move_text="had tucked it away while tidying too fast",
        explanation="Mina had tried to help by putting the flat paper thing somewhere safe, but in the jumble she forgot to tell anyone where it went.",
        apology="Mina bit her lip and said helping is better when you also tell people what you moved.",
        tags={"friend", "clue", "paper"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Omar"]
TRAITS = ["careful", "curious", "patient", "hasty", "impulsive"]


def valid_combo(place_id: str, item_id: str, culprit_id: str) -> bool:
    if place_id not in PLACES or item_id not in ITEMS or culprit_id not in CULPRITS:
        return False
    place = PLACES[place_id]
    item = ITEMS[item_id]
    culprit = CULPRITS[culprit_id]
    return item.tag == culprit.desire_tag and culprit.spot in place.spots


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for item_id in ITEMS:
            for culprit_id in CULPRITS:
                if valid_combo(place_id, item_id, culprit_id):
                    combos.append((place_id, item_id, culprit_id))
    return combos


def is_hasty(trait: str) -> bool:
    return trait in HASTY_TRAITS


def outcome_of(params: StoryParams) -> str:
    return "quick_blame" if is_hasty(params.hero_trait) else "careful_solve"


def explain_rejection(place_id: str, item_id: str, culprit_id: str) -> str:
    place = PLACES.get(place_id)
    item = ITEMS.get(item_id)
    culprit = CULPRITS.get(culprit_id)
    if place is None or item is None or culprit is None:
        return "(No story: one of the requested options is unknown.)"
    if item.tag != culprit.desire_tag:
        return (
            f"(No story: {culprit.label} would not naturally take {item.phrase}. "
            f"This world only allows clues that fit the culprit's reason for moving the item.)"
        )
    if culprit.spot not in place.spots:
        return (
            f"(No story: {culprit.label}'s usual hiding place is {SPOTS[culprit.spot].phrase}, "
            f"but that does not belong in {place.label}.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
compatible(C, I) :- culprit(C), item(I), desire(C, T), item_tag(I, T).
valid(P, I, C) :- place(P), compatible(C, I), uses_spot(C, S), has_spot(P, S).

quick_blame :- chosen_trait(T), hasty_trait(T).
careful_solve :- chosen_trait(T), not hasty_trait(T).

outcome(quick_blame) :- quick_blame.
outcome(careful_solve) :- careful_solve.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for spot in sorted(place.spots):
            lines.append(asp.fact("has_spot", place_id, spot))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_tag", item_id, item.tag))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("desire", culprit_id, culprit.desire_tag))
        lines.append(asp.fact("uses_spot", culprit_id, culprit.spot))
    for trait in sorted(HASTY_TRAITS):
        lines.append(asp.fact("hasty_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_trait", params.hero_trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    found = asp.atoms(model, "outcome")
    return found[0][0] if found else "?"


def predict_missing(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {"hidden": item.meters["hidden"] >= THRESHOLD}


def introduce(world: World, hero: Entity, parent: Entity, item: Entity, item_cfg: Item, place: Place) -> None:
    trait = hero.traits[0] if hero.traits else "curious"
    world.say(f"{place.opening}")
    world.say(
        f"{hero.id} was a {trait} little {hero.type} who was getting ready for {place.event}."
    )
    world.say(
        f"Most of all, {hero.pronoun()} wanted {item_cfg.event_use}. "
        f"That is why {item.phrase} mattered so much."
    )
    world.say(
        f'{hero.id} set it down for one tiny moment while {parent.label_word} said, "Shoes first, then the fun part."'
    )


def cause_misplacing(world: World, culprit_ent: Entity, item: Entity, culprit_cfg: Culprit) -> None:
    room = world.get("room")
    room.meters["jumble"] += 1
    item.meters["misplaced"] += 1
    culprit_ent.memes["secret"] += 1
    propagate(world, narrate=False)
    world.facts["predicted_hidden"] = predict_missing(world)["hidden"]


def discover(world: World, hero: Entity, friend: Entity, item: Entity, item_cfg: Item) -> None:
    hero.memes["wants_item"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {hero.id} came back, {item_cfg.phrase} was gone."
    )
    if world.get("room").meters["jumble"] >= THRESHOLD:
        world.say(
            f"The whole room looked like a jumble of good intentions, and now the missing thing seemed to have melted right into it."
        )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f'{hero.id} took a breath. "This is a real mystery," {hero.pronoun()} whispered.'
        )
    friend.memes["helpfulness"] += 1
    world.say(
        f'{friend.id} came close and said, "Then let\'s be detectives and look for a clue."'
    )


def wrong_guess(world: World, hero: Entity, friend: Entity, culprit_cfg: Culprit) -> Optional[str]:
    candidates = []
    if culprit_cfg.id != "friend":
        candidates.append(friend.id)
    if culprit_cfg.id != "brother":
        candidates.append("Owen")
    if culprit_cfg.id != "puppy":
        candidates.append("Pip")
    guess = candidates[0] if candidates else None
    if guess is None:
        return None
    hero.memes["embarrassment"] += 1
    world.say(
        f'"Maybe {guess} did it," {hero.id} said too quickly.'
    )
    world.say(
        f'But even as the words came out, {hero.pronoun()} looked around again and knew one fast guess was not a real answer.'
    )
    return guess


def inspect_clue(world: World, hero: Entity, culprit_cfg: Culprit) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"Then {hero.id} noticed {culprit_cfg.clue}."
    )
    if culprit_cfg.clue_kind == "pawprints":
        world.say(
            "They were too small for grown-up shoes and too muddy to belong to a stack of books."
        )
    elif culprit_cfg.clue_kind == "blocks":
        world.say(
            "The blocks leaned in one direction, almost like a little arrow pointing the way."
        )
    else:
        world.say(
            "It was the kind of tiny paper sign a careful helper might leave behind without meaning to."
        )
    world.facts["clue_seen"] = True


def deduce(world: World, hero: Entity, culprit_ent: Entity, culprit_cfg: Culprit, spot: Spot) -> None:
    culprit_ent.memes["suspected"] += 1
    world.say(
        f'{hero.id} narrowed {hero.pronoun("possessive")} eyes. "I know who moved it," {hero.pronoun()} said.'
    )
    if culprit_cfg.id == "puppy":
        world.say(
            f'"Those paw prints lead toward {spot.phrase}. It has to be {culprit_cfg.label}."'
        )
    elif culprit_cfg.id == "brother":
        world.say(
            f'"The block trail goes straight to {spot.phrase}. It has to be {culprit_cfg.label}."'
        )
    else:
        world.say(
            f'"A paper star by the shelf and a paper thing gone missing? Someone tidied too fast. It has to be {culprit_cfg.label}."'
        )


def find_item(world: World, hero: Entity, item: Entity, item_cfg: Item, culprit_ent: Entity, culprit_cfg: Culprit, spot: Spot) -> None:
    item.meters["found"] += 1
    item.meters["hidden"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"They hurried to {spot.phrase}, and there was {item_cfg.phrase}, {spot.find_text}."
    )
    world.say(
        f"So that was it: {culprit_cfg.label} {culprit_cfg.move_text}."
    )
    culprit_ent.memes["guilt"] += 1


def resolve(world: World, hero: Entity, friend: Entity, culprit_ent: Entity, culprit_cfg: Culprit, spot: Spot, false_guess: Optional[str]) -> None:
    world.say(
        f"{culprit_cfg.explanation}"
    )
    world.say(
        f"{culprit_cfg.apology}"
    )
    if false_guess is not None:
        hero.memes["lesson"] += 1
        world.say(
            f'{hero.id} gave a small nod. "I should not have guessed so fast," {hero.pronoun()} said. "A clue is kinder than a blame."'
        )
    else:
        hero.memes["lesson"] += 1
        world.say(
            f'{hero.id} smiled. "I am glad we looked carefully first," {hero.pronoun()} said. "That helped us find the true answer without hurting feelings."'
        )
    friend.memes["trust"] += 1
    culprit_ent.memes["trust"] += 1
    world.say(
        spot.tidy_fix
    )


def ending(world: World, hero: Entity, item_cfg: Item, place: Place) -> None:
    hero.memes["joy"] += 1
    if place.id == "classroom":
        image = "the bins stood straight, and the clue-hunters sat in a neat circle at last"
    elif place.id == "bedroom":
        image = "the blankets were folded, and even the toy box looked ready to keep secrets properly"
    else:
        image = "the cushions were puffed smooth, and the room no longer swallowed little treasures"
    world.say(
        f"Soon {hero.id} was ready to {item_cfg.event_use}, and {image}."
    )
    world.say(
        "The mystery was solved, the jumble was gentler, and everyone remembered that careful looking beats quick blaming."
    )


def tell(
    place: Place,
    item_cfg: Item,
    culprit_cfg: Culprit,
    hero_name: str,
    hero_gender: str,
    hero_trait: str,
    friend_name: str,
    friend_gender: str,
    parent_type: str,
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[hero_trait],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        phrase=friend_name,
        role="friend",
        traits=["helpful"],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    culprit_ent = world.add(Entity(
        id="culprit",
        kind="character",
        type=culprit_cfg.type,
        label=culprit_cfg.name,
        phrase=culprit_cfg.label,
        role="culprit",
        traits=["secretive"],
        tags=set(culprit_cfg.tags),
    ))
    item = world.add(Entity(
        id="item",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        tags=set(item_cfg.tags),
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=place.label,
        phrase=place.label,
        tags=set(place.tags),
    ))
    world.facts["hero_name"] = hero_name
    world.facts["friend_name"] = friend_name

    spot = SPOTS[culprit_cfg.spot]

    introduce(world, hero, parent, item, item_cfg, place)
    world.para()
    cause_misplacing(world, culprit_ent, item, culprit_cfg)
    discover(world, hero, friend, item, item_cfg)
    false_guess = None
    if is_hasty(hero_trait):
        false_guess = wrong_guess(world, hero, friend, culprit_cfg)
    inspect_clue(world, hero, culprit_cfg)
    world.para()
    deduce(world, hero, culprit_ent, culprit_cfg, spot)
    find_item(world, hero, item, item_cfg, culprit_ent, culprit_cfg, spot)
    resolve(world, hero, friend, culprit_ent, culprit_cfg, spot, false_guess)
    world.para()
    ending(world, hero, item_cfg, place)

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        spot=spot,
        hero=hero,
        friend=friend,
        parent=parent,
        culprit=culprit_ent,
        false_guess=false_guess,
        outcome="quick_blame" if false_guess else "careful_solve",
        clue=culprit_cfg.clue,
        item_found=item.meters["found"] >= THRESHOLD,
        lesson_learned=hero.memes["lesson"] >= THRESHOLD,
    )
    hero.label = hero_name
    friend.label = friend_name
    parent.label = "the parent"
    culprit_ent.label = culprit_cfg.name
    return world


KNOWLEDGE = {
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out. Detectives look for clues instead of guessing too fast."
    )],
    "dog": [(
        "Why do puppies carry soft things away sometimes?",
        "Puppies often carry soft things because they like making a cozy nest or playing with something gentle in their mouths."
    )],
    "sibling": [(
        "Why should you ask before borrowing something?",
        "You should ask before borrowing because the other person may need it or may worry when it is gone. Asking keeps trust strong."
    )],
    "friend": [(
        "Why is it important to tell someone when you move their things?",
        "If you move someone's things without telling them, they may think the thing is lost. Telling people helps everyone feel calm and included."
    )],
    "tidy": [(
        "Why do labels and tidy bins help?",
        "Labels and tidy bins make it easier to know where things belong. That means important things are easier to find."
    )],
    "paper": [(
        "Why can paper things get lost in a messy room?",
        "Paper things are flat and light, so they can slide under other papers or books very easily when a room is messy."
    )],
    "shiny": [(
        "Why do shiny things catch your eye?",
        "Shiny things reflect light, so they sparkle or glint. That makes them easy to notice and tempting to pick up."
    )],
    "soft": [(
        "Why do soft things feel cozy?",
        "Soft things feel gentle against your skin or fur, so they often make people and pets feel comfortable and safe."
    )],
}
KNOWLEDGE_ORDER = ["clue", "dog", "sibling", "friend", "tidy", "paper", "shiny", "soft"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    place = f["place"]
    base = (
        f'Write a short whodunit for a 3-to-5-year-old that includes the word "jumble", '
        f'a missing {item.label}, and a gentle lesson about looking for clues before blaming.'
    )
    if f["outcome"] == "quick_blame":
        return [
            base,
            f"Tell a tiny detective story where {f['hero_name']} makes one hasty guess in {place.label}, then notices {culprit.clue} and discovers that {culprit.label} moved the {item.label}.",
            f"Write a child-friendly mystery with a lesson learned: a {hero.type} solves a missing-item case and apologizes for guessing too fast.",
        ]
    return [
        base,
        f"Tell a cozy classroom-style mystery where {f['hero_name']} follows {culprit.clue} and discovers that {culprit.label} moved the {item.label} without meaning harm.",
        f"Write a child-facing whodunit that ends with the room tidier than before and the detective learning that careful looking is kinder than fast blaming.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    culprit = f["culprit"]
    culprit_cfg = f["culprit_cfg"]
    item = f["item_cfg"]
    place = f["place"]
    spot = f["spot"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {f['hero_name']}, a little detective, with {f['friend_name']} helping nearby. It also includes {culprit_cfg.label}, who moved the missing {item.label}."
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. {hero.pronoun('subject').capitalize()} needed it to {item.event_use}."
        ),
        (
            "Why did the room matter to the mystery?",
            f"The room was in a jumble, so the missing thing could vanish among many other objects. That messy state made the mystery feel real and also helped hide the item."
        ),
        (
            "What clue helped solve the case?",
            f"The key clue was {culprit_cfg.clue}. It pointed toward {spot.phrase}, which helped the children stop guessing and start reasoning."
        ),
        (
            f"Who moved the {item.label}, and why?",
            f"{culprit_cfg.label} moved it. {culprit_cfg.explanation} That is why the item ended up at {spot.phrase} instead of where {f['hero_name']} left it."
        ),
    ]
    if f["false_guess"]:
        qa.append((
            f"Did {f['hero_name']} guess wrong at first?",
            f"Yes. {f['hero_name']} made one quick guess before checking the clue, then realized that was unfair. The real answer came only after careful looking."
        ))
    qa.append((
        "What lesson did everyone learn?",
        "They learned that careful looking beats quick blaming. They also learned to tell people when something gets moved and to keep special things in clear places."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"clue", "tidy", f["item_cfg"].tag} | set(f["culprit_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="living_room",
        item="ribbon",
        culprit="puppy",
        hero_name="Lily",
        hero_gender="girl",
        hero_trait="hasty",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="bedroom",
        item="medal",
        culprit="brother",
        hero_name="Noah",
        hero_gender="boy",
        hero_trait="curious",
        friend_name="Maya",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="classroom",
        item="notebook",
        culprit="friend",
        hero_name="Ava",
        hero_gender="girl",
        hero_trait="patient",
        friend_name="Leo",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="classroom",
        item="map",
        culprit="friend",
        hero_name="Finn",
        hero_gender="boy",
        hero_trait="careful",
        friend_name="Lucy",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        place="bedroom",
        item="badge",
        culprit="brother",
        hero_name="Rose",
        hero_gender="girl",
        hero_trait="impulsive",
        friend_name="Theo",
        friend_gender="boy",
        parent="mother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny whodunit story world: a missing item, a jumble, a clue, and a lesson about not blaming too fast."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.culprit and not valid_combo(args.place, args.item, args.culprit):
        raise StoryError(explain_rejection(args.place, args.item, args.culprit))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, culprit_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    trait = args.trait or rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        item=item_id,
        culprit=culprit_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_trait=trait,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def _validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(No story: unknown culprit '{params.culprit}'.)")
    if params.hero_trait not in TRAITS:
        raise StoryError(f"(No story: unknown trait '{params.hero_trait}'.)")
    if not valid_combo(params.place, params.item, params.culprit):
        raise StoryError(explain_rejection(params.place, params.item, params.culprit))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        culprit_cfg=CULPRITS[params.culprit],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_trait=params.hero_trait,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
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
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue
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
        if not sample.story.strip():
            raise StoryError("empty story")
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old_stdout
        print("OK: smoke test generated and emitted a story.")
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
        print(f"{len(combos)} compatible (place, item, culprit) combos:\n")
        for place_id, item_id, culprit_id in combos:
            print(f"  {place_id:12} {item_id:10} {culprit_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.item} missing in {p.place} ({p.culprit}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
