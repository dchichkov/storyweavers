#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/inject_knuckle_recommend_bravery_twist_heartwarming.py
=================================================================================

A small heartwarming storyworld about a child who bravely helps a hidden animal.

This domain rebuilds a TinyStories-style tale with a clear beginning, middle
turn, and ending image:

* A child hears a frightened little animal hidden in a tight place.
* A grown-up recommends the safest rescue aid instead of bare hands.
* The child chooses bravery, squeezes in, and even scrapes a knuckle while
  helping.
* Twist: the "stray" turns out to be a neighbor's missing pet.
* At the clinic, a vet injects a tiny bit of numbing medicine so the sore paw
  can be treated.
* The animal goes home safe, and the child learns that brave can also mean
  being gentle.

The world model tracks both physical meters and emotional memes.  The prose is
rendered from simulated state, not from a frozen template with swapped nouns.
It includes a Python reasonableness gate plus an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/inject_knuckle_recommend_bravery_twist_heartwarming.py
    python storyworlds/worlds/gpt-5.4/inject_knuckle_recommend_bravery_twist_heartwarming.py --spot porch --animal kitten --aid towel
    python storyworlds/worlds/gpt-5.4/inject_knuckle_recommend_bravery_twist_heartwarming.py --animal puppy --aid towel
    python storyworlds/worlds/gpt-5.4/inject_knuckle_recommend_bravery_twist_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/inject_knuckle_recommend_bravery_twist_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/inject_knuckle_recommend_bravery_twist_heartwarming.py --verify
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

# Make shared result containers importable when this script is run directly from
# the repo root or from inside this nested directory.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "female_neighbor"}
        male = {"boy", "father", "man", "male_neighbor"}
        animal_neutral = {"kitten", "puppy", "rabbit", "pet"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal_neutral:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    entry: str
    scrape: str
    scare: int
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalCfg:
    id: str
    label: str
    phrase: str
    type: str
    cry: str
    paw_part: str
    sore_from: str
    hidden_mark: str
    owner_name: str
    owner_type: str
    owner_phrase: str
    owner_end: str
    jumpy: int
    safe_aids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    recommend: str
    use_text: str
    control: int
    comfort: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Trait:
    id: str
    label: str
    bravery: int


@dataclass
class StoryParams:
    spot: str
    animal: str
    aid: str
    child_name: str
    child_gender: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


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


def _r_sore_animal(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    if animal is None:
        return out
    if animal.meters["sore"] >= THRESHOLD:
        sig = ("sore", animal.id)
        if sig not in world.fired:
            world.fired.add(sig)
            animal.memes["fear"] += 1
            animal.meters["crying"] += 1
            out.append("__sore__")
    return out


def _r_contained_calm(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    if animal is None:
        return out
    if animal.meters["wrapped"] >= THRESHOLD or animal.meters["carried"] >= THRESHOLD:
        sig = ("calm", animal.id)
        if sig not in world.fired:
            world.fired.add(sig)
            animal.memes["fear"] = max(0.0, animal.memes["fear"] - 1.0)
            animal.memes["trust"] += 1
            out.append("__calm__")
    return out


def _r_found_owner(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    owner = world.entities.get("owner")
    animal = world.entities.get("animal")
    if child is None or owner is None or animal is None:
        return out
    if animal.meters["identified"] >= THRESHOLD:
        sig = ("owner_relief", owner.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["relief"] += 1
            child.memes["pride"] += 1
            out.append("__owner__")
    return out


CAUSAL_RULES = [
    Rule(name="sore_animal", tag="physical", apply=_r_sore_animal),
    Rule(name="contained_calm", tag="social", apply=_r_contained_calm),
    Rule(name="found_owner", tag="social", apply=_r_found_owner),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for text in produced:
            world.say(text)
    return produced


SPOTS = {
    "porch": Spot(
        id="porch",
        label="under the porch",
        phrase="the dark space under the porch",
        entry="kneel and reach under the low porch boards",
        scrape="a rough board brushed a knuckle",
        scare=2,
        tags={"porch", "dark"},
    ),
    "shed": Spot(
        id="shed",
        label="behind the shed",
        phrase="the narrow space behind the garden shed",
        entry="slip sideways between the shed and the fence",
        scrape="an old crate knocked a knuckle",
        scare=3,
        tags={"shed", "dark"},
    ),
    "hedge": Spot(
        id="hedge",
        label="inside the hedge",
        phrase="the leafy tunnel inside the hedge",
        entry="part the branches and crawl into the hedge",
        scrape="a twig nicked a knuckle",
        scare=1,
        tags={"hedge", "garden"},
    ),
}

ANIMALS = {
    "kitten": AnimalCfg(
        id="kitten",
        label="kitten",
        phrase="a little gray kitten",
        type="kitten",
        cry="thin mews",
        paw_part="paw",
        sore_from="a rose thorn",
        hidden_mark="a blue ribbon hidden in its neck fur",
        owner_name="Mrs. Vale",
        owner_type="female_neighbor",
        owner_phrase="the kind neighbor from two doors down",
        owner_end="carried the kitten home under her chin, smiling through happy tears",
        jumpy=2,
        safe_aids={"towel", "basket"},
        tags={"kitten", "pet", "vet"},
    ),
    "puppy": AnimalCfg(
        id="puppy",
        label="puppy",
        phrase="a small brown puppy",
        type="puppy",
        cry="small yips",
        paw_part="front paw",
        sore_from="a sharp splinter",
        hidden_mark="a red collar tag tucked under one floppy ear",
        owner_name="Mr. Reed",
        owner_type="male_neighbor",
        owner_phrase="the quiet neighbor who always watered the roses",
        owner_end="hugged the puppy close while its little tail thumped against his coat",
        jumpy=2,
        safe_aids={"blanket", "basket"},
        tags={"puppy", "pet", "vet"},
    ),
    "rabbit": AnimalCfg(
        id="rabbit",
        label="rabbit",
        phrase="a white pet rabbit",
        type="rabbit",
        cry="soft frightened thumps",
        paw_part="hind paw",
        sore_from="a burr pressed deep between its toes",
        hidden_mark="a tiny green bow hidden against one ear",
        owner_name="Mrs. Lin",
        owner_type="female_neighbor",
        owner_phrase="the neighbor who baked sesame buns on Sundays",
        owner_end="held the rabbit in both hands as if it were made of moonlight",
        jumpy=3,
        safe_aids={"towel", "basket"},
        tags={"rabbit", "pet", "vet"},
    ),
}

AIDS = {
    "towel": Aid(
        id="towel",
        label="soft towel",
        phrase="a soft towel",
        recommend='said, "I recommend the soft towel. It can wrap around a scared little body and help it feel safe."',
        use_text="spread the towel first and scoop the little animal up in one gentle bundle",
        control=2,
        comfort=2,
        tags={"towel", "gentle"},
    ),
    "basket": Aid(
        id="basket",
        label="laundry basket",
        phrase="the laundry basket",
        recommend='said, "I recommend the laundry basket. High sides can keep a frightened pet from wriggling away."',
        use_text="tip the basket low, guide the animal inside, and keep it from darting back into the shadows",
        control=3,
        comfort=1,
        tags={"basket", "gentle"},
    ),
    "blanket": Aid(
        id="blanket",
        label="small blanket",
        phrase="a small blanket",
        recommend='said, "I recommend the small blanket. It is warm and calm, and a chilly puppy often settles into soft folds."',
        use_text="hold the blanket open like a warm cloud and lift the animal carefully into it",
        control=1,
        comfort=3,
        tags={"blanket", "warm"},
    ),
}

TRAITS = {
    "careful": Trait(id="careful", label="careful", bravery=2),
    "gentle": Trait(id="gentle", label="gentle", bravery=2),
    "steady": Trait(id="steady", label="steady", bravery=3),
    "timid": Trait(id="timid", label="timid", bravery=1),
    "curious": Trait(id="curious", label="curious", bravery=2),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Zoe", "Ruby", "June", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Evan", "Finn", "Leo", "Sam", "Noah"]


def rescue_strength(aid: Aid) -> int:
    return aid.control + aid.comfort


def valid_combo(animal: AnimalCfg, aid: Aid) -> bool:
    return aid.id in animal.safe_aids and rescue_strength(aid) >= animal.jumpy + 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for spot_id in SPOTS:
        for animal_id, animal in ANIMALS.items():
            for aid_id, aid in AIDS.items():
                if valid_combo(animal, aid):
                    combos.append((spot_id, animal_id, aid_id))
    return combos


def courage_score(trait: Trait, spot: Spot) -> int:
    return trait.bravery + 1


def solo_rescue(trait: Trait, spot: Spot) -> bool:
    return courage_score(trait, spot) >= spot.scare + 1


def explain_rejection(animal: AnimalCfg, aid: Aid) -> str:
    if aid.id not in animal.safe_aids:
        ok = ", ".join(sorted(animal.safe_aids))
        return (
            f"(No story: {aid.phrase} is not a sensible rescue tool for a frightened "
            f"{animal.label} here. Try one of: {ok}.)"
        )
    return (
        f"(No story: {aid.phrase} does not give enough gentle control for a jumpy "
        f"{animal.label}. Pick an aid that keeps the rescue calm and safe.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "solo" if solo_rescue(TRAITS[params.trait], SPOTS[params.spot]) else "together"


def introduce(world: World, child: Entity, caretaker: Entity, spot: Spot, animal: AnimalCfg) -> None:
    world.say(
        f"Late one golden afternoon, {child.id} was helping {caretaker.label_word} water the plants "
        f"when {child.pronoun()} heard {animal.cry} coming from {spot.phrase}."
    )
    world.say(
        f"{child.id} crouched near the shadows and saw {animal.phrase} holding up one sore {animal.paw_part}."
    )


def need_help(world: World, child: Entity, animal_ent: Entity, animal: AnimalCfg) -> None:
    animal_ent.meters["sore"] += 1
    animal_ent.meters["lost"] += 1
    propagate(world, narrate=False)
    child.memes["care"] += 1
    world.say(
        f'"Oh, you poor thing," {child.id} whispered. The little {animal.label} looked scared, not mean, '
        f'and that made {child.pronoun("object")} want to help.'
    )


def recommend_aid(world: World, caretaker: Entity, child: Entity, aid: Aid, spot: Spot) -> None:
    child.memes["fear"] += max(0, spot.scare - 1)
    world.say(
        f'{caretaker.label_word.capitalize()} knelt beside {child.id}, looked at {spot.label}, and {aid.recommend}'
    )
    world.say(
        f'"Do not reach in with bare hands," {caretaker.pronoun()} added. "A frightened animal can kick or scramble. '
        f'We will help the safe way."'
    )


def brave_step(world: World, child: Entity, spot: Spot, outcome: str) -> None:
    child.memes["bravery"] += 1
    if outcome == "solo":
        world.say(
            f"{child.id} took one deep breath, tucked in {child.pronoun('possessive')} tummy, and chose bravery."
        )
        world.say(
            f"{child.pronoun().capitalize()} slid forward to {spot.entry}. {spot.scrape}, and {child.pronoun()} "
            f"felt the sting, but kept going anyway."
        )
    else:
        world.say(
            f"{child.id} took a deep breath and tried to be brave, but the space still looked very tight and dark."
        )
        world.say(
            f'{caretaker.label_word.capitalize()} squeezed {child.pronoun("possessive")} shoulder. "We can be brave together," '
            f'{caretaker.pronoun()} said.'
        )
        world.say(
            f"They moved in side by side to {spot.entry}. {spot.scrape}, and {child.id} winced, but did not back away."
        )
    child.meters["knuckle_scraped"] += 1


def rescue(world: World, child: Entity, caretaker: Entity, animal_ent: Entity,
           animal: AnimalCfg, aid: Aid, outcome: str) -> None:
    animal_ent.meters["wrapped"] += 1
    animal_ent.meters["carried"] += 1
    propagate(world, narrate=False)
    helper = child.id if outcome == "solo" else f"{child.id} and {caretaker.label_word}"
    world.say(
        f"Using {aid.phrase}, {helper} {aid.use_text}. At first the little {animal.label} trembled, "
        f"then it went still, as if it understood kindness when it felt it."
    )
    world.say(
        f"When {child.id} lifted it into the light, {child.pronoun()} saw why it had been crying: "
        f"{animal.sore_from} was stuck beside its sore {animal.paw_part}."
    )


def reveal_twist(world: World, child: Entity, owner: Entity, animal_ent: Entity, animal: AnimalCfg) -> None:
    animal_ent.meters["identified"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came the twist. As the fur settled, {child.id} noticed {animal.hidden_mark}."
    )
    world.say(
        f'"This is not a stray at all," {child.pronoun()} said. "It belongs to {owner.id}!"'
    )


def clinic(world: World, child: Entity, caretaker: Entity, owner: Entity,
           animal_ent: Entity, animal: AnimalCfg) -> None:
    animal_ent.meters["treated"] += 1
    animal_ent.meters["sore"] = 0.0
    animal_ent.memes["fear"] = 0.0
    animal_ent.memes["relief"] += 1
    child.memes["relief"] += 1
    world.say(
        f"They hurried to the little animal clinic with {owner.id}. The vet smiled at {child.id} and said, "
        f'"I am going to inject a tiny bit of numbing medicine near the {animal.paw_part}, so taking out {animal.sore_from} '
        f'will not hurt so much."'
    )
    world.say(
        f"{child.id} watched with steady eyes and held the carrier door while the vet worked. In a moment, "
        f"the sore place was clean, and the little {animal.label} gave a much softer sound."
    )


def ending(world: World, child: Entity, caretaker: Entity, owner: Entity,
           animal_ent: Entity, animal: AnimalCfg, outcome: str) -> None:
    child.memes["love"] += 1
    child.memes["pride"] += 1
    owner.memes["gratitude"] += 1
    line = "all by " + child.pronoun("object") if outcome == "solo" else "with help at " + child.pronoun("possessive") + " side"
    world.say(
        f'Outside the clinic, {owner.id} hugged {child.id} and {caretaker.label_word}. "Thank you for finding my little one," '
        f'{owner.pronoun()} said. "You were very brave and very gentle."'
    )
    world.say(
        f"That made {child.id} look at the tiny scrape on {child.pronoun('possessive')} knuckle and smile. "
        f"It had been worth it."
    )
    world.say(
        f"As the sun slipped down, {owner.id} {animal.owner_end}, and {child.id} walked home feeling taller than before. "
        f"{child.pronoun().capitalize()} had gone into the dark {line}, and come out carrying comfort."
    )


def tell(spot: Spot, animal: AnimalCfg, aid: Aid, trait: Trait,
         child_name: str = "Maya", child_gender: str = "girl",
         caretaker_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait.id],
        label=child_name,
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        role="caretaker",
        label="the parent",
    ))
    animal_ent = world.add(Entity(
        id="animal",
        kind="character",
        type=animal.type,
        role="animal",
        label=animal.label,
        phrase=animal.phrase,
    ))
    owner = world.add(Entity(
        id=animal.owner_name,
        kind="character",
        type=animal.owner_type,
        role="owner",
        label=animal.owner_phrase,
    ))
    child.memes["bravery_seed"] = float(trait.bravery)
    outcome = "solo" if solo_rescue(trait, spot) else "together"

    introduce(world, child, caretaker, spot, animal)
    need_help(world, child, animal_ent, animal)

    world.para()
    recommend_aid(world, caretaker, child, aid, spot)
    brave_step(world, child, spot, outcome)

    world.para()
    rescue(world, child, caretaker, animal_ent, animal, aid, outcome)
    reveal_twist(world, child, owner, animal_ent, animal)

    world.para()
    clinic(world, child, caretaker, owner, animal_ent, animal)
    ending(world, child, caretaker, owner, animal_ent, animal, outcome)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        animal=animal_ent,
        animal_cfg=animal,
        owner=owner,
        spot=spot,
        aid=aid,
        trait=trait,
        outcome=outcome,
        scraped=child.meters["knuckle_scraped"] >= THRESHOLD,
        injected=animal_ent.meters["treated"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "vet": [
        (
            "What does a vet do?",
            "A vet is a doctor for animals. Vets help pets when they are hurt or sick."
        )
    ],
    "inject": [
        (
            "What does inject mean?",
            "To inject medicine means to put medicine into the body with a small needle. A doctor or vet does it carefully to help someone feel better."
        )
    ],
    "knuckle": [
        (
            "What is a knuckle?",
            "A knuckle is one of the little bumps on your finger where it bends. You can see your knuckles when you make a fist."
        )
    ],
    "recommend": [
        (
            "What does recommend mean?",
            "To recommend something means to say it is the choice you think is best. A grown-up might recommend a safe tool or a careful plan."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel scared. It does not mean you stop feeling fear; it means you keep being kind and careful anyway."
        )
    ],
    "pet": [
        (
            "Why can a lost pet hide?",
            "A lost pet can hide when it is scared or hurt. Quiet, dark places can feel safer to a frightened animal."
        )
    ],
    "towel": [
        (
            "Why can a towel help with a scared animal?",
            "A soft towel can help a small animal feel covered and calm. It also helps hands stay gentle and safe."
        )
    ],
    "basket": [
        (
            "Why is a basket useful in a rescue?",
            "A basket has sides that can keep a frightened pet from darting away. That makes moving the animal safer."
        )
    ],
    "blanket": [
        (
            "Why can a blanket calm a puppy?",
            "A soft blanket feels warm and snug. That can help a cold or frightened puppy settle down."
        )
    ],
}
KNOWLEDGE_ORDER = ["vet", "inject", "knuckle", "recommend", "bravery", "pet", "towel", "basket", "blanket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    animal = f["animal_cfg"]
    spot = f["spot"]
    aid = f["aid"]
    outcome = f["outcome"]
    bravery_clause = "goes in alone" if outcome == "solo" else "is brave together with a parent"
    return [
        (
            f'Write a heartwarming story for a 3-to-5-year-old where a child hears a frightened '
            f'{animal.label} in {spot.label}, a grown-up uses the word "recommend," and the story '
            f'includes the words "inject" and "knuckle."'
        ),
        (
            f"Tell a gentle bravery story where {child.id} uses {aid.phrase} to rescue a hurt {animal.label}, "
            f"and the twist is that the little animal belongs to a neighbor."
        ),
        (
            f"Write a short story with a warm twist in which a child {bravery_clause}, helps a lost pet, "
            f"and ends at a clinic where a vet explains a tiny medicine shot."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    animal_ent = f["animal"]
    animal = f["animal_cfg"]
    owner = f["owner"]
    spot = f["spot"]
    aid = f["aid"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who found a frightened {animal.label}, and the grown-ups who helped. The story follows {child.id} from the dark hiding place to the happy ending outside the clinic."
        ),
        (
            f"Why did {child.id} go near {spot.label}?",
            f"{child.id} heard {animal.cry} and realized a little animal was hiding there with a sore {animal.paw_part}. That sound made {child.pronoun('object')} want to help instead of walking away."
        ),
        (
            f"What did {caretaker.label_word} recommend?",
            f"{caretaker.label_word.capitalize()} recommended {aid.phrase} for the rescue. The choice was meant to keep the frightened {animal.label} calm and keep everybody safer."
        ),
        (
            f"What happened to {child.id}'s knuckle?",
            f"{child.id}'s knuckle got scraped while {child.pronoun()} moved into the tight hiding place. Even though it stung, {child.pronoun()} kept helping."
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"How was {child.id} brave?",
                f"{child.id} was brave by going into the dark space alone after taking a deep breath. {child.pronoun().capitalize()} felt the sting on a scraped knuckle but kept moving gently toward the frightened animal."
            )
        )
    else:
        qa.append(
            (
                f"How was {child.id} brave?",
                f"{child.id} was brave by admitting the space felt scary and still going in with help. The story shows that bravery can mean doing a hard thing together instead of pretending not to be scared."
            )
        )
    qa.append(
        (
            "What was the twist?",
            f"The twist was that the little {animal.label} was not a stray at all. {child.id} noticed {animal.hidden_mark}, which showed that it belonged to {owner.id}."
        )
    )
    qa.append(
        (
            "Why did the vet inject medicine?",
            f"The vet injected a tiny bit of numbing medicine near the sore {animal.paw_part} so taking out {animal.sore_from} would hurt less. That helped the animal get treated gently and safely."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {owner.id} getting the pet back and thanking {child.id} for being brave and gentle. The ending image shows the pet going home safe while {child.id} walks home feeling taller inside."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"vet", "inject", "knuckle", "recommend", "bravery", "pet"} | set(f["aid"].tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:10} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Python gate twin: a combo is valid when the aid is explicitly safe for the
% animal and when its rescue strength reaches the animal's jumpiness threshold.
rescue_strength(A, S) :- control(A, C), comfort(A, K), S = C + K.
valid(Spot, Animal, Aid) :-
    spot(Spot), animal(Animal), aid(Aid),
    safe_for(Animal, Aid),
    rescue_strength(Aid, S),
    jumpy(Animal, J),
    S >= J + 1.

% Outcome twin: bravery score = trait bravery + one step of grown-up support.
courage(Trait, C) :- bravery(Trait, B), C = B + 1.
outcome(solo) :-
    chosen_trait(Trait), chosen_spot(Spot),
    courage(Trait, C), scare(Spot, S), C >= S + 1.
outcome(together) :-
    chosen_trait(Trait), chosen_spot(Spot),
    courage(Trait, C), scare(Spot, S), C < S + 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("scare", spot_id, spot.scare))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("jumpy", animal_id, animal.jumpy))
        for aid_id in sorted(animal.safe_aids):
            lines.append(asp.fact("safe_for", animal_id, aid_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("control", aid_id, aid.control))
        lines.append(asp.fact("comfort", aid_id, aid.comfort))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("bravery", trait_id, trait.bravery))
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
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_spot", params.spot),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    sink = io.StringIO()
    with redirect_stdout(sink):
        emit(sample, trace=False, qa=True, header="### smoke")


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
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

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcome checks differ.")

    try:
        for params in CURATED[:2]:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story during smoke test.")
            sample.to_json()
            _smoke_emit(sample)
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        default_sample = generate(default_params)
        if "inject" not in default_sample.story or "knuckle" not in default_sample.story or "recommend" not in default_sample.story:
            raise StoryError("Seed words did not appear in smoke-test story.")
        _smoke_emit(default_sample)
        print("OK: smoke generation and emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        spot="porch",
        animal="kitten",
        aid="towel",
        child_name="Maya",
        child_gender="girl",
        caretaker="mother",
        trait="steady",
    ),
    StoryParams(
        spot="shed",
        animal="puppy",
        aid="basket",
        child_name="Owen",
        child_gender="boy",
        caretaker="father",
        trait="careful",
    ),
    StoryParams(
        spot="hedge",
        animal="rabbit",
        aid="towel",
        child_name="Ruby",
        child_gender="girl",
        caretaker="mother",
        trait="timid",
    ),
    StoryParams(
        spot="porch",
        animal="puppy",
        aid="blanket",
        child_name="Leo",
        child_gender="boy",
        caretaker="father",
        trait="gentle",
    ),
    StoryParams(
        spot="shed",
        animal="kitten",
        aid="basket",
        child_name="Nora",
        child_gender="girl",
        caretaker="mother",
        trait="steady",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming rescue storyworld: a child helps a hidden pet, with bravery and a gentle twist."
    )
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.aid:
        animal = ANIMALS[args.animal]
        aid = AIDS[args.aid]
        if not valid_combo(animal, aid):
            raise StoryError(explain_rejection(animal, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.animal is None or combo[1] == args.animal)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, animal_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        spot=spot_id,
        animal=animal_id,
        aid=aid_id,
        child_name=child_name,
        child_gender=gender,
        caretaker=caretaker,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.caretaker not in {"mother", "father"}:
        raise StoryError(f"(Unknown caretaker: {params.caretaker})")

    animal = ANIMALS[params.animal]
    aid = AIDS[params.aid]
    if not valid_combo(animal, aid):
        raise StoryError(explain_rejection(animal, aid))

    world = tell(
        spot=SPOTS[params.spot],
        animal=animal,
        aid=aid,
        trait=TRAITS[params.trait],
        child_name=params.child_name,
        child_gender=params.child_gender,
        caretaker_type=params.caretaker,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, animal, aid) combos:\n")
        for spot_id, animal_id, aid_id in combos:
            print(f"  {spot_id:6} {animal_id:7} {aid_id}")
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
            header = f"### {p.child_name}: {p.animal} at {p.spot} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
