#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/group_transfer_curiosity_sound_effects_pirate_tale.py
=================================================================================

A standalone story world for a tiny pirate-play domain built from the seed words
"group" and "transfer", with curiosity and sound effects as core story forces.

Premise
-------
A small group of children is playing pirates indoors. They hear a mysterious
treasure sound from a container set up high above them. Their curiosity grows.
One child wants to climb and transfer the treasure into the crew's pirate chest
right away. Another child warns that the high reach is risky. Depending on the
children's relationship, the container, and the delay before help, the risky
idea is either stopped in time, or it leads to a spill, or the container breaks.
A calm grown-up then helps the group finish the transfer the safe way.

World-model commitments
-----------------------
- Entities carry physical meters and emotional memes.
- Curiosity is driven by a heard sound, not by a static template.
- The middle turn is stateful: a wobble can become a drop; a drop can become a
  spill; a breakable source can shatter.
- The ending image proves what changed: the group now transfers treasure safely,
  on the floor, with help and a sensible method.

Run it
------
    python storyworlds/worlds/gpt-5.4/group_transfer_curiosity_sound_effects_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/group_transfer_curiosity_sound_effects_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/group_transfer_curiosity_sound_effects_pirate_tale.py --verify
    python storyworlds/worlds/gpt-5.4/group_transfer_curiosity_sound_effects_pirate_tale.py --qa --json
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
BOLDNESS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    goal: str
    send_off: str
    crew_word: str


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    sound: str
    listen_line: str
    size: str
    move_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    place: str
    material: str
    breakable: bool = False
    heavy: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    mouth: str = "wide"
    accepts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    precise: bool = False
    sense: int = 2
    success_text: str = ""
    qa_text: str = ""
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_drop_from_wobble(world: World) -> list[str]:
    src = world.get("source")
    if src.meters["lifted_high"] < THRESHOLD or src.meters["wobble"] < THRESHOLD:
        return []
    sig = ("drop", src.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    src.meters["dropped"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__drop__"]


def _r_spill_from_drop(world: World) -> list[str]:
    src = world.get("source")
    if src.meters["dropped"] < THRESHOLD:
        return []
    sig = ("spill", src.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    src.meters["spilled"] += 1
    world.get("room").meters["mess"] += 1
    return ["__spill__"]


def _r_break_from_drop(world: World) -> list[str]:
    src = world.get("source")
    if src.meters["dropped"] < THRESHOLD or not src.attrs.get("breakable", False):
        return []
    sig = ("break", src.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    src.meters["broken"] += 1
    world.get("room").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__break__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="drop_from_wobble", tag="physical", apply=_r_drop_from_wobble),
    Rule(name="spill_from_drop", tag="physical", apply=_r_spill_from_drop),
    Rule(name="break_from_drop", tag="physical", apply=_r_break_from_drop),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s.startswith("__"):
                continue
            world.say(s)
    return produced


def sound_worthy(treasure: Treasure) -> bool:
    return bool(treasure.sound)


def destination_fits(treasure: Treasure, destination: Destination) -> bool:
    return treasure.size in destination.accepts


def method_fits(treasure: Treasure, destination: Destination, method: Method) -> bool:
    if treasure.move_kind not in method.handles:
        return False
    if destination.mouth == "narrow" and not method.precise:
        return False
    return True


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for treasure_id, treasure in TREASURES.items():
            for destination_id, destination in DESTINATIONS.items():
                for method_id, method in METHODS.items():
                    if not sound_worthy(treasure):
                        continue
                    if method.sense < SENSE_MIN:
                        continue
                    if destination_fits(treasure, destination) and method_fits(treasure, destination, method):
                        combos.append((theme_id, treasure_id, destination_id, method_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BOLDNESS_INIT


def risk_score(source: Source, delay: int) -> int:
    return source.heavy + delay + (1 if source.breakable else 0)


def outcome_of(params: "StoryParams") -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "broken" if risk_score(SOURCES[params.source], params.delay) >= 4 else "spilled"


def predict_mishap(world: World) -> dict:
    sim = world.copy()
    src = sim.get("source")
    src.meters["lifted_high"] += 1
    src.meters["wobble"] += 1
    propagate(sim, narrate=False)
    return {
        "drops": src.meters["dropped"] >= THRESHOLD,
        "spills": src.meters["spilled"] >= THRESHOLD,
        "breaks": src.meters["broken"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme, crew_count: int) -> None:
    for kid in world.kids():
        kid.memes["joy"] += 1
    more = "The whole group felt ready for adventure." if crew_count > 2 else "Their tiny crew felt ready for adventure."
    world.say(
        f"One afternoon, {a.id} and {b.id} turned the living room into {theme.scene}. "
        f"{theme.rig} {more}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} shouted. '
        f'"Let\'s gather treasure for the {theme.goal}!"'
    )


def hear_mystery(world: World, a: Entity, b: Entity, source: Source, treasure: Treasure) -> None:
    for kid in world.kids():
        kid.memes["curiosity"] += 1
    world.say(
        f"Then a curious sound came from {source.place}: {treasure.sound}! "
        f"{b.id} looked up at {source.phrase}, and both children froze to listen."
    )
    world.say(
        f'"What is in there?" {b.id} whispered. {treasure.listen_line}'
    )


def tempt_transfer(world: World, a: Entity, source: Source, destination: Destination, treasure: Treasure) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'{a.id}\'s eyes shone. "Maybe it is pirate treasure! We can transfer the '
        f'{treasure.label} from {source.phrase} into {destination.phrase} for our whole group."'
    )
    world.say("For one breath, the plan sounded clever and quick.")


def warn(world: World, b: Entity, a: Entity, parent: Entity, source: Source) -> None:
    pred = predict_mishap(world)
    b.memes["caution"] += 1
    world.facts["pred_breaks"] = pred["breaks"]
    extra = ""
    if pred["breaks"]:
        extra = f" If it fell, the {source.material} could break."
    world.say(
        f'{b.id} frowned. "{a.id}, don\'t climb for it. {parent.label_word.capitalize()} should help us bring it down first. '
        f'That chair could wobble, and everything might spill.{extra}"'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["boldness"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} opened {a.pronoun("possessive")} mouth to argue, then looked at {b.id} and stopped. '
        f'"You are right," {a.pronoun()} said. "Let\'s call {parent.label_word}."'
    )


def defy(world: World, a: Entity, source_ent: Entity) -> None:
    a.memes["defiance"] += 1
    source_ent.meters["lifted_high"] += 1
    source_ent.meters["wobble"] += 1
    world.say(
        f'"I can do it myself," {a.id} said. {a.pronoun().capitalize()} scrambled onto the chair and reached for the container.'
    )
    world.say("Creak... wobble... wobble...")


def tumble(world: World, source: Source, treasure: Treasure) -> None:
    src = world.get("source")
    if src.meters["dropped"] < THRESHOLD:
        return
    if src.meters["broken"] >= THRESHOLD:
        world.say(
            f"Thump! Crash! {source.phrase.capitalize()} slipped from small hands, hit the floor, and broke open. "
            f"{treasure.sound} went skittering everywhere."
        )
    else:
        world.say(
            f"Thump! Clatter! {source.phrase.capitalize()} slipped from small hands and spilled across the rug. "
            f"{treasure.sound} bounced in every direction."
        )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    cry = "It broke!" if world.get("source").meters["broken"] >= THRESHOLD else "It spilled!"
    world.say(f'"{parent.label_word.upper()}! {cry}" {b.id} cried.')


def parent_arrives(world: World, parent: Entity, source: Source) -> None:
    if source.breakable and world.get("source").meters["broken"] >= THRESHOLD:
        world.say(
            f"{parent.label_word.capitalize()} came quickly, saw the broken {source.material} on the floor, and held up a careful hand."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} came quickly and knelt beside the scattered treasure."
        )


def safe_transfer(world: World, parent: Entity, method: Method, destination: Destination, treasure: Treasure) -> None:
    src = world.get("source")
    src.meters["transferred"] += 1
    src.meters["spilled"] = 0.0
    world.get("room").meters["mess"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = method.success_text.format(destination=destination.label, treasure=treasure.label)
    world.say(
        f"{parent.label_word.capitalize()} {body}."
    )
    world.say(
        f"Soon the {treasure.label} rested in {destination.phrase}, ready for the crew instead of scattered on the floor."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, source: Source) -> None:
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    sharp = ""
    if source.breakable and world.facts.get("outcome") == "broken":
        sharp = " Broken things can have sharp edges, so only a grown-up should handle them."
    world.say(
        f'{parent.label_word.capitalize()} hugged the little crew close. "I am glad you called me," {parent.pronoun()} said softly. '
        f'"Curiosity is fine, but climbing for heavy things is not safe.{sharp}"'
    )
    world.say(
        f'"Next time," said {b.id}, "we ask first and transfer treasure on the floor."'
    )
    world.say(f'{a.id} nodded. "A real pirate group can wait for the safe way."')


def bright_ending(world: World, a: Entity, b: Entity, theme: Theme, destination: Destination, treasure: Treasure) -> None:
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"At last {a.id} tipped {destination.phrase} just enough for the crew to admire the prize, and {treasure.sound} answered one last time."
    )
    world.say(
        f'The children grinned. "{theme.crew_word.capitalize()}, away!" they cheered, and {theme.send_off} with their treasure safe at the center.'
    )


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a windy pirate deck",
        rig="The sofa was their ship, a striped blanket was their sail, and a cardboard map pointed to a hidden chest.",
        captain="Captain",
        mate="First Mate",
        goal="captain's chest",
        send_off="the pirate game sailed on",
        crew_word="crew",
    ),
    "islanders": Theme(
        id="islanders",
        scene="a bright island cove",
        rig="The rug was the sandy shore, two chairs made a lookout tower, and a cardboard box waited as a treasure hold.",
        captain="Captain",
        mate="Lookout",
        goal="treasure hold",
        send_off="the little ship set off for the island cave",
        crew_word="crew",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a moonlit pirate harbor",
        rig="The coffee table became a dock, the sofa became a black ship, and a paper map curled toward an X in the corner.",
        captain="Captain",
        mate="Scout",
        goal="sea chest",
        send_off="their daring game drifted on into calmer waters",
        crew_word="group",
    ),
}

TREASURES = {
    "coins": Treasure(
        id="coins",
        label="coins",
        phrase="a pile of shiny coins",
        sound="Clink-clink",
        listen_line="The sound was bright and sharp, like tiny bells in a pocket.",
        size="small",
        move_kind="tiny",
        tags={"coins", "sound", "treasure"},
    ),
    "buttons": Treasure(
        id="buttons",
        label="buttons",
        phrase="a heap of bright buttons",
        sound="Clickety-click",
        listen_line="It sounded like little taps from a secret stash.",
        size="small",
        move_kind="tiny",
        tags={"buttons", "sound", "treasure"},
    ),
    "shells": Treasure(
        id="shells",
        label="shells",
        phrase="a handful of striped shells",
        sound="Clatter-clatter",
        listen_line="The sound was hollow and beachy, as if the sea had come indoors.",
        size="large",
        move_kind="large",
        tags={"shells", "sound", "treasure"},
    ),
    "marbles": Treasure(
        id="marbles",
        label="marbles",
        phrase="a cluster of glass marbles",
        sound="Tik-tik-tik",
        listen_line="The sound danced lightly, like hard little stars tapping together.",
        size="small",
        move_kind="rolling",
        tags={"marbles", "sound", "treasure"},
    ),
    "feathers": Treasure(
        id="feathers",
        label="feathers",
        phrase="a bunch of soft feathers",
        sound="",
        listen_line="There was almost no sound at all.",
        size="large",
        move_kind="light",
        tags={"feathers"},
    ),
}

SOURCES = {
    "glass_jar": Source(
        id="glass_jar",
        label="glass jar",
        phrase="the tall glass jar",
        place="the high bookshelf",
        material="glass",
        breakable=True,
        heavy=2,
        tags={"glass", "high_shelf"},
    ),
    "metal_tin": Source(
        id="metal_tin",
        label="metal tin",
        phrase="the old metal tin",
        place="the top shelf",
        material="metal",
        breakable=False,
        heavy=2,
        tags={"metal", "high_shelf"},
    ),
    "wooden_box": Source(
        id="wooden_box",
        label="wooden box",
        phrase="the small wooden box",
        place="the mantel",
        material="wood",
        breakable=False,
        heavy=1,
        tags={"wood", "high_place"},
    ),
}

DESTINATIONS = {
    "chest": Destination(
        id="chest",
        label="treasure chest",
        phrase="the little pirate chest",
        mouth="wide",
        accepts={"small", "large"},
        tags={"chest"},
    ),
    "pouch": Destination(
        id="pouch",
        label="treasure pouch",
        phrase="the striped treasure pouch",
        mouth="wide",
        accepts={"small", "large"},
        tags={"pouch"},
    ),
    "bottle": Destination(
        id="bottle",
        label="message bottle",
        phrase="the message bottle",
        mouth="narrow",
        accepts={"small"},
        tags={"bottle"},
    ),
}

METHODS = {
    "scoop": Method(
        id="scoop",
        label="small scoop",
        phrase="a small scoop",
        handles={"tiny", "rolling"},
        precise=True,
        sense=3,
        success_text="set the container on the floor and used a small scoop to move the {treasure} into the {destination}, one calm scoop at a time",
        qa_text="set the container on the floor and used a small scoop to transfer the treasure",
        tags={"scoop", "transfer"},
    ),
    "funnel": Method(
        id="funnel",
        label="paper funnel",
        phrase="a paper funnel",
        handles={"tiny", "rolling"},
        precise=True,
        sense=3,
        success_text="made a paper funnel and guided the {treasure} neatly into the {destination}",
        qa_text="made a paper funnel and guided the treasure into the destination",
        tags={"funnel", "transfer"},
    ),
    "hands": Method(
        id="hands",
        label="careful hands",
        phrase="careful hands",
        handles={"large"},
        precise=False,
        sense=2,
        success_text="brought the container down first and let everyone use careful hands to place the {treasure} into the {destination}",
        qa_text="brought the container down first and let everyone use careful hands to transfer the treasure",
        tags={"hands", "transfer"},
    ),
    "shake": Method(
        id="shake",
        label="shaking and pouring",
        phrase="shaking and pouring",
        handles={"tiny", "rolling", "large"},
        precise=False,
        sense=1,
        success_text="shook everything out quickly",
        qa_text="shook everything out quickly",
        tags={"bad_transfer"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "curious", "steady", "thoughtful", "sensible"]
COMFORTS = ["stuffed rabbit", "little octopus toy", "floppy bear", "plush parrot"]
PETS = ["the cat", "the puppy", "the kitten", "their little dog"]


@dataclass
class StoryParams:
    theme: str
    treasure: str
    source: str
    destination: str
    method: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    crew_count: int = 2
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    comfort: str = ""
    pet: str = ""
    seed: Optional[int] = None


def tell(
    theme: Theme,
    treasure: Treasure,
    source: Source,
    destination: Destination,
    method: Method,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    crew_count: int = 2,
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    comfort: str = "",
    pet: str = "",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation, "comfort": comfort},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    source_ent = world.add(Entity(
        id="source",
        type="container",
        label=source.label,
        phrase=source.phrase,
        attrs={"breakable": source.breakable, "material": source.material},
        tags=set(source.tags),
    ))
    dest_ent = world.add(Entity(
        id="destination",
        type="container",
        label=destination.label,
        phrase=destination.phrase,
        tags=set(destination.tags),
    ))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts["pet"] = pet

    play_setup(world, a, b, theme, crew_count)
    hear_mystery(world, a, b, source, treasure)

    world.para()
    tempt_transfer(world, a, source, destination, treasure)
    warn(world, b, a, parent, source)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent)
        world.para()
        world.say(
            f"{parent.label_word.capitalize()} reached up, brought {source.phrase} down safely, and set it on the rug where small hands could help."
        )
        safe_transfer(world, parent, method, destination, treasure)
        lesson(world, parent, a, b, source)
        world.para()
        bright_ending(world, a, b, theme, destination, treasure)
    else:
        defy(world, a, source_ent)
        for _ in range(delay):
            source_ent.meters["wobble"] += 1
        propagate(world, narrate=False)

        world.para()
        tumble(world, source, treasure)
        alarm(world, b, parent)

        world.para()
        parent_arrives(world, parent, source)
        safe_transfer(world, parent, method, destination, treasure)
        lesson(world, parent, a, b, source)
        world.para()
        bright_ending(world, a, b, theme, destination, treasure)

    outcome = outcome_of(StoryParams(
        theme=theme.id,
        treasure=treasure.id,
        source=source.id,
        destination=destination.id,
        method=method.id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent_type,
        trait=trait,
        delay=delay,
        crew_count=crew_count,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        comfort=comfort,
        pet=pet,
    ))
    world.facts.update(
        theme=theme,
        treasure=treasure,
        source_cfg=source,
        destination_cfg=destination,
        method=method,
        instigator=a,
        cautioner=b,
        parent=parent,
        destination=dest_ent,
        source=source_ent,
        outcome=outcome,
        relation=relation,
        crew_count=crew_count,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "treasure": [(
        "What is treasure in a pretend pirate game?",
        "Treasure is a special thing the pirates want to find or protect, like shiny coins, shells, or bright buttons in a game."
    )],
    "sound": [(
        "How can sound help you guess what is in a container?",
        "Different things make different sounds when they tap together. Listening can give you a clue before you look."
    )],
    "transfer": [(
        "What does transfer mean?",
        "Transfer means moving something from one place or container to another place or container."
    )],
    "glass": [(
        "Why do people need to be careful with glass?",
        "Glass can break into sharp pieces if it falls. That is why a grown-up should handle broken glass."
    )],
    "scoop": [(
        "What is a scoop good for?",
        "A scoop helps you move lots of little things carefully. It is useful when tiny pieces would be hard to pick up one by one."
    )],
    "funnel": [(
        "What does a funnel do?",
        "A funnel helps guide little things into a small opening. It keeps them from bouncing or spilling so much."
    )],
    "hands": [(
        "When are careful hands enough to move something?",
        "Careful hands work best for bigger pieces that are easy to hold, like shells. Tiny rolling things often need a tool."
    )],
    "help": [(
        "Why should children ask a grown-up before climbing for something high?",
        "Things up high can be heavy, wobbly, or breakable. A grown-up can bring them down more safely."
    )],
}


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
    a = f["instigator"]
    b = f["cautioner"]
    treasure = f["treasure"]
    destination = f["destination_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-play story for a 3-to-5-year-old where a curious group hears "{treasure.sound}" from a mystery container and wants to transfer treasure into {destination.phrase}. Include the word "group" and the word "transfer".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle pirate tale where {a.id} wants to climb for the treasure, but {b.id} wisely stops the risky plan and a grown-up helps the group transfer it safely.",
            f"Write a story driven by curiosity and sound effects, where the crew learns that asking first is better than rushing.",
        ]
    if outcome == "broken":
        return [
            base,
            f"Tell a cautionary pirate story where {a.id} ignores a warning, the container falls and breaks, and then a grown-up helps the group finish the transfer the safe way.",
            f"Write a story with a sharp middle turn, sound effects, and a calm ending image that proves the children changed their plan.",
        ]
    return [
        base,
        f"Tell a pirate-play story where {a.id} rushes, the treasure spills, and then a grown-up helps the group transfer it carefully into {destination.phrase}.",
        f"Write a simple story full of curiosity and little sounds, ending with the crew using a safer method on the floor.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    treasure = f["treasure"]
    source = f["source_cfg"]
    destination = f["destination_cfg"]
    method = f["method"]
    outcome = f["outcome"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were pretending to be pirates with a curious little group. Their {parent.label_word} helped when the treasure plan became risky."
        ),
        (
            "What made the children curious?",
            f"They heard {treasure.sound} from {source.phrase} up high. The mysterious sound made them wonder what treasure was hidden inside."
        ),
        (
            "What did the children want to do?",
            f"They wanted to transfer the {treasure.label} into {destination.phrase} for their pirate group. The transfer felt exciting because it would make their game seem more real."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned {a.id} because the container was up high and the chair could wobble. {b.pronoun().capitalize()} could tell that a spill, or even a break, might happen if they rushed."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What happened after the warning?",
            f"{a.id} listened and backed down, so nothing fell at all. Then their {parent.label_word} brought the container down safely and helped the group transfer the treasure on the floor."
        ))
    elif outcome == "spilled":
        qa.append((
            "What went wrong in the middle of the story?",
            f"The container slipped and the {treasure.label} spilled across the rug. That happened because {a.id} tried to reach for it from up high instead of waiting for help."
        ))
    else:
        qa.append((
            "What went wrong in the middle of the story?",
            f"The container fell, broke, and the {treasure.label} scattered everywhere. It became more dangerous because the broken {source.material} needed careful grown-up hands."
        ))
    qa.append((
        f"How did {parent.label_word} solve the problem?",
        f"{parent.label_word.capitalize()} {method.qa_text}. The grown-up changed the risky high reach into a calm, safe transfer on the floor."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with the treasure safe in {destination.phrase} and the children ready to keep playing. The last image shows that the group had learned a safer way to be curious."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"treasure", "sound", "transfer", "help"}
    source = f["source_cfg"]
    method = f["method"]
    if source.breakable:
        tags.add("glass")
    tags |= set(method.tags)
    ordered = ["treasure", "sound", "transfer", "glass", "scoop", "funnel", "hands", "help"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:11} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        treasure="coins",
        source="wooden_box",
        destination="chest",
        method="scoop",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        crew_count=3,
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        comfort="stuffed rabbit",
        pet="the puppy",
    ),
    StoryParams(
        theme="islanders",
        treasure="shells",
        source="metal_tin",
        destination="pouch",
        method="hands",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="steady",
        delay=0,
        crew_count=4,
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        comfort="",
        pet="",
    ),
    StoryParams(
        theme="corsairs",
        treasure="marbles",
        source="glass_jar",
        destination="bottle",
        method="funnel",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        crew_count=3,
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        comfort="little octopus toy",
        pet="the cat",
    ),
]


def explain_rejection_treasure(treasure: Treasure) -> str:
    return (
        f"(No story: {treasure.phrase} would not make a clear mystery sound, so curiosity-by-listening would be weak. "
        f"Pick treasure like coins, shells, buttons, or marbles.)"
    )


def explain_rejection_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of the safer transfer methods: {better}.)"
    )


def explain_rejection_combo(treasure: Treasure, destination: Destination, method: Method) -> str:
    if not destination_fits(treasure, destination):
        return (
            f"(No story: {treasure.label} are not a good fit for {destination.phrase}. "
            f"The destination opening or shape does not suit that treasure.)"
        )
    return (
        f"(No story: {method.phrase} is not a sensible way to move {treasure.label} into {destination.phrase}. "
        f"Pick a method that matches the treasure and the opening.)"
    )


ASP_RULES = r"""
sound_worthy(T) :- treasure(T), makes_sound(T).
destination_fits(T, D) :- treasure_size(T, S), accepts(D, S).
method_fits(T, D, M) :- move_kind(T, K), handles(M, K),
                        destination_mouth(D, wide), method(M).
method_fits(T, D, M) :- move_kind(T, K), handles(M, K),
                        destination_mouth(D, narrow), precise(M).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

valid(Th, T, D, M) :- theme(Th), treasure(T), destination(D), method(M),
                      sound_worthy(T), destination_fits(T, D), method_fits(T, D, M),
                      sensible(M).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), boldness_init(BI), A > BI.

risk(H + D + B) :- chosen_source(S), heavy(S, H), delay(D), source_break_bonus(S, B).

outcome(averted) :- averted.
outcome(broken) :- not averted, risk(R), R >= 4.
outcome(spilled) :- not averted, risk(R), R < 4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        if sound_worthy(treasure):
            lines.append(asp.fact("makes_sound", treasure_id))
        lines.append(asp.fact("treasure_size", treasure_id, treasure.size))
        lines.append(asp.fact("move_kind", treasure_id, treasure.move_kind))
    for destination_id, destination in DESTINATIONS.items():
        lines.append(asp.fact("destination", destination_id))
        lines.append(asp.fact("destination_mouth", destination_id, destination.mouth))
        for size in sorted(destination.accepts):
            lines.append(asp.fact("accepts", destination_id, size))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.precise:
            lines.append(asp.fact("precise", method_id))
        for handle in sorted(method.handles):
            lines.append(asp.fact("handles", method_id, handle))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("heavy", source_id, source.heavy))
        lines.append(asp.fact("source_break_bonus", source_id, 1 if source.breakable else 0))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: curious pirate-play children hear treasure sounds, risk a high reach, and learn a safer transfer."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra wobble before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treasure and not sound_worthy(TREASURES[args.treasure]):
        raise StoryError(explain_rejection_treasure(TREASURES[args.treasure]))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_rejection_method(args.method))
    if args.treasure and args.destination and args.method:
        treasure = TREASURES[args.treasure]
        destination = DESTINATIONS[args.destination]
        method = METHODS[args.method]
        if not (destination_fits(treasure, destination) and method_fits(treasure, destination, method)):
            raise StoryError(explain_rejection_combo(treasure, destination, method))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.treasure is None or combo[1] == args.treasure)
        and (args.destination is None or combo[2] == args.destination)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, treasure_id, destination_id, method_id = rng.choice(sorted(combos))
    source_id = args.source or rng.choice(sorted(SOURCES))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    crew_count = rng.choice([2, 3, 4])
    comfort = rng.choice(COMFORTS + ["", ""])
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        theme=theme_id,
        treasure=treasure_id,
        source=source_id,
        destination=destination_id,
        method=method_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        crew_count=crew_count,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        comfort=comfort,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        treasure = TREASURES[params.treasure]
        source = SOURCES[params.source]
        destination = DESTINATIONS[params.destination]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not sound_worthy(treasure):
        raise StoryError(explain_rejection_treasure(treasure))
    if method.sense < SENSE_MIN:
        raise StoryError(explain_rejection_method(params.method))
    if not destination_fits(treasure, destination) or not method_fits(treasure, destination, method):
        raise StoryError(explain_rejection_combo(treasure, destination, method))

    world = tell(
        theme=theme,
        treasure=treasure,
        source=source,
        destination=destination,
        method=method,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        crew_count=params.crew_count,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        comfort=params.comfort,
        pet=params.pet,
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

    c_sens = set(asp_sensible_methods())
    p_sens = {m.id for m in sensible_methods()}
    if c_sens == p_sens:
        print(f"OK: sensible methods match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(120):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
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

    smoke = CURATED[0]
    try:
        sample = generate(smoke)
        emit(sample, trace=False, qa=False, header="")
        print("\nOK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, treasure, destination, method) combos:\n")
        for theme, treasure, destination, method in combos:
            print(f"  {theme:10} {treasure:8} {destination:11} {method}")
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.treasure} from {p.source} "
                f"to {p.destination} ({p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
