#!/usr/bin/env python3
"""Petting-zoo ghost story where friendship quiets a lonely shackle."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


INTERNAL_SOURCE_TALE = (
    "At closing time in a petting zoo, two children hear a lonely shackle tap from a pen "
    "that should be empty. A ghost animal is not angry, only stuck to a missing keepsake "
    "and the feeling of being left alone. The children answer with a small act of "
    "friendship, return the keepsake, and stay beside the ghost until the shackle falls quiet."
)


@dataclass(frozen=True)
class Enclosure:
    key: str
    phrase: str
    smell: str
    closing_task: str
    moon_image: str


@dataclass(frozen=True)
class Gesture:
    key: str
    phrase: str
    action_template: str
    comfort_result: str
    courage_delta: float
    friendship_delta: float
    glow_delta: float


@dataclass(frozen=True)
class GhostAnimal:
    key: str
    name: str
    kind: str
    enclosure: str
    shackle_phrase: str
    charm_phrase: str
    clue_place: str
    entry_image: str
    memory_sentence: str
    final_image: str
    favorite_treat: str
    allowed_gestures: frozenset[str]


@dataclass
class StoryParams:
    enclosure: str
    ghost: str
    gesture: str
    hero: str
    friend: str
    caretaker: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    location: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    subject: str
    location: str
    target: str | None = None
    tags: tuple[str, ...] = ()


@dataclass
class World:
    params: StoryParams
    enclosure: Enclosure
    ghost_spec: GhostAnimal
    gesture: Gesture
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "mist": 0.65,
            "lantern_glow": 0.35,
            "shackle_tension": 1.0,
            "zoo_hush": 0.55,
        }
    )
    facts: dict[str, str] = field(default_factory=dict)
    fired: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def bump_world(self, key: str, delta: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + delta, 3)

    def bump_entity_meter(self, entity_id: str, key: str, delta: float) -> None:
        entity = self.entities[entity_id]
        entity.meters[key] = round(entity.meters.get(key, 0.0) + delta, 3)

    def bump_entity_meme(self, entity_id: str, key: str, delta: float) -> None:
        entity = self.entities[entity_id]
        entity.memes[key] = round(entity.memes.get(key, 0.0) + delta, 3)

    def record(
        self,
        event_id: str,
        text: str,
        subject: str,
        location: str,
        target: str | None = None,
        tags: tuple[str, ...] = (),
    ) -> None:
        self.history.append(
            Event(
                id=event_id,
                text=text,
                subject=subject,
                location=location,
                target=target,
                tags=tags,
            )
        )
        self.fired.append(event_id)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  enclosure: {self.enclosure.key} ({self.enclosure.phrase})")
        rows.append(f"  ghost: {self.ghost_spec.key} ({self.ghost_spec.name})")
        rows.append(f"  gesture: {self.gesture.key} ({self.gesture.phrase})")
        rows.append(f"  meters: {self.meters}")
        rows.append(f"  facts: {self.facts}")
        rows.append(f"  fired: {self.fired}")
        for name, entity in self.entities.items():
            traits = ", ".join(entity.traits) if entity.traits else "none"
            rows.append(
                f"  {name:<12} ({entity.kind:<12}) location={entity.location:<12} "
                f"traits=[{traits}] meters={entity.meters} memes={entity.memes}"
            )
        rows.append("  history:")
        for event in self.history:
            rows.append(
                f"    - {event.id}: {event.text} [subject={event.subject} target={event.target or '-'}]"
            )
        return "\n".join(rows)


ENCLOSURES: dict[str, Enclosure] = {
    "goat_yard": Enclosure(
        key="goat_yard",
        phrase="the clover-sweet goat yard",
        smell="warm clover and old cedar rails",
        closing_task="stack the empty feed bowls",
        moon_image="moonlight striped the rails like pale ribbons",
    ),
    "lamb_pen": Enclosure(
        key="lamb_pen",
        phrase="the straw-soft lamb pen",
        smell="clean straw and sleepy wool",
        closing_task="gather the tiny brushing mitts",
        moon_image="the fence looked powdered with silver flour",
    ),
    "pony_ring": Enclosure(
        key="pony_ring",
        phrase="the round pony ring",
        smell="sweet hay and cool leather",
        closing_task="hang the lead ropes on their pegs",
        moon_image="the painted rails held a rim of milk-white light",
    ),
    "calf_stall": Enclosure(
        key="calf_stall",
        phrase="the quiet calf stall",
        smell="warm grain and sleepy milk pails",
        closing_task="set the little water buckets upside down",
        moon_image="the stall door shone like a pearl in the dusk",
    ),
}

GESTURES: dict[str, Gesture] = {
    "offer_treat": Gesture(
        key="offer_treat",
        phrase="offering a small treat",
        action_template=(
            "{hero} held out {treat} on a flat palm while {friend} stayed close enough to show "
            "that neither child meant to run away."
        ),
        comfort_result=(
            "The friendly offering made the ghost pause instead of pulling back into the mist."
        ),
        courage_delta=0.2,
        friendship_delta=0.35,
        glow_delta=0.05,
    ),
    "hum_softly": Gesture(
        key="hum_softly",
        phrase="humming softly",
        action_template=(
            "{hero} began a small bedtime hum, and {friend} matched the tune until the dark "
            "pen sounded more like a nursery than a warning."
        ),
        comfort_result="The soft song gave the ghost something gentle to step toward.",
        courage_delta=0.15,
        friendship_delta=0.3,
        glow_delta=0.08,
    ),
    "hold_lantern": Gesture(
        key="hold_lantern",
        phrase="holding the lantern steady",
        action_template=(
            "{hero} kept the lantern low and still while {friend} rested one hand on the gate, "
            "making a bright path instead of a bright scare."
        ),
        comfort_result="The steady lantern turned the shadows into places the ghost could trust.",
        courage_delta=0.18,
        friendship_delta=0.25,
        glow_delta=0.22,
    ),
    "walk_together": Gesture(
        key="walk_together",
        phrase="walking together beside the fence",
        action_template=(
            "{hero} and {friend} walked one slow circle beside the fence, showing the ghost that "
            "friendship could keep pace with frightened feet."
        ),
        comfort_result="The shared walk made the lonely pen feel like company instead of emptiness.",
        courage_delta=0.24,
        friendship_delta=0.4,
        glow_delta=0.1,
    ),
}

GHOSTS: dict[str, GhostAnimal] = {
    "pepper": GhostAnimal(
        key="pepper",
        name="Pepper",
        kind="ghost goat",
        enclosure="goat_yard",
        shackle_phrase="a brass shackle hanging from an old bell strap around one misty ankle",
        charm_phrase="the little brass bell that belonged on the strap",
        clue_place="the clover trough",
        entry_image="a small goat shape gathered itself out of the dusk beside the feed rail",
        memory_sentence="Pepper had once waited after closing for one more friend to scratch his ears.",
        final_image="a single clover leaf stayed shining on the rail after Pepper faded away.",
        favorite_treat="three clover tips",
        allowed_gestures=frozenset({"offer_treat", "hold_lantern", "walk_together"}),
    ),
    "morrow": GhostAnimal(
        key="morrow",
        name="Morrow",
        kind="ghost lamb",
        enclosure="lamb_pen",
        shackle_phrase="a silver shackle tied to a ribbon-thin anklet that clicked when the lamb shivered",
        charm_phrase="a blue nursery ribbon that had slipped from the anklet",
        clue_place="the brushing basket",
        entry_image="a woolly lamb outline floated above the straw, pale as breath on a window",
        memory_sentence="Morrow remembered the comfort of being sung to when the zoo went dark.",
        final_image="the blue ribbon fluttered once on the fence and then lay still in the straw glow.",
        favorite_treat="a curled oat biscuit",
        allowed_gestures=frozenset({"offer_treat", "hum_softly", "hold_lantern"}),
    ),
    "comet": GhostAnimal(
        key="comet",
        name="Comet",
        kind="ghost pony",
        enclosure="pony_ring",
        shackle_phrase="a moon-cold shackle linked to a training strap that never stopped trembling",
        charm_phrase="a tin star tag from the old strap",
        clue_place="the saddle peg",
        entry_image="a pony shape paced through the ring in a wash of silver mist",
        memory_sentence="Comet had been happiest when someone walked one calm circle beside him.",
        final_image="a bright hoofprint of dew remained in the dust at the center of the ring.",
        favorite_treat="a sliced apple round",
        allowed_gestures=frozenset({"hum_softly", "hold_lantern", "walk_together"}),
    ),
    "pebble": GhostAnimal(
        key="pebble",
        name="Pebble",
        kind="ghost calf",
        enclosure="calf_stall",
        shackle_phrase="a barn shackle hooked to a milk-pail chain that clinked against the boards",
        charm_phrase="a red feed charm that once hung from the chain",
        clue_place="the upside-down water bucket",
        entry_image="a round-eyed calf shape stood in the stall mist with its nose lowered",
        memory_sentence="Pebble missed the sound of two children talking kindly while chores were finished.",
        final_image="one red spark lingered on the bucket rim before the whole stall turned warm and ordinary.",
        favorite_treat="a carrot coin",
        allowed_gestures=frozenset({"offer_treat", "hold_lantern", "walk_together"}),
    ),
}

HERO_NAMES = ("Mina", "Nora", "Eli", "Theo", "June", "Owen")
FRIEND_NAMES = ("Tess", "Arlo", "Pia", "Ben", "Luca", "Sana")
CARETAKERS = ("Ms. Imani", "Mr. Joel", "Rosa", "Uncle Dev")


def _distinct_names(hero_choice: str | None, friend_choice: str | None, rng: random.Random) -> tuple[str, str]:
    hero = hero_choice or rng.choice(HERO_NAMES)
    pool = [name for name in FRIEND_NAMES if name != hero]
    friend = friend_choice or rng.choice(pool)
    if hero == friend:
        raise StoryError("No story: hero and friend must have different names.")
    return hero, friend


def valid_combo(enclosure_key: str, ghost_key: str, gesture_key: str) -> bool:
    if enclosure_key not in ENCLOSURES or ghost_key not in GHOSTS or gesture_key not in GESTURES:
        return False
    ghost = GHOSTS[ghost_key]
    return ghost.enclosure == enclosure_key and gesture_key in ghost.allowed_gestures


def invalid_reason(enclosure_key: str, ghost_key: str, gesture_key: str) -> str:
    if enclosure_key not in ENCLOSURES:
        return f"No story: unknown enclosure {enclosure_key!r}."
    if ghost_key not in GHOSTS:
        return f"No story: unknown ghost {ghost_key!r}."
    if gesture_key not in GESTURES:
        return f"No story: unknown friendship gesture {gesture_key!r}."
    ghost = GHOSTS[ghost_key]
    if ghost.enclosure != enclosure_key:
        return (
            f"No story: {ghost.name} belongs in {ENCLOSURES[ghost.enclosure].phrase}, "
            f"not {ENCLOSURES[enclosure_key].phrase}."
        )
    if gesture_key not in ghost.allowed_gestures:
        allowed = ", ".join(sorted(ghost.allowed_gestures))
        return (
            f"No story: {GESTURES[gesture_key].phrase} does not fit {ghost.name}'s haunting. "
            f"Allowed gestures: {allowed}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for enclosure_key in sorted(ENCLOSURES):
        for ghost_key, ghost in sorted(GHOSTS.items()):
            if ghost.enclosure != enclosure_key:
                continue
            for gesture_key in sorted(ghost.allowed_gestures):
                combos.append((enclosure_key, ghost_key, gesture_key))
    return combos


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str],
    index: int = 0,
) -> StoryParams:
    seed = (args.seed or 1) + index
    rng = random.Random(seed)
    hero, friend = _distinct_names(args.hero, args.friend, rng)
    caretaker = args.caretaker or rng.choice(CARETAKERS)
    return StoryParams(
        enclosure=combo[0],
        ghost=combo[1],
        gesture=combo[2],
        hero=hero,
        friend=friend,
        caretaker=caretaker,
        seed=seed,
    )


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.enclosure, params.ghost, params.gesture):
        raise StoryError(invalid_reason(params.enclosure, params.ghost, params.gesture))
    if params.hero == params.friend:
        raise StoryError("No story: hero and friend must have different names.")

    enclosure = ENCLOSURES[params.enclosure]
    ghost_spec = GHOSTS[params.ghost]
    gesture = GESTURES[params.gesture]

    world = World(params=params, enclosure=enclosure, ghost_spec=ghost_spec, gesture=gesture)
    world.add(
        Entity(
            id="hero",
            kind="child",
            location=enclosure.key,
            traits=["gentle", "curious"],
            meters={"lantern_glow": 0.35, "steady_steps": 0.4},
            memes={"fear": 0.2, "friendship": 0.4, "courage": 0.45},
        )
    )
    world.add(
        Entity(
            id="friend",
            kind="child",
            location=enclosure.key,
            traits=["loyal", "watchful"],
            meters={"lantern_glow": 0.25, "steady_steps": 0.45},
            memes={"fear": 0.25, "friendship": 0.55, "courage": 0.4},
        )
    )
    world.add(
        Entity(
            id="ghost",
            kind=ghost_spec.kind,
            location=enclosure.key,
            traits=["lonely", "soft-hoofed"],
            meters={"mist": 1.0, "shackle_weight": 1.0},
            memes={"fear": 0.65, "trust": 0.05, "peace": 0.0, "friendship": 0.0},
        )
    )
    world.add(
        Entity(
            id="shackle",
            kind="physical",
            location=enclosure.key,
            traits=["cold", "ringing"],
            meters={"tension": 1.0, "sound": 0.9},
            memes={"memory": 1.0},
        )
    )
    world.add(
        Entity(
            id="charm",
            kind="physical",
            location=enclosure.key,
            traits=["missing", "keepsake"],
            meters={"found": 0.0, "warmth": 0.0},
            memes={"belonging": 0.8},
        )
    )
    world.facts.update(
        {
            "source_tale": INTERNAL_SOURCE_TALE,
            "setting": "petting zoo",
            "enclosure_phrase": enclosure.phrase,
            "ghost_name": ghost_spec.name,
            "ghost_kind": ghost_spec.kind,
            "gesture_phrase": gesture.phrase,
            "shackle_phrase": ghost_spec.shackle_phrase,
            "charm_phrase": ghost_spec.charm_phrase,
            "clue_place": ghost_spec.clue_place,
            "caretaker": params.caretaker,
            "seed": str(params.seed),
        }
    )
    simulate(world)
    return world


def simulate(world: World) -> None:
    hero_name = world.params.hero
    friend_name = world.params.friend
    enclosure = world.enclosure
    ghost = world.ghost_spec
    gesture = world.gesture

    opening = (
        f"At closing time, {hero_name} and {friend_name} stayed behind in the petting zoo to "
        f"{enclosure.closing_task} for {world.params.caretaker}. The air smelled like {enclosure.smell}, "
        f"and {enclosure.moon_image}."
    )
    world.record("arrival", opening, subject="hero", location=enclosure.key, target="friend", tags=("premise",))

    omen = (
        f"Then something tapped inside {enclosure.phrase}: not a hoof, not a bucket, but the quick metal "
        f"click of {ghost.shackle_phrase}. When {hero_name} lifted the lantern, {ghost.entry_image}."
    )
    world.record(
        "omen",
        omen,
        subject="shackle",
        location=enclosure.key,
        target="ghost",
        tags=("tension", "ghost"),
    )
    world.bump_world("mist", 0.15)
    world.bump_world("zoo_hush", 0.2)
    world.bump_entity_meme("hero", "fear", 0.2)
    world.bump_entity_meme("friend", "fear", 0.22)
    world.bump_entity_meter("shackle", "sound", 0.05)

    clue = (
        f"Instead of running, {hero_name} saw {ghost.charm_phrase} resting by {ghost.clue_place}. "
        f"{friend_name} whispered that the ghost did not look mean, only lonely."
    )
    world.record("clue", clue, subject="hero", location=enclosure.key, target="charm", tags=("clue",))
    world.entities["charm"].meters["found"] = 1.0
    world.entities["charm"].location = ghost.clue_place
    world.bump_entity_meme("hero", "courage", 0.12)
    world.bump_entity_meme("friend", "courage", 0.1)

    comfort = gesture.action_template.format(
        hero=hero_name,
        friend=friend_name,
        treat=ghost.favorite_treat,
    )
    comfort += f" {gesture.comfort_result} {ghost.memory_sentence}"
    world.record(
        "friendship_turn",
        comfort,
        subject="hero",
        location=enclosure.key,
        target="ghost",
        tags=("turn", "friendship"),
    )
    world.bump_world("lantern_glow", gesture.glow_delta)
    world.bump_entity_meme("hero", "friendship", gesture.friendship_delta)
    world.bump_entity_meme("friend", "friendship", gesture.friendship_delta / 2)
    world.bump_entity_meme("hero", "courage", gesture.courage_delta)
    world.bump_entity_meme("ghost", "trust", 0.55)
    world.bump_entity_meme("ghost", "friendship", 0.6)
    world.bump_entity_meme("ghost", "fear", -0.25)
    world.bump_entity_meter("ghost", "mist", -0.2)
    world.entities["charm"].meters["warmth"] = 0.7

    release = (
        f"{hero_name} clipped {ghost.charm_phrase} back where it belonged, and {friend_name} kept one hand on "
        f"{hero_name}'s sleeve while the old shackle gave one last tiny ring. The metal slackened, the mist "
        f"around {ghost.name} softened, and the ghost animal stepped close enough to seem grateful instead of trapped."
    )
    world.record(
        "release",
        release,
        subject="hero",
        location=enclosure.key,
        target="shackle",
        tags=("resolution", "release"),
    )
    world.bump_world("shackle_tension", -1.0)
    world.bump_entity_meter("shackle", "tension", -1.0)
    world.bump_entity_meter("shackle", "sound", -0.8)
    world.bump_entity_meme("ghost", "peace", 0.95)
    world.bump_entity_meme("ghost", "trust", 0.2)
    world.bump_entity_meme("hero", "fear", -0.15)
    world.bump_entity_meme("friend", "fear", -0.18)

    ending = (
        f"Before the children left, {ghost.name} walked one calm step beside them as if accepting their friendship "
        f"at last. Then the ghost thinned into moonlit air, and {ghost.final_image} By the time {hero_name} and "
        f"{friend_name} latched the gate, the pen felt like part of the petting zoo again, not a place stuck in a sad echo."
    )
    world.record("ending", ending, subject="ghost", location=enclosure.key, target="friend", tags=("ending",))

    world.facts["released"] = "yes"
    world.facts["final_image"] = ghost.final_image
    world.facts["friendship_result"] = "The children stayed, shared kindness, and the ghost accepted company."


def _fear_phrase(level: float) -> str:
    if level >= 0.5:
        return "their fear pinched for a moment"
    if level >= 0.25:
        return "they felt nervous but steady"
    return "the fear had mostly melted away"


def _story_text(world: World) -> str:
    hero = world.params.hero
    friend = world.params.friend
    ghost = world.ghost_spec
    friend_state = world.entities["friend"]
    glow = world.meters["lantern_glow"]
    trust = world.entities["ghost"].memes["trust"]

    p1 = world.history[0].text
    p2 = (
        f"{world.history[1].text} {hero} squeezed the lantern handle, and {friend} moved closer because "
        f"{_fear_phrase(friend_state.memes['fear'])}."
    )
    p3 = (
        f"{world.history[2].text} {world.history[3].text} By then the lantern glow felt "
        f"{'warm enough to share' if glow >= 0.5 else 'small but brave'}, and the ghost's eyes no longer looked wild."
    )
    p4 = (
        f"{world.history[4].text} The change happened because friendship reached {ghost.name} before the fear did."
    )
    p5 = (
        f"{world.history[5].text} Both children would remember that some ghost stories end "
        f"with a friend being found, not a monster being chased away."
        if trust >= 0.75
        else world.history[5].text
    )
    return "\n\n".join([p1, p2, p3, p4, p5])


def _prompts(world: World) -> list[str]:
    return [
        "Write a gentle ghost story set in a petting zoo.",
        f"Include the word shackle and make {world.ghost_spec.name}, the {world.ghost_spec.kind}, central to the mystery.",
        f"Let friendship solve the haunting by {world.gesture.phrase}, then end with a concrete final image.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    friend = world.params.friend
    ghost = world.ghost_spec
    return [
        QAItem(
            "Who stayed in the petting zoo after closing time?",
            f"{hero} and {friend} stayed behind to help with evening chores. Their being there matters because the ghost needed children who would notice a lonely sound instead of a dangerous one.",
        ),
        QAItem(
            "What made the children realize the haunting was near?",
            f"They heard the quick metal click of {ghost.shackle_phrase} inside {world.enclosure.phrase}. That sound led them to the ghost before they understood why it was trapped in sadness.",
        ),
        QAItem(
            f"What missing object did {hero} find?",
            f"{hero} found {ghost.charm_phrase} near {ghost.clue_place}. Returning it mattered because the shackle was tied to the ghost's memory of belonging there.",
        ),
        QAItem(
            "How did friendship change the middle of the story?",
            f"The children answered the haunting by {world.gesture.phrase} instead of panicking. That choice made the ghost trust them enough to accept the keepsake and let the shackle go quiet.",
        ),
        QAItem(
            "What proves the story ended differently from how it began?",
            f"The pen stopped feeling trapped and scary once the ghost found peace. The ending proves it with this image: {ghost.final_image}",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    ghost = world.ghost_spec
    return [
        QAItem(
            "Why does a keepsake matter in this world?",
            "A keepsake anchors the ghost to a memory of being cared for in the petting zoo. When the right object is returned, the haunting can move from lonely repetition to peace.",
        ),
        QAItem(
            "Why are friendship gestures part of the logic instead of decoration?",
            "The haunting is emotional as well as physical, so a correct gesture changes trust and courage in the pen. The story does not end just because the charm is present; it ends because kindness makes the ghost willing to accept it.",
        ),
        QAItem(
            "What does the shackle represent here?",
            f"The shackle is the physical sign of the ghost being stuck in one sad memory. Once {ghost.name} feels accompanied and the keepsake is restored, that metal no longer has a reason to keep ringing.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=_story_text(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
ghost_home(G,E) :- ghost(G), enclosure(E), home(G,E).
valid(E,G,A) :-
    enclosure(E),
    ghost(G),
    gesture(A),
    home(G,E),
    allows(G,A).

ok :- chosen(E,G,A), valid(E,G,A).

#show valid/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for enclosure_key in ENCLOSURES:
        rows.append(fact("enclosure", enclosure_key))
    for ghost_key, ghost in GHOSTS.items():
        rows.append(fact("ghost", ghost_key))
        rows.append(fact("home", ghost_key, ghost.enclosure))
        rows.append(fact("charm", ghost_key, ghost.charm_phrase))
        for gesture_key in ghost.allowed_gestures:
            rows.append(fact("allows", ghost_key, gesture_key))
    for gesture_key in GESTURES:
        rows.append(fact("gesture", gesture_key))
    if params is not None:
        rows.append(fact("chosen", params.enclosure, params.ghost, params.gesture))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        for combo in atoms(model, "valid"):
            combos.add(tuple(combo))
    return combos


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def _validate_sample_shape(sample: StorySample) -> None:
    story = sample.story
    if "petting zoo" not in story:
        raise StoryError("Verification failed: story omitted the petting zoo setting.")
    if "shackle" not in story:
        raise StoryError("Verification failed: story omitted the required word 'shackle'.")
    if story.count("\n\n") < 4:
        raise StoryError("Verification failed: story is missing a full beginning, turn, or ending.")
    if any(token in story for token in ("{", "}", "None", "  ")):
        raise StoryError("Verification failed: story contains unresolved or low-quality text.")
    if not sample.story_qa or not sample.world_qa or not sample.prompts:
        raise StoryError("Verification failed: missing prompt or QA sections.")


def verify() -> str:
    python_combos = set(valid_combos())
    asp_combos = asp_valid_combos()
    if python_combos != asp_combos:
        only_python = sorted(python_combos - asp_combos)
        only_asp = sorted(asp_combos - python_combos)
        raise StoryError(
            f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}"
        )
    for index, combo in enumerate(sorted(python_combos), 1):
        params = _params_from_combo(
            argparse.Namespace(
                seed=1000,
                hero=None,
                friend=None,
                caretaker=None,
            ),
            combo,
            index=index,
        )
        sample = generate(params)
        _validate_sample_shape(sample)
        if not asp_verify(params):
            raise StoryError(f"Verification failed: chosen combo {combo} was not accepted by ASP.")
    return f"OK: Python and ASP agree for {len(python_combos)} combos, and every generated sample passed shape checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a petting-zoo friendship ghost story about a lonely shackle."
    )
    parser.add_argument("--enclosure", choices=tuple(ENCLOSURES))
    parser.add_argument("--ghost", choices=tuple(GHOSTS))
    parser.add_argument("--gesture", choices=tuple(GESTURES))
    parser.add_argument("--hero", default=None)
    parser.add_argument("--friend", default=None)
    parser.add_argument("--caretaker", default=None)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random | None = None,
    index: int = 0,
) -> StoryParams:
    chooser = rng or random.Random((args.seed or 1) + index)
    combos = valid_combos()
    if args.enclosure or args.ghost or args.gesture:
        filtered = [
            combo
            for combo in combos
            if (args.enclosure is None or combo[0] == args.enclosure)
            and (args.ghost is None or combo[1] == args.ghost)
            and (args.gesture is None or combo[2] == args.gesture)
        ]
        if not filtered:
            raise StoryError(
                invalid_reason(
                    args.enclosure or "<enclosure>",
                    args.ghost or "<ghost>",
                    args.gesture or "<gesture>",
                )
            )
        combo = chooser.choice(filtered)
    else:
        combo = chooser.choice(combos)
    return _params_from_combo(args, combo, index=index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for index, prompt in enumerate(sample.prompts, 1):
        print(f"{index}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if header:
        print(header)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for enclosure_key, ghost_key, gesture_key in sorted(asp_valid_combos()):
        print(f"{enclosure_key}\t{ghost_key}\t{gesture_key}")


def _json_dump(samples: list[StorySample]) -> None:
    if len(samples) == 1:
        print(samples[0].to_json())
        return
    print(
        json.dumps(
            [sample.to_dict() for sample in samples],
            indent=2,
            ensure_ascii=False,
        )
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            samples = [generate(_params_from_combo(args, combo, index=i)) for i, combo in enumerate(combos, 1)]
            if args.json:
                _json_dump(samples)
                return 0
            for i, sample in enumerate(samples, 1):
                combo = combos[i - 1]
                emit(sample, args, f"### {combo[0]} / {combo[1]} / {combo[2]}")
                if i != len(samples):
                    print("\n" + "=" * 72 + "\n")
            return 0
        count = max(1, args.n)
        samples = [generate(resolve_params(args, index=i)) for i in range(count)]
        if args.json:
            _json_dump(samples)
            return 0
        for i, sample in enumerate(samples, 1):
            header = f"### variant {i}" if count > 1 else None
            emit(sample, args, header)
            if i != count:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
