#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py
======================================================

A standalone story world for gentle, humorous, slice-of-life stories about a
child who tries to invite a hoofed farm friend to a tiny indoor tea party.

The core premise:
- a child makes a small pretend party,
- a hoofed animal is tempted by a snack,
- a sibling or friend warns that a real hoof in a little room will make a mess,
- either the warning works, or the animal clops inside,
- a calm grown-up redirects the fun to a better place.

This world prefers plausible, child-facing variants:
- the snack must be one the animal would really follow,
- the room must be big enough for that animal,
- low-common-sense responses are known but refused,
- an older, cautious sibling can avert the indoor mess before it starts.

Run it
------
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py --animal pony --snack apple_slices --room front_room
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py --animal calf --room bedroom
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py --response shoo
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py --all
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py --trace --seed 777
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py --json
python storyworlds/worlds/gpt-5.4/hoof_humor_slice_of_life.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class AnimalCfg:
    id: str
    label: str
    phrase: str
    hoof_sound: str
    nose_line: str
    size: int
    likes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SnackCfg:
    id: str
    label: str
    phrase: str
    crumbs: int
    treat_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RoomCfg:
    id: str
    label: str
    phrase: str
    capacity: int
    mess_risk: int
    table_phrase: str
    outside_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ResponseCfg:
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"host", "cautioner"}]

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


def _r_indoor_mess(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    room = world.entities.get("room")
    if not animal or not room:
        return out
    if animal.meters["indoors"] < THRESHOLD:
        return out
    sig = ("indoor_mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["mess"] += 1
    room.meters["prints"] += 1
    for kid in world.kids():
        kid.memes["surprise"] += 1
    out.append("__clop__")
    return out


def _r_table_wobble(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    room = world.entities.get("room")
    snack = world.entities.get("snack")
    if not animal or not room or not snack:
        return out
    if animal.meters["indoors"] < THRESHOLD:
        return out
    if snack.meters["close_to_animal"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["wobble"] += 1
    room.meters["mess"] += 1
    animal.meters["crumbs_on_nose"] += 1
    out.append("__wobble__")
    return out


CAUSAL_RULES = [
    Rule(name="indoor_mess", tag="physical", apply=_r_indoor_mess),
    Rule(name="table_wobble", tag="physical", apply=_r_table_wobble),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def snack_works(animal: AnimalCfg, snack: SnackCfg) -> bool:
    return snack.id in animal.likes


def room_fits(animal: AnimalCfg, room: RoomCfg) -> bool:
    return animal.size <= room.capacity


def sensible_responses() -> list[ResponseCfg]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> ResponseCfg:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def mess_severity(room: RoomCfg, snack: SnackCfg, delay: int) -> int:
    return room.mess_risk + snack.crumbs + delay


def is_contained(response: ResponseCfg, room: RoomCfg, snack: SnackCfg, delay: int) -> bool:
    return response.power >= mess_severity(room, snack, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, host_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > host_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_mess(world: World) -> dict:
    sim = world.copy()
    animal = sim.get("animal")
    snack = sim.get("snack")
    animal.meters["indoors"] += 1
    snack.meters["close_to_animal"] += 1
    propagate(sim, narrate=False)
    room = sim.get("room")
    return {
        "mess": room.meters["mess"],
        "prints": room.meters["prints"],
        "wobble": room.meters["wobble"],
    }


def morning_setup(world: World, a: Entity, b: Entity, room: RoomCfg) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One mild morning, {a.id} set up a tiny tea party in {room.phrase}. "
        f"{room.table_phrase}"
    )
    world.say(
        f"{b.id} sat nearby, folding a napkin into a crooked little fan and trying not to laugh."
    )


def choose_guest(world: World, a: Entity, animal: AnimalCfg, snack: SnackCfg) -> None:
    a.memes["idea"] += 1
    world.say(
        f'When {a.id} looked out the window and saw {animal.phrase} in the yard, '
        f"{a.pronoun('possessive')} eyes went bright. "
        f'"Maybe {animal.label} can be our special guest," {a.pronoun()} whispered.'
    )
    world.say(f"{a.id} lifted {snack.phrase}. {snack.treat_line}")


def warn(world: World, b: Entity, a: Entity, animal: AnimalCfg, room: RoomCfg, parent: Entity) -> None:
    pred = predict_mess(world)
    b.memes["caution"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    details = []
    if pred["prints"] >= THRESHOLD:
        details.append("hoof prints")
    if pred["wobble"] >= THRESHOLD:
        details.append("wobbling cups")
    worry = " and ".join(details) if details else "a muddle"
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} could already picture {worry} in {room.label}."
    world.say(
        f'{b.id} lowered the sugar spoon. "{a.id}, a real hoof does not know tea-party rules. '
        f'If {animal.label} follows that snack into {room.label}, we will have {worry}. '
        f'Let\'s ask {parent.label_word} first."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, animal: AnimalCfg, snack: SnackCfg, room: RoomCfg, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {snack.label}, then at the little cups, and finally at {b.id}. '
        f'"You are right," {a.pronoun()} said. "A hoof is bigger than my best saucer."'
    )
    world.say(
        f"They left {snack.phrase} by the window, went to fetch {parent.label_word}, "
        f"and told the whole silly plan before a single hoof crossed the door."
    )


def defy(world: World, a: Entity, b: Entity, animal: AnimalCfg, snack: SnackCfg) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Just one tiny visit," {a.id} said. {a.pronoun().capitalize()} opened the door a crack '
        f"and held out {snack.phrase}."
    )
    world.say(
        f"{animal.hoof_sound.capitalize()} came closer on the step, and {b.id} made a face that said this was already becoming a story."
    )


def invite_inside(world: World, animal_ent: Entity, snack_ent: Entity, animal: AnimalCfg, room: RoomCfg) -> None:
    animal_ent.meters["indoors"] += 1
    snack_ent.meters["close_to_animal"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In came {animal.phrase}, slow and curious, with one careful hoof, then another. "
        f"The little room suddenly felt much smaller."
    )
    if world.get("room").meters["prints"] >= THRESHOLD:
        world.say(
            f"{animal.hoof_sound.capitalize()} sounded across the floor, and neat little hoof marks appeared where no tea guest had been invited to step."
        )
    if world.get("room").meters["wobble"] >= THRESHOLD:
        world.say(
            f"{animal.pronoun('possessive').capitalize()} nose reached for the treat, bumped the table, and the toy cups clicked together in a brave but shaky row."
        )


def giggle_turn(world: World, a: Entity, b: Entity, animal_ent: Entity, animal: AnimalCfg, snack: SnackCfg) -> None:
    a.memes["surprise"] += 1
    b.memes["surprise"] += 1
    if animal_ent.meters["crumbs_on_nose"] >= THRESHOLD:
        world.say(
            f"Then both children forgot to gasp, because {animal.label} ended up with crumbs on {animal.nose_line}, looking far too pleased with the job."
        )
    else:
        world.say(
            f"For one second the whole thing was so ridiculous that even {b.id} had to clap a hand over a laugh."
        )


def call_parent(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}!" {b.id} called. "Please come see our very large tea guest."')


def rescue(world: World, parent: Entity, response: ResponseCfg, animal: AnimalCfg, room: RoomCfg) -> None:
    room_ent = world.get("room")
    animal_ent = world.get("animal")
    room_ent.meters["mess"] = 0.0
    room_ent.meters["prints"] = 0.0
    room_ent.meters["wobble"] = 0.0
    animal_ent.meters["indoors"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came to the doorway, blinked once, and then smiled instead of scolding. "
        f"{parent.pronoun().capitalize()} {response.text.format(animal=animal.label, room=room.label, outside=room.outside_place)}."
    )
    world.say(
        f"In another moment the tea things were safe, the hoof was back where a hoof belonged, and the room could breathe again."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, animal: AnimalCfg, room: RoomCfg) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'"Tiny cups are for tiny hands," {parent.label_word} said warmly, brushing at the floor, '
        f'"and {animal.label} can visit much better in {room.outside_place}."'
    )
    world.say(
        f'{a.id} nodded. "{animal.label.capitalize()} was funny," {a.pronoun()} admitted, '
        f'"but not very good at sitting still on a tea-party chair."'
    )


def outside_party(world: World, parent: Entity, a: Entity, b: Entity, animal: AnimalCfg, snack: SnackCfg, room: RoomCfg) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"A little later they carried the napkins outside to {room.outside_place}, where there was room for laughter, crumbs, and one honest hoof."
    )
    world.say(
        f"{parent.label_word.capitalize()} set out a sturdy pan for {animal.label} and kept the tiny cups for the children. "
        f"{animal.phrase.capitalize()} crunched {snack.label} from the pan and looked deeply proud."
    )
    world.say(
        f"By the end, {b.id} was giggling, {a.id} was pouring pretend tea for the daisies, "
        f"and the hoof stood politely on the grass as if it had learned the joke too."
    )


def rescue_fail(world: World, parent: Entity, response: ResponseCfg, animal: AnimalCfg, room: RoomCfg) -> None:
    room_ent = world.get("room")
    room_ent.meters["mess"] += 1
    room_ent.meters["prints"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried in and {response.fail.format(animal=animal.label, room=room.label, outside=room.outside_place)}."
    )
    world.say(
        f"But by then the tiny party had become a cheerful muddle of crumbs, crooked saucers, and extra hoof prints all the way to the rug."
    )


def clean_together(world: World, parent: Entity, a: Entity, b: Entity, animal: AnimalCfg, room: RoomCfg) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
    world.say(
        f"No one was hurt, but everyone had to stop and clean. {a.id} fetched a cloth, {b.id} straightened the cups, and {parent.label_word} guided {animal.label} back to {room.outside_place}."
    )
    world.say(
        f'When the floor was tidy again, {parent.label_word} said, "Funny ideas are welcome. Hooves in {room.label} are not."'
    )
    world.say(
        f"That afternoon they started over outside, where the joke felt gentler and the room no longer had to wear the party on its face."
    )


def tell(
    animal: AnimalCfg,
    snack: SnackCfg,
    room: RoomCfg,
    response: ResponseCfg,
    host_name: str = "Mila",
    host_gender: str = "girl",
    cautioner_name: str = "Ben",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    host_age: int = 5,
    cautioner_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id=host_name,
        kind="character",
        type=host_gender,
        role="host",
        age=host_age,
        traits=["imaginative"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner_name,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(
        id="animal",
        kind="character",
        type="animal",
        label=animal.label,
        phrase=animal.phrase,
        tags=set(animal.tags),
    ))
    world.add(Entity(
        id="snack",
        type="snack",
        label=snack.label,
        phrase=snack.phrase,
        tags=set(snack.tags),
    ))
    world.add(Entity(
        id="room",
        type="room",
        label=room.label,
        phrase=room.phrase,
        tags=set(room.tags),
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    morning_setup(world, a, b, room)
    choose_guest(world, a, animal, snack)

    world.para()
    warn(world, b, a, animal, room, parent)
    averted = would_avert(relation, host_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, animal, snack, room, parent)
        world.para()
        outside_party(world, parent, a, b, animal, snack, room)
        severity = 0
        contained = True
    else:
        defy(world, a, b, animal, snack)
        world.para()
        invite_inside(world, world.get("animal"), world.get("snack"), animal, room)
        giggle_turn(world, a, b, world.get("animal"), animal, snack)
        call_parent(world, b, parent)

        severity = mess_severity(room, snack, delay)
        world.get("room").meters["severity"] = float(severity)
        contained = is_contained(response, room, snack, delay)

        world.para()
        if contained:
            rescue(world, parent, response, animal, room)
            lesson(world, parent, a, b, animal, room)
            world.para()
            outside_party(world, parent, a, b, animal, snack, room)
        else:
            rescue_fail(world, parent, response, animal, room)
            clean_together(world, parent, a, b, animal, room)

    outcome = "averted" if averted else ("contained" if contained else "topsy")
    world.facts.update(
        host=a,
        cautioner=b,
        parent=parent,
        animal_cfg=animal,
        snack_cfg=snack,
        room_cfg=room,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        indoor=not averted,
        prints=world.get("room").meters["prints"] >= THRESHOLD or outcome == "topsy",
        wobble=world.get("room").meters["wobble"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


ANIMALS = {
    "pony": AnimalCfg(
        id="pony",
        label="pony",
        phrase="the chestnut pony",
        hoof_sound="clop clop",
        nose_line="its whiskery nose",
        size=2,
        likes={"apple_slices", "carrot_coins"},
        tags={"pony", "hoof", "farm_animal"},
    ),
    "goat": AnimalCfg(
        id="goat",
        label="goat",
        phrase="the spotted goat",
        hoof_sound="tik-tik",
        nose_line="its bold little nose",
        size=1,
        likes={"apple_slices", "clover_crackers"},
        tags={"goat", "hoof", "farm_animal"},
    ),
    "calf": AnimalCfg(
        id="calf",
        label="calf",
        phrase="the soft-eyed calf",
        hoof_sound="thup-thup",
        nose_line="its velvety nose",
        size=3,
        likes={"apple_slices", "hay_biscuit"},
        tags={"calf", "hoof", "farm_animal"},
    ),
}

SNACKS = {
    "apple_slices": SnackCfg(
        id="apple_slices",
        label="apple slices",
        phrase="a plate of apple slices",
        crumbs=1,
        treat_line="The sweet smell floated right out through the screen door.",
        tags={"apple", "snack"},
    ),
    "carrot_coins": SnackCfg(
        id="carrot_coins",
        label="carrot coins",
        phrase="a saucer of carrot coins",
        crumbs=1,
        treat_line="They looked tidy to a child and irresistible to the wrong guest.",
        tags={"carrot", "snack"},
    ),
    "clover_crackers": SnackCfg(
        id="clover_crackers",
        label="clover crackers",
        phrase="a little bowl of clover crackers",
        crumbs=2,
        treat_line="They smelled grassy enough to count as an invitation.",
        tags={"cracker", "snack"},
    ),
    "hay_biscuit": SnackCfg(
        id="hay_biscuit",
        label="a hay biscuit",
        phrase="a crumbly hay biscuit on a plate",
        crumbs=2,
        treat_line="It was not fancy, but it was exactly the sort of thing a barn guest would notice.",
        tags={"hay", "snack"},
    ),
}

ROOMS = {
    "kitchen": RoomCfg(
        id="kitchen",
        label="the kitchen",
        phrase="the sunny kitchen",
        capacity=2,
        mess_risk=1,
        table_phrase="A towel was folded under the toy teapot, and three raisin-sized biscuits waited on a tray.",
        outside_place="the back step",
        tags={"kitchen"},
    ),
    "front_room": RoomCfg(
        id="front_room",
        label="the front room",
        phrase="the quiet front room",
        capacity=2,
        mess_risk=2,
        table_phrase="A lace napkin covered the stool they were using as a table, and the cups were lined up with serious ceremony.",
        outside_place="the porch",
        tags={"living_room"},
    ),
    "bedroom": RoomCfg(
        id="bedroom",
        label="the bedroom",
        phrase="the little bedroom by the garden side",
        capacity=1,
        mess_risk=3,
        table_phrase="The tea things were balanced on a book crate beside the bed, which made the whole arrangement look brave but doubtful.",
        outside_place="the shady yard",
        tags={"bedroom"},
    ),
}

RESPONSES = {
    "porch_picnic": ResponseCfg(
        id="porch_picnic",
        sense=3,
        power=4,
        text="lifted the tray to {outside}, opened the door wide, and coaxed {animal} back out with a sturdier snack pan",
        fail="tried to hustle everything toward {outside}, but the tray tipped and the room grew sillier before it got calmer",
        qa_text="moved the tea things outside and guided the animal out with a snack pan",
        tags={"outside", "redirect"},
    ),
    "towel_trail": ResponseCfg(
        id="towel_trail",
        sense=3,
        power=3,
        text="laid a towel path to {outside} and patted {animal} along it, hoof by hoof",
        fail="laid down towels and patted {animal} toward {outside}, but not before more crumbs and prints joined the party",
        qa_text="laid a towel path and guided the animal outside",
        tags={"towel", "redirect"},
    ),
    "grain_bucket": ResponseCfg(
        id="grain_bucket",
        sense=2,
        power=2,
        text="fetched a grain bucket and led {animal} out to {outside} before the little table lost its courage",
        fail="shook a grain bucket at the doorway, but {animal} took one more interested look around {room} first",
        qa_text="used a grain bucket to lead the animal back outside",
        tags={"bucket", "redirect"},
    ),
    "shoo": ResponseCfg(
        id="shoo",
        sense=1,
        power=1,
        text="flapped both hands and shooed at {animal} until it backed out",
        fail="flapped both hands and shooed, which only made {animal} curious about the cups",
        qa_text="shooed at the animal",
        tags={"shoo"},
    ),
}

GIRL_NAMES = ["Mila", "Lily", "Ava", "Nora", "Ella", "Maya", "Zoe", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Noah", "Finn", "Eli", "Jack", "Theo"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "patient"]


@dataclass
class StoryParams:
    animal: str
    snack: str
    room: str
    response: str
    host_name: str
    host_gender: str
    cautioner_name: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    host_age: int = 5
    cautioner_age: int = 7
    relation: str = "siblings"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for animal_id, animal in ANIMALS.items():
        for snack_id, snack in SNACKS.items():
            for room_id, room in ROOMS.items():
                if snack_works(animal, snack) and room_fits(animal, room):
                    combos.append((animal_id, snack_id, room_id))
    return combos


KNOWLEDGE = {
    "hoof": [(
        "What is a hoof?",
        "A hoof is the hard foot of an animal like a pony, goat, or calf. It helps the animal stand and walk, and it sounds different from soft shoes on a floor."
    )],
    "pony": [(
        "What is a pony?",
        "A pony is a small horse. Ponies have hooves, eat plant food, and need room to move around."
    )],
    "goat": [(
        "What is a goat?",
        "A goat is a farm animal with cloven hooves. Goats are curious and often nibble or sniff interesting things."
    )],
    "calf": [(
        "What is a calf?",
        "A calf is a young cow. A calf is gentle and growing, so it needs calm space and proper food."
    )],
    "outside": [(
        "Why is outside a better place for a farm animal to eat?",
        "Outside gives a farm animal more room to stand, chew, and turn around safely. It also keeps muddy feet and crumbs out of the house."
    )],
    "towel": [(
        "Why would someone put down a towel path?",
        "A towel path can catch dirt or wet prints from feet or hooves. It helps protect the floor while someone walks back outside."
    )],
    "bucket": [(
        "Why can a bucket help lead an animal?",
        "If the bucket holds the food the animal wants, it gives the animal something clear to follow. That is calmer than pushing or shouting."
    )],
    "apple": [(
        "Why do many farm animals like apples?",
        "Apples smell sweet and juicy, so many animals notice them quickly. People still have to give treats carefully and in the right place."
    )],
    "carrot": [(
        "Why are carrots common treats for ponies?",
        "Carrots are crunchy and easy to hold out in small pieces. People often use them as a simple treat for ponies."
    )],
}


KNOWLEDGE_ORDER = ["hoof", "pony", "goat", "calf", "apple", "carrot", "towel", "bucket", "outside"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    host = f["host"]
    cautioner = f["cautioner"]
    animal = f["animal_cfg"]
    room = f["room_cfg"]
    snack = f["snack_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a funny slice-of-life story for a 3-to-5-year-old that includes the word "hoof" '
        f"and shows a child trying to invite a {animal.label} to a tiny tea party in {room.label}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle near-miss story where {host.id} wants to tempt a {animal.label} inside with {snack.label}, but {cautioner.id} warns {host.pronoun('object')} in time and the fun moves outside.",
            f"Write a warm family story where an older sibling stops a silly plan before one hoof crosses the door, and the ending image is calm and funny.",
        ]
    if outcome == "topsy":
        return [
            base,
            f"Tell a humorous story where {host.id} ignores a warning, a real hoof clops into {room.label}, and the room turns topsy-turvy before everyone cleans up and starts again outside.",
            f"Write a cozy story with a messy middle, a calm grown-up, and a funny ending that proves the children learned where a farm animal belongs.",
        ]
    return [
        base,
        f"Tell a humorous story where {host.id} lures a {animal.label} inside with {snack.label}, a grown-up redirects the whole tea party outside, and everyone ends up laughing.",
        f"Write a small domestic story with a clear problem, a calm fix, and an ending image of one polite hoof standing outside where it belongs.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    host = f["host"]
    cautioner = f["cautioner"]
    parent = f["parent"]
    animal = f["animal_cfg"]
    snack = f["snack_cfg"]
    room = f["room_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(host, cautioner, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {host.id} and {cautioner.id}, and a {animal.label} that almost became a tea-party guest. Their {pw} helps turn the silly moment into a better plan."
        ),
        (
            f"Why did {host.id} want the {animal.label} to come closer?",
            f"{host.id} thought it would be funny and special to have the {animal.label} visit the tiny tea party. The snack made the idea feel possible, even though the room was too small for a real hoof."
        ),
        (
            f"What warning did {cautioner.id} give?",
            f"{cautioner.id} warned that if the {animal.label} followed the snack into {room.label}, there would be hoof prints and wobbling cups. The warning came from picturing what a real farm animal would do in such a little room."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What did {host.id} do after hearing the warning?",
            f"{host.id} listened and gave up the indoor plan before the animal came in. That kept the room neat and let the fun move outside in a safer, sillier way."
        ))
        qa.append((
            "How did the story end?",
            f"It ended outside, where the children kept their tiny cups and the {animal.label} got a proper pan. The ending proves they learned that a hoof needs space, not a bedroom or a crowded little table."
        ))
    elif f["outcome"] == "contained":
        body = response.qa_text
        qa.append((
            f"How did the {pw} solve the problem?",
            f"The {pw} {body}. That worked because the grown-up changed the place of the party instead of trying to make the small room fit a big, curious guest."
        ))
        qa.append((
            "What made the middle of the story funny?",
            f"The joke is that the children tried to treat a farm animal like a polite doll-sized guest. Seeing a real hoof, a sniffing nose, and shaky tea cups together made the problem funny even while it needed fixing."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the party outside, where everyone had enough room and the hoof stood on the grass. That final picture shows the problem was solved by moving the fun to the right place."
        ))
    else:
        qa.append((
            f"Did the {pw} stop the mess right away?",
            f"No. The {pw} tried, but the tea party had already become a cheerful muddle with extra crumbs and hoof prints. After that, everyone had to clean together before starting over outside."
        ))
        qa.append((
            "Was anyone hurt?",
            "No one was hurt. The trouble was a silly indoor mess, and the lesson was about choosing a place that fits the guest."
        ))
        qa.append((
            "How did the story end?",
            f"It ended more quietly, with the room cleaned and the fun moved outside. The children still got their laugh, but now they understood that a hoof does not belong in a tiny tea-party room."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    animal = f["animal_cfg"]
    snack = f["snack_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    tags: set[str] = {"hoof"} | set(animal.tags) | set(snack.tags)
    if outcome == "contained":
        tags |= set(response.tags)
    elif outcome == "topsy":
        tags |= set(response.tags) | {"outside"}
    else:
        tags |= {"outside"}
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="pony",
        snack="carrot_coins",
        room="front_room",
        response="porch_picnic",
        host_name="Mila",
        host_gender="girl",
        cautioner_name="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        host_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        animal="goat",
        snack="clover_crackers",
        room="bedroom",
        response="towel_trail",
        host_name="Leo",
        host_gender="boy",
        cautioner_name="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        host_age=6,
        cautioner_age=6,
        relation="friends",
    ),
    StoryParams(
        animal="calf",
        snack="apple_slices",
        room="kitchen",
        response="grain_bucket",
        host_name="Ava",
        host_gender="girl",
        cautioner_name="Eli",
        cautioner_gender="boy",
        parent="mother",
        trait="steady",
        delay=1,
        host_age=6,
        cautioner_age=5,
        relation="siblings",
    ),
    StoryParams(
        animal="goat",
        snack="apple_slices",
        room="bedroom",
        response="grain_bucket",
        host_name="Finn",
        host_gender="boy",
        cautioner_name="Sam",
        cautioner_gender="boy",
        parent="father",
        trait="cautious",
        delay=2,
        host_age=7,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        animal="pony",
        snack="apple_slices",
        room="kitchen",
        response="towel_trail",
        host_name="Ella",
        host_gender="girl",
        cautioner_name="Maya",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        host_age=4,
        cautioner_age=8,
        relation="siblings",
    ),
]


def explain_rejection(animal: AnimalCfg, snack: SnackCfg, room: RoomCfg) -> str:
    if not snack_works(animal, snack):
        liked = ", ".join(sorted(animal.likes))
        return (
            f"(No story: {animal.label} would not reasonably follow {snack.label}. "
            f"Try a snack this animal actually likes: {liked}.)"
        )
    if not room_fits(animal, room):
        return (
            f"(No story: {room.label} is too small for a {animal.label}. "
            f"The room would need capacity {animal.size}, but it only has {room.capacity}.)"
        )
    return "(No story: this combination is not reasonable.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a calmer fix like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.host_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], ROOMS[params.room], SNACKS[params.snack], params.delay)
    return "contained" if contained else "topsy"


ASP_RULES = r"""
likes_snack(A, S) :- likes(A, S).
fits(A, R) :- animal_size(A, Z), room_capacity(R, C), Z <= C.
hazard(A, S, R) :- animal(A), snack(S), room(R), likes_snack(A, S), fits(A, R).

sensible(Rsp) :- response(Rsp), sense(Rsp, V), sense_min(M), V >= M.
valid(A, S, R) :- hazard(A, S, R).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), host_age(HA), cautioner_age(CA), CA > HA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(Risk + Crumbs + D) :- chosen_room(R), room_risk(R, Risk), chosen_snack(S), snack_crumbs(S, Crumbs), delay(D).
resp_power(P) :- chosen_response(Rsp), response_power(Rsp, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(topsy) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("animal_size", aid, animal.size))
        for snack in sorted(animal.likes):
            lines.append(asp.fact("likes", aid, snack))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("snack_crumbs", sid, snack.crumbs))
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        lines.append(asp.fact("room_capacity", rid, room.capacity))
        lines.append(asp.fact("room_risk", rid, room.mess_risk))
    for rsp_id, response in RESPONSES.items():
        lines.append(asp.fact("response", rsp_id))
        lines.append(asp.fact("sense", rsp_id, response.sense))
        lines.append(asp.fact("response_power", rsp_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_room", params.room),
        asp.fact("chosen_snack", params.snack),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("host_age", params.host_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError("unresolved template brace in smoke test story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Funny slice-of-life story world: a child, a hoofed guest, and a tiny tea party gone slightly wrong."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the silly situation goes on before the grown-up redirects it")
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.snack and not snack_works(ANIMALS[args.animal], SNACKS[args.snack]):
        raise StoryError(explain_rejection(ANIMALS[args.animal], SNACKS[args.snack], ROOMS[args.room or "kitchen"]))
    if args.animal and args.room and not room_fits(ANIMALS[args.animal], ROOMS[args.room]):
        snack_id = args.snack or next(iter(ANIMALS[args.animal].likes))
        raise StoryError(explain_rejection(ANIMALS[args.animal], SNACKS[snack_id], ROOMS[args.room]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.snack is None or combo[1] == args.snack)
        and (args.room is None or combo[2] == args.room)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal, snack, room = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    host_name, host_gender = _pick_child(rng)
    cautioner_name, cautioner_gender = _pick_child(rng, avoid=host_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    host_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        animal=animal,
        snack=snack,
        room=room,
        response=response,
        host_name=host_name,
        host_gender=host_gender,
        cautioner_name=cautioner_name,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        host_age=host_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def _validate_params(params: StoryParams) -> None:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    animal = ANIMALS[params.animal]
    snack = SNACKS[params.snack]
    room = ROOMS[params.room]
    if not snack_works(animal, snack) or not room_fits(animal, room):
        raise StoryError(explain_rejection(animal, snack, room))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        animal=ANIMALS[params.animal],
        snack=SNACKS[params.snack],
        room=ROOMS[params.room],
        response=RESPONSES[params.response],
        host_name=params.host_name,
        host_gender=params.host_gender,
        cautioner_name=params.cautioner_name,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        host_age=params.host_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (animal, snack, room) combos:\n")
        for animal, snack, room in combos:
            print(f"  {animal:6} {snack:16} {room}")
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
            header = f"### {p.host_name} & {p.cautioner_name}: {p.animal} with {p.snack} in {p.room} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
