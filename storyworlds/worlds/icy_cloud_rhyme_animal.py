#!/usr/bin/env python3
"""
storyworlds/worlds/icy_cloud_rhyme_animal.py
============================================

A standalone story world sketch for a small animal who follows an icy cloud and
learns which shelter really protects friends from frost, with a rhymed surprise
ending.  The world keeps the physical frost state and the animal's care/lesson
state on entities, then renders a complete TinyStories-style story from those
facts.
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    inside: Optional[str] = None
    shelter: bool = False
    blocks_frost: bool = False
    warm_lining: bool = False
    capacity: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"doe", "hen", "vixen"}
        male = {"buck", "rooster", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Animal:
    id: str
    name: str
    kind: str
    phrase: str
    subject: str
    object: str
    possessive: str
    quick: str
    home_hint: str
    trait: str


@dataclass
class FriendGroup:
    id: str
    label: str
    phrase: str
    count: int
    place_detail: str
    cold_image: str
    grateful_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    open_detail: str
    safe_detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shelter:
    id: str
    label: str
    phrase: str
    approach: str
    failure: str
    success: str
    capacity: int
    blocks_frost: bool
    warm_lining: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    reveal: str
    rhyme: str
    final_image: str
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

    def shelters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.shelter]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_exposed_frost(world: World) -> list[str]:
    out: list[str] = []
    cloud = world.entities.get("cloud")
    friends = world.entities.get("friends")
    if not cloud or not friends or cloud.meters["near"] < THRESHOLD:
        return out
    if friends.inside:
        shelter = world.get(friends.inside)
        if shelter.blocks_frost and shelter.capacity >= int(friends.meters["count"]):
            return out
    sig = ("frost", friends.id, friends.inside or "open")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friends.meters["frost"] += 1
    out.append("Silver frost crept close to the friends.")
    return out


def _r_bad_shelter_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friends = world.entities.get("friends")
    if not hero or not friends or friends.meters["frost"] < THRESHOLD:
        return out
    sig = ("worry", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["care"] += 1
    out.append(f"{hero.id} knew a roof was not enough if cold wind could crawl inside.")
    return out


def _r_good_shelter_warmth(world: World) -> list[str]:
    out: list[str] = []
    friends = world.entities.get("friends")
    if not friends or not friends.inside:
        return out
    shelter = world.get(friends.inside)
    if not (shelter.blocks_frost and shelter.capacity >= int(friends.meters["count"])):
        return out
    sig = ("warm", friends.id, shelter.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friends.meters["safe"] += 1
    friends.meters["warm"] += 1
    friends.meters["frost"] = 0
    out.append("The frost stopped at the door, thin as glass and quiet as a held breath.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friends = world.entities.get("friends")
    if not hero or not friends or friends.meters["safe"] < THRESHOLD:
        return out
    sig = ("lesson", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["lesson"] += 1
    hero.memes["relief"] += 1
    out.append(f"{hero.id} learned to choose the place that stopped the frost, not just the place that looked like a roof.")
    return out


CAUSAL_RULES = [
    Rule("frost", "physical", _r_exposed_frost),
    Rule("worry", "emotional", _r_bad_shelter_worry),
    Rule("warm", "physical", _r_good_shelter_warmth),
    Rule("lesson", "emotional", _r_lesson),
]


def propagate(world: World, *, narrate: bool = False) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            lines = rule.apply(world)
            if len(world.fired) != before:
                changed = True
            if narrate:
                out.extend(lines)
    return out


def protects_friends(shelter: Shelter, friends: FriendGroup) -> bool:
    return shelter.blocks_frost and shelter.warm_lining and shelter.capacity >= friends.count


def valid_transition(decoy: Shelter, shelter: Shelter, friends: FriendGroup) -> bool:
    return not protects_friends(decoy, friends) and protects_friends(shelter, friends)


def predict_shelter(shelter: Shelter, friends: FriendGroup, place: Place) -> dict[str, float]:
    world = World(place)
    world.add(Entity("cloud", type="cloud", label="icy cloud", meters=defaultdict(float, {"near": 1.0})))
    world.add(Entity("friends", kind="character", type="friends", label=friends.label,
                     inside="test", meters=defaultdict(float, {"count": float(friends.count)})))
    world.add(Entity("test", type="shelter", label=shelter.label, shelter=True,
                     blocks_frost=shelter.blocks_frost, warm_lining=shelter.warm_lining,
                     capacity=shelter.capacity))
    propagate(world)
    friends_ent = world.get("friends")
    return {"frost": friends_ent.meters["frost"], "safe": friends_ent.meters["safe"]}


def introduce(world: World, hero: Entity, animal: Animal, place: Place) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Once there was {animal.phrase} named {animal.name} who lived near {place.label}."
    )
    world.say(
        f"{animal.name} was {animal.trait}, and {animal.subject} liked to watch "
        f"clouds change shape over the grass."
    )


def follow_cloud(world: World, hero: Entity, animal: Animal, place: Place) -> None:
    cloud = world.get("cloud")
    cloud.meters["near"] += 1
    hero.memes["care"] += 1
    world.say(
        f"One morning an icy cloud bumped along the sky, low and blue-white, "
        f"as if it had lost its way."
    )
    world.say(
        f"{animal.name} followed it past {place.open_detail}, because every place "
        f"under the cloud glittered with cold."
    )


def find_friends(world: World, hero: Entity, animal: Animal, friends: FriendGroup) -> None:
    friends_ent = world.get("friends")
    friends_ent.meters["count"] = float(friends.count)
    world.say(
        f"Then {animal.name} heard {friends.grateful_sound} from {friends.place_detail}."
    )
    world.say(
        f"There were {friends.phrase}, {friends.cold_image}, and the icy cloud was sliding toward them."
    )


def try_decoy(world: World, hero: Entity, animal: Animal, friends: FriendGroup,
              decoy: Shelter) -> None:
    decoy_ent = world.get("decoy")
    friends_ent = world.get("friends")
    friends_ent.inside = decoy_ent.id
    world.say(f"First, {animal.name} led them to {decoy.phrase}.")
    world.say(decoy.approach)
    for line in propagate(world, narrate=True):
        world.say(line)
    world.say(decoy.failure)


def choose_shelter(world: World, hero: Entity, animal: Animal, friends: FriendGroup,
                   shelter: Shelter, place: Place) -> None:
    safe_ent = world.get("shelter")
    friends_ent = world.get("friends")
    prediction = predict_shelter(shelter, friends, place)
    world.facts["prediction"] = prediction
    world.say(
        f"{animal.name} looked again and found {shelter.phrase}. It had a snug "
        f"mouth and a warm little floor."
    )
    if prediction["safe"] >= THRESHOLD:
        world.say(
            f'"This one stops the frost," {animal.name} said. "Quick, inside with me."'
        )
    friends_ent.inside = safe_ent.id
    for line in propagate(world, narrate=True):
        world.say(line)
    world.say(shelter.success)


def surprise_ending(world: World, hero: Entity, animal: Animal, friends: FriendGroup,
                    surprise: Surprise) -> None:
    cloud = world.get("cloud")
    friends_ent = world.get("friends")
    if friends_ent.meters["safe"] >= THRESHOLD:
        cloud.memes["surprise"] += 1
        hero.memes["joy"] += 1
    world.say(surprise.reveal.format(name=animal.name, friends=friends.label))
    world.say(f'"{surprise.rhyme}"')
    world.say(surprise.final_image.format(name=animal.name, friends=friends.label))


def tell(animal: Animal, friends: FriendGroup, place: Place, decoy: Shelter,
         shelter: Shelter, surprise: Surprise) -> World:
    world = World(place)
    hero = world.add(Entity(animal.name, kind="character", type=animal.kind,
                            label=animal.name, traits=[animal.trait], role="hero"))
    world.entities["hero"] = hero
    world.add(Entity("cloud", type="cloud", label="icy cloud"))
    world.add(Entity("friends", kind="character", type="friends",
                     label=friends.label, phrase=friends.phrase))
    world.add(Entity("decoy", type="shelter", label=decoy.label, shelter=True,
                     blocks_frost=decoy.blocks_frost, warm_lining=decoy.warm_lining,
                     capacity=decoy.capacity))
    world.add(Entity("shelter", type="shelter", label=shelter.label, shelter=True,
                     blocks_frost=shelter.blocks_frost, warm_lining=shelter.warm_lining,
                     capacity=shelter.capacity))

    introduce(world, hero, animal, place)
    follow_cloud(world, hero, animal, place)

    world.para()
    find_friends(world, hero, animal, friends)
    try_decoy(world, hero, animal, friends, decoy)

    world.para()
    choose_shelter(world, hero, animal, friends, shelter, place)
    surprise_ending(world, hero, animal, friends, surprise)

    world.facts.update(
        animal=animal, hero=hero, friends=friends, friends_ent=world.get("friends"),
        place=place, decoy=decoy, shelter=shelter, surprise=surprise,
        protected=world.get("friends").meters["safe"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


ANIMALS = {
    "mouse": Animal("mouse", "Milo", "mouse", "a tiny brown mouse",
                    "he", "him", "his", "scampered", "a mossy mouse hole", "brave"),
    "bunny": Animal("bunny", "Bibi", "bunny", "a small gray bunny",
                    "she", "her", "her", "hopped", "a burrow under the fern", "gentle"),
    "hedgehog": Animal("hedgehog", "Hattie", "hedgehog", "a little hedgehog",
                       "she", "her", "her", "trotted", "a nest of dry leaves", "thoughtful"),
    "squirrel": Animal("squirrel", "Pip", "squirrel", "a young red squirrel",
                       "he", "him", "his", "skipped", "a hollow branch", "quick"),
}

FRIENDS = {
    "sparrows": FriendGroup(
        "sparrows", "the sparrows", "three baby sparrows", 3,
        "the bare blackberry bush", "their feathers puffed like tiny gray mittens",
        "thin peeps", tags={"birds", "frost"}),
    "ducklings": FriendGroup(
        "ducklings", "the ducklings", "two ducklings", 2,
        "the rim of the frozen puddle", "their little orange feet tucked up tight",
        "soft cheeps", tags={"ducks", "frost"}),
    "beetles": FriendGroup(
        "beetles", "the beetles", "four striped beetles", 4,
        "a curled brown leaf", "their shiny backs dusted white",
        "tiny taps", tags={"beetles", "frost"}),
}

PLACES = {
    "meadow": Place("meadow", "the winter meadow", "the bent grass and seed heads",
                    "the old bank where roots made rooms", tags={"meadow", "cloud"}),
    "garden": Place("garden", "the quiet garden", "the parsley pot and frosty stones",
                    "the compost corner where straw stayed dry", tags={"garden", "cloud"}),
    "pond": Place("pond", "the little pond", "the reeds and the silver mud",
                  "the willow roots by the bank", tags={"pond", "cloud"}),
}

SHELTERS = {
    "leaf": Shelter(
        "leaf", "curled leaf", "a curled leaf",
        "It looked like a roof, shiny and brown.",
        "But the leaf rattled, and the cold slipped under its curled-up edge.",
        "The leaf lay still behind them, sparkling but empty.",
        capacity=2, blocks_frost=False, warm_lining=False, tags={"leaf"}),
    "mushroom": Shelter(
        "mushroom", "mushroom cap", "a wide mushroom cap",
        "It made a neat umbrella over their heads.",
        "But the icy wind blew sideways under the cap and nipped their toes.",
        "The mushroom cap wore a white rim while everyone stayed away from the cold.",
        capacity=3, blocks_frost=False, warm_lining=False, tags={"mushroom"}),
    "stone": Shelter(
        "stone", "flat stone", "the shadow of a flat stone",
        "It was dark underneath, so it seemed secret and safe.",
        "But stone held the chill, and the floor felt cold through every tiny foot.",
        "The flat stone shone with frost like a little moon.",
        capacity=4, blocks_frost=False, warm_lining=False, tags={"stone"}),
    "log": Shelter(
        "log", "hollow log", "a hollow log lined with moss",
        "The round doorway was small, and the moss inside smelled green and dry.",
        "The log had no gap for the wind to poke through.",
        "Inside the mossy log, the friends warmed their toes and blinked at the bright door.",
        capacity=5, blocks_frost=True, warm_lining=True, tags={"log", "moss"}),
    "burrow": Shelter(
        "burrow", "warm burrow", "a warm burrow under fern roots",
        "The fern roots made a low brown door, just big enough for friends.",
        "The burrow held the ground's quiet warmth.",
        "In the burrow, every friend had a dry spot and a warm shoulder nearby.",
        capacity=4, blocks_frost=True, warm_lining=True, tags={"burrow", "roots"}),
    "straw_basket": Shelter(
        "straw_basket", "straw basket", "an overturned straw basket packed with hay",
        "The hay made a sweet little cave with a round yellow wall.",
        "The basket kept out the frost and held the hay-warm air.",
        "Under the basket, the hay rustled softly and nobody shivered.",
        capacity=6, blocks_frost=True, warm_lining=True, tags={"basket", "hay"}),
}

SURPRISES = {
    "bell": Surprise(
        "bell",
        "Then the icy cloud bumped the shelter and sneezed out a blue glass bell.",
        "Ding-ding, snow king, cold may sing, but warm hearts ring!",
        "The bell chimed above {name} and {friends}, and frost flowers opened without touching their toes.",
        tags={"bell", "rhyme"}),
    "star": Surprise(
        "star",
        "Then the icy cloud rolled over and showed a tiny star tucked in its middle.",
        "Bright little star, near and far, warm friends are where you are!",
        "The star winked over {name}, and the cloud drifted away like a sleepy white boat.",
        tags={"star", "rhyme"}),
    "scarf": Surprise(
        "scarf",
        "Then the icy cloud shook itself and dropped one soft scarf made of snowlight.",
        "Loop and glow, soft as snow, thank you, friends, below!",
        "{name} tied the scarf on a twig, and it fluttered like a flag for the safe little home.",
        tags={"scarf", "rhyme"}),
}


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos = []
    for animal in ANIMALS:
        for friends_id, friends in FRIENDS.items():
            for place in PLACES:
                for decoy_id, decoy in SHELTERS.items():
                    for shelter_id, shelter in SHELTERS.items():
                        if decoy_id == shelter_id:
                            continue
                        if not valid_transition(decoy, shelter, friends):
                            continue
                        for surprise in SURPRISES:
                            combos.append((animal, friends_id, place, decoy_id, shelter_id, surprise))
    return combos


@dataclass
class StoryParams:
    animal: str
    friends: str
    place: str
    decoy: str
    shelter: str
    surprise: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cloud": [("What is an icy cloud?",
               "An icy cloud is a cold cloud carrying tiny bits of frozen water. In this story it makes frost wherever it drifts low.")],
    "frost": [("What is frost?",
               "Frost is a thin layer of ice crystals that forms when water in the air gets very cold. It can make leaves, stones, and toes feel chilly.")],
    "moss": [("Why did moss help in the hollow log?",
              "Dry moss made a soft lining that held warmth inside the log. It helped the friends stay away from the icy wind.")],
    "burrow": [("Why can a burrow be warm?",
                "A burrow is tucked in the ground, where wind cannot blow straight through. The earth around it helps hold warmth.")],
    "hay": [("Why does hay make a cozy shelter?",
             "Hay traps little pockets of air, and those pockets help keep warmth close. That is why the basket felt snug.")],
    "birds": [("Why do small birds puff up in the cold?",
               "Small birds puff their feathers to trap warm air near their bodies. It helps them stay warmer in cold weather.")],
    "ducks": [("Can ducklings get cold?",
               "Yes. Ducklings have small bodies, so cold wind and ice can chill them quickly. They need a dry, sheltered spot.")],
    "beetles": [("Where do beetles hide from cold weather?",
                 "Many beetles tuck under leaves, bark, or soil when it gets cold. A protected place keeps frost off their bodies.")],
}
KNOWLEDGE_ORDER = ["cloud", "frost", "moss", "burrow", "hay", "birds", "ducks", "beetles"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal, friends, shelter = f["animal"], f["friends"], f["shelter"]
    return [
        'Write a TinyStories-style animal story using the seed words "icy cloud".',
        f"Tell a child-facing story where {animal.name} the {animal.kind} follows an icy cloud and learns that {shelter.phrase} protects {friends.label} from frost.",
        "Write a gentle story with a surprise rhymed ending, a small animal hero, and friends who are kept warm by the right shelter.",
    ]


def clean_reveal(text: str) -> str:
    text = text.rstrip(".")
    if text.startswith("Then "):
        text = text[5:]
    return text[:1].lower() + text[1:]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal, friends, place = f["animal"], f["friends"], f["place"]
    decoy, shelter, surprise = f["decoy"], f["shelter"], f["surprise"]
    qa: list[tuple[str, str]] = [
        ("Who is the story about?",
         f"The story is about {animal.name}, a small {animal.kind}, and {friends.phrase} near {place.label}. {animal.name} follows an icy cloud because the cold is moving toward the friends."),
        ("Why did the animal follow the icy cloud?",
         f"{animal.name} followed the icy cloud because every place below it glittered with cold. Following it helped {animal.name} see that {friends.label} were in danger of frost."),
        ("Which shelter did not work at first?",
         f"First, {animal.name} tried {decoy.phrase}. It looked helpful, but it did not block the frost and cold wind well enough."),
        ("Which shelter actually protected the friends?",
         f"{shelter.phrase.capitalize()} protected {friends.label}. It blocked the frost, had enough room, and held warmth around them."),
    ]
    if f.get("learned"):
        qa.append((
            f"What did {animal.name} learn?",
            f"{animal.name} learned that a shelter must stop frost, not just look like a roof. The safe place worked because it kept cold wind out and warmth in.",
        ))
    if f.get("protected"):
        qa.append((
            "What was the surprise ending?",
            f"The icy cloud gave a surprise after the friends were safe: {clean_reveal(surprise.reveal)}. Then it spoke in a rhyme, so the ending felt playful instead of scary.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cloud", "frost"} | set(f["friends"].tags) | set(f["shelter"].tags)
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
    for e in world.entities.values():
        if e.id == "hero":
            continue
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.inside:
            bits.append(f"inside={e.inside}")
        if e.shelter:
            bits.append(
                f"shelter blocks_frost={e.blocks_frost} warm_lining={e.warm_lining} capacity={e.capacity}"
            )
        lines.append(f"  {e.id:9} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("mouse", "sparrows", "meadow", "leaf", "log", "bell"),
    StoryParams("bunny", "ducklings", "pond", "mushroom", "burrow", "star"),
    StoryParams("hedgehog", "beetles", "garden", "stone", "straw_basket", "scarf"),
    StoryParams("squirrel", "sparrows", "garden", "mushroom", "log", "star"),
    StoryParams("mouse", "beetles", "pond", "leaf", "straw_basket", "bell"),
]


def explain_rejection(decoy: Shelter, shelter: Shelter, friends: FriendGroup) -> str:
    if protects_friends(decoy, friends):
        return (
            f"(No story: {decoy.phrase} already protects {friends.label}, so the "
            "animal would not need to learn a better shelter.)"
        )
    if not protects_friends(shelter, friends):
        return (
            f"(No story: {shelter.phrase} does not truly protect {friends.label} "
            "from frost. The final shelter must block cold, hold warmth, and fit everyone.)"
        )
    return "(No story: the shelter change does not create the required learning turn.)"


ASP_RULES = r"""
protects(S, F) :- shelter(S), friend(F), blocks_frost(S), warm_lining(S),
                  capacity(S, C), friend_count(F, N), C >= N.
bad_first(D, F) :- shelter(D), friend(F), not protects(D, F).
valid(A, F, P, D, S, R) :- animal(A), friend(F), place(P), shelter(D), shelter(S),
                           surprise(R), D != S, bad_first(D, F), protects(S, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    for fid, friends in FRIENDS.items():
        lines.append(asp.fact("friend", fid))
        lines.append(asp.fact("friend_count", fid, friends.count))
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for sid, shelter in SHELTERS.items():
        lines.append(asp.fact("shelter", sid))
        lines.append(asp.fact("capacity", sid, shelter.capacity))
        if shelter.blocks_frost:
            lines.append(asp.fact("blocks_frost", sid))
        if shelter.warm_lining:
            lines.append(asp.fact("warm_lining", sid))
    for surprise in SURPRISES:
        lines.append(asp.fact("surprise", surprise))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid story gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    mismatches = []
    for fid, friends in FRIENDS.items():
        for sid, shelter in SHELTERS.items():
            predicted = predict_shelter(shelter, friends, next(iter(PLACES.values())))
            py = protects_friends(shelter, friends)
            model_safe = predicted["safe"] >= THRESHOLD and predicted["frost"] == 0
            if py != model_safe:
                mismatches.append((sid, fid, py, predicted))
    if mismatches:
        rc = 1
        print("MISMATCH in Python shelter simulation:")
        for row in mismatches:
            print(" ", row)
    else:
        print("OK: shelter simulation matches protects_friends().")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description='Story world sketch: a small animal follows an "icy cloud" '
                    "and learns which shelter protects friends from frost.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friends", choices=FRIENDS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--decoy", choices=SHELTERS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches the Python logic")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.friends and args.decoy and args.shelter:
        friends = FRIENDS[args.friends]
        decoy, shelter = SHELTERS[args.decoy], SHELTERS[args.shelter]
        if not valid_transition(decoy, shelter, friends):
            raise StoryError(explain_rejection(decoy, shelter, friends))

    combos = [
        c for c in valid_combos()
        if (args.animal is None or c[0] == args.animal)
        and (args.friends is None or c[1] == args.friends)
        and (args.place is None or c[2] == args.place)
        and (args.decoy is None or c[3] == args.decoy)
        and (args.shelter is None or c[4] == args.shelter)
        and (args.surprise is None or c[5] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal, friends, place, decoy, shelter, surprise = rng.choice(sorted(combos))
    return StoryParams(animal, friends, place, decoy, shelter, surprise)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ANIMALS[params.animal], FRIENDS[params.friends], PLACES[params.place],
        SHELTERS[params.decoy], SHELTERS[params.shelter], SURPRISES[params.surprise],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, friends, place, decoy, shelter, surprise) combos:\n")
        for animal, friends, place, decoy, shelter, surprise in combos:
            print(f"  {animal:9} {friends:9} {place:7} {decoy:9} -> {shelter:12} {surprise}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.animal}: {p.decoy} -> {p.shelter} for {p.friends} ({p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
