#!/usr/bin/env python3
"""A state-driven ghost story about a shackle, friendship, and a petting zoo at night."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "After closing time at a petting zoo, a careful child hears a shackle striking a pen gate. "
    "A lonely ghost is not trying to scare anyone away; the ghost is trying to protect one animal "
    "and keep an old promise about the night latch. The child studies the physical problem, answers "
    "it with a fitting act of care, and lets friendship settle into the shackle itself."
)


@dataclass(frozen=True)
class Pen:
    id: str
    name: str
    animal_name: str
    animal_kind: str
    eerie_detail: str
    risk_text: str
    discovery_text: str
    closing_image: str
    needed_tags: tuple[str, ...]


@dataclass(frozen=True)
class Ghost:
    id: str
    name: str
    role: str
    home_pen: str
    worry: str
    whisper: str
    request: str
    ending_line: str
    accepted_gestures: tuple[str, ...]
    needed_tags: tuple[str, ...]


@dataclass(frozen=True)
class Shackle:
    id: str
    label: str
    sound: str
    feel: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Gesture:
    id: str
    action: str
    effect_text: str
    promise_text: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class StoryParams:
    pen: str
    ghost: str
    shackle: str
    gesture: str
    child_name: str
    child_trait: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    location: str
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, int] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None
    meter_delta: dict[str, int] = field(default_factory=dict)
    meme_delta: dict[str, int] = field(default_factory=dict)


@dataclass
class PettingZooWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: str | None = None,
        meter_delta: dict[str, int] | None = None,
        meme_delta: dict[str, int] | None = None,
    ) -> None:
        meter_delta = dict(meter_delta or {})
        meme_delta = dict(meme_delta or {})
        self.history.append(Event(event_id, text, actor, target, meter_delta, meme_delta))
        for key, value in meter_delta.items():
            entity_id, metric = key.split(":", 1)
            entity = self.entities[entity_id]
            entity.meters[metric] = entity.meters.get(metric, 0) + value
        for key, value in meme_delta.items():
            entity_id, metric = key.split(":", 1)
            entity = self.entities[entity_id]
            entity.memes[metric] = entity.memes.get(metric, 0) + value


PENS = {
    "lamb_corner": Pen(
        id="lamb_corner",
        name="the lamb corner by the white fence",
        animal_name="Wisp",
        animal_kind="lamb",
        eerie_detail="The moon put a pale stripe over the hay, and every hanging brush made a shadow that looked one step longer than it should have been.",
        risk_text="Wisp kept shrinking from the gate as though one more hard knock would make the whole pen feel unkind.",
        discovery_text="the cold metal was startling the little lamb more than the dark itself",
        closing_image="Wisp folded into the straw right beside the latch and breathed as softly as milk cooling in a pail.",
        needed_tags=("warm", "care"),
    ),
    "goat_walk": Pen(
        id="goat_walk",
        name="the goat walk beside the red barn",
        animal_name="Thimble",
        animal_kind="goat",
        eerie_detail="Old feed pans swung on their nails, and the fence cast ribs of shadow across the path.",
        risk_text="Thimble kept butting the boards and stepping back again, as if the loose gate sounded too weak to trust through the night.",
        discovery_text="the latch needed a steadier hold and a kinder sound before the goat would settle",
        closing_image="Thimble leaned one small horn against the rail and let the night pass without another jump.",
        needed_tags=("sturdy", "quiet"),
    ),
    "donkey_stall": Pen(
        id="donkey_stall",
        name="the little donkey stall near the lantern shed",
        animal_name="Bramble",
        animal_kind="donkey",
        eerie_detail="The shed lantern was out, so the stall door floated in the dark like a closed eyelid.",
        risk_text="Bramble kept turning the wrong way in the straw, too bothered by the restless gate to find the calm side of the stall.",
        discovery_text="the night pen needed a clear, guiding feel so the donkey could choose the safe side again",
        closing_image="Bramble faced the stall door, ears low and peaceful, as though the dark had finally learned its manners.",
        needed_tags=("guide", "sturdy"),
    ),
}

GHOSTS = {
    "elsie": Ghost(
        id="elsie",
        name="Elsie",
        role="a lamb tender from long ago",
        home_pen="lamb_corner",
        worry="she once promised that no frightened lamb would be left with a sharp night sound",
        whisper='"Please make the night softer for Wisp," the ghost whispered.',
        request="show the latch one gentle act of care",
        ending_line='"Now the pen sounds loved again," Elsie said, and her smile no longer looked lonely.',
        accepted_gestures=("wrap", "oil"),
        needed_tags=("warm", "care"),
    ),
    "rowan": Ghost(
        id="rowan",
        name="Rowan",
        role="an old goat keeper with silver dust in his sleeves",
        home_pen="goat_walk",
        worry="he cannot rest while a brave-sounding gate is actually wobbling loose",
        whisper='"Listen closely," the ghost whispered. "The rattle is the gate asking for help."',
        request="answer the gate before it frightens Thimble again",
        ending_line='"You heard the hurt part of the noise," Rowan said, sounding more proud than sad.',
        accepted_gestures=("oil", "bell"),
        needed_tags=("quiet", "care"),
    ),
    "milo": Ghost(
        id="milo",
        name="Milo",
        role="a donkey groom who still walks the closing round in mist",
        home_pen="donkey_stall",
        worry="he wants the last sound at the stall to guide Bramble home instead of turning the dark into a maze",
        whisper='"If the latch can guide Bramble, I can stop walking in circles too," the ghost whispered.',
        request="help the stall feel like home again",
        ending_line='"That is the sound of finding home," Milo said, and the cold around him thinned into silver dust.',
        accepted_gestures=("bell", "oil"),
        needed_tags=("guide", "care"),
    ),
}

SHACKLES = {
    "fleece_bound": Shackle(
        id="fleece_bound",
        label="the fleece-bound shackle",
        sound="a muffled tap that still carried a lonely shiver",
        feel="soft cloth wrapped over cold iron, with one rough edge still peeking through",
        tags=("warm", "care"),
    ),
    "barn_brass": Shackle(
        id="barn_brass",
        label="the barn-brass shackle",
        sound="a flat clack that bounced off the boards like a spoon on a bucket",
        feel="smooth in the middle but loose at the hinge, as if too many tired hands had rushed past it",
        tags=("sturdy", "quiet"),
    ),
    "lantern_loop": Shackle(
        id="lantern_loop",
        label="the lantern-loop shackle",
        sound="a thin ring that seemed to point somewhere deeper into the pen",
        feel="firm metal with a worn groove where generations of fingers had found the latch in the dark",
        tags=("guide", "sturdy"),
    ),
}

GESTURES = {
    "wrap": Gesture(
        id="wrap",
        action="wrap the shackle in a clean strip of fleece from the brush hook",
        effect_text="The cloth took the bite out of {shackle}, and even the next test of the gate came out like a sleepy breath.",
        promise_text="Treat the frightening sound as something that can be comforted.",
        tags=("warm", "care"),
    ),
    "oil": Gesture(
        id="oil",
        action="rub a little lamp oil and patient straw over the stiff link",
        effect_text="The stubborn metal loosened, and {shackle} settled deeper into its place instead of scraping for attention.",
        promise_text="Stay and fix the trouble instead of running from it.",
        tags=("quiet", "care"),
    ),
    "bell": Gesture(
        id="bell",
        action="tie on the little bedtime bell that the keepers use for the gentlest animals",
        effect_text="The bell gave one round note, and {animal} turned toward the safe side of the pen as if the sound had shown the way home.",
        promise_text="Answer fear with a guide, not with more noise.",
        tags=("guide", "care"),
    ),
}

CHILD_NAMES = ("Nora", "Lila", "Tess", "Mina", "Poppy", "June")
CHILD_TRAITS = ("careful", "steady", "observant", "gentle", "patient", "brave")


def combined_tags(shackle_id: str, gesture_id: str) -> set[str]:
    return set(SHACKLES[shackle_id].tags) | set(GESTURES[gesture_id].tags)


def validate_combo(pen_id: str, ghost_id: str, shackle_id: str, gesture_id: str) -> tuple[bool, str]:
    if pen_id not in PENS:
        return False, f"unknown pen: {pen_id}"
    if ghost_id not in GHOSTS:
        return False, f"unknown ghost: {ghost_id}"
    if shackle_id not in SHACKLES:
        return False, f"unknown shackle: {shackle_id}"
    if gesture_id not in GESTURES:
        return False, f"unknown gesture: {gesture_id}"

    pen = PENS[pen_id]
    ghost = GHOSTS[ghost_id]
    tags = combined_tags(shackle_id, gesture_id)

    if ghost.home_pen != pen_id:
        return False, f"{ghost.name} belongs to {PENS[ghost.home_pen].name}, not {pen.name}"
    if gesture_id not in ghost.accepted_gestures:
        return False, f"{ghost.name} would not trust the {gesture_id} gesture in this haunting"
    for tag in pen.needed_tags:
        if tag not in tags:
            return False, f"{pen.name} needs a {tag} answer before the gate can feel safe"
    for tag in ghost.needed_tags:
        if tag not in tags:
            return False, f"{ghost.name} needs a {tag} answer before friendship can happen"
    return True, ""


def all_valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for pen_id in sorted(PENS):
        for ghost_id in sorted(GHOSTS):
            for shackle_id in sorted(SHACKLES):
                for gesture_id in sorted(GESTURES):
                    ok, _ = validate_combo(pen_id, ghost_id, shackle_id, gesture_id)
                    if ok:
                        combos.append((pen_id, ghost_id, shackle_id, gesture_id))
    return combos


def pick_story_params(
    combo: tuple[str, str, str, str],
    rng: random.Random,
    seed: int | None,
) -> StoryParams:
    child_name = rng.choice(CHILD_NAMES)
    child_trait = rng.choice(CHILD_TRAITS)
    return StoryParams(
        pen=combo[0],
        ghost=combo[1],
        shackle=combo[2],
        gesture=combo[3],
        child_name=child_name,
        child_trait=child_trait,
        seed=seed,
    )


def filtered_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    if args.pen and args.ghost and args.shackle and args.gesture:
        ok, reason = validate_combo(args.pen, args.ghost, args.shackle, args.gesture)
        if not ok:
            raise StoryError(reason)
    combos = [
        combo
        for combo in all_valid_combos()
        if (args.pen is None or combo[0] == args.pen)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.shackle is None or combo[2] == args.shackle)
        and (args.gesture is None or combo[3] == args.gesture)
    ]
    if not combos:
        raise StoryError("No valid petting-zoo ghost story matches the requested options.")
    return combos


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Story world: shackle, petting zoo, friendship, ghost story."
    )
    parser.add_argument("--pen", choices=sorted(PENS))
    parser.add_argument("--ghost", choices=sorted(GHOSTS))
    parser.add_argument("--shackle", choices=sorted(SHACKLES))
    parser.add_argument("--gesture", choices=sorted(GESTURES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = filtered_combos(args)
    return pick_story_params(rng.choice(combos), rng, args.seed)


def make_world(params: StoryParams) -> PettingZooWorld:
    pen = PENS[params.pen]
    ghost = GHOSTS[params.ghost]
    shackle = SHACKLES[params.shackle]
    world = PettingZooWorld(params=params)
    world.add(
        Entity(
            id="child",
            name=params.child_name,
            kind="child",
            location="path",
            meters={"steps": 1},
            memes={"care": 1, "courage": 1, "fear": 0, "friendship": 0},
        )
    )
    world.add(
        Entity(
            id="animal",
            name=pen.animal_name,
            kind=pen.animal_kind,
            location=pen.id,
            meters={"calm": 0, "alarm": 0, "homeward": 0},
            memes={"trust": 0},
        )
    )
    world.add(
        Entity(
            id="gate",
            name=f"the gate at {pen.name}",
            kind="gate",
            location=pen.id,
            meters={"secure": 0, "quiet": 0, "danger": 0},
            memes={"memory": 1},
        )
    )
    world.add(
        Entity(
            id="shackle",
            name=shackle.label,
            kind="shackle",
            location=pen.id,
            meters={"rattle": 0, "rest": 0},
            memes={"friendship": 0},
        )
    )
    world.add(
        Entity(
            id="ghost",
            name=ghost.name,
            kind="ghost",
            location=pen.id,
            meters={"visible": 0},
            memes={"trust": 0, "loneliness": 2, "friendship": 0},
        )
    )
    world.add(
        Entity(
            id="pen",
            name=pen.name,
            kind="place",
            location="petting_zoo",
            meters={"night": 1},
            memes={"memory": 1},
        )
    )
    world.facts.update(
        {
            "source_tale": SOURCE_TALE,
            "setting": "petting zoo",
            "carrier": shackle.label,
            "ghost_worry": ghost.worry,
            "animal_need": pen.discovery_text,
            "combined_tags": sorted(combined_tags(params.shackle, params.gesture)),
            "ending": "haunting",
        }
    )
    return world


def closing_round(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    child = world.params.child_name
    trait = world.params.child_trait
    world.record(
        "closing_round",
        f"The petting zoo had already closed when {child}, the {trait} helper on the last lantern walk, slowed beside {pen.name}. {pen.eerie_detail}",
        "child",
        "pen",
        meter_delta={"child:steps": 1, "pen:night": 1},
        meme_delta={"child:care": 1},
    )


def hear_the_shackle(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    shackle = SHACKLES[world.params.shackle]
    world.record(
        "rattle",
        f"Then {shackle.label} struck the gate with {shackle.sound}, and {pen.animal_name} flinched in the straw. {pen.risk_text}",
        "shackle",
        "animal",
        meter_delta={"shackle:rattle": 1, "gate:danger": 1, "animal:alarm": 1},
        meme_delta={"child:fear": 1},
    )


def reveal_ghost(world: PettingZooWorld) -> None:
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]
    child = world.params.child_name
    world.record(
        "apparition",
        f"Cold mist gathered around {shackle.label} until {ghost.name}, {ghost.role}, stepped out of it. {ghost.whisper} {ghost.name} pointed at the latch as if begging {child} to {ghost.request}.",
        "ghost",
        "child",
        meter_delta={"ghost:visible": 1},
        meme_delta={"child:fear": 1, "ghost:trust": 0},
    )


def understand_the_need(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]
    child = world.params.child_name
    world.record(
        "turn",
        f"Instead of running, {child} touched {shackle.label} and felt {shackle.feel}. That was when {child} saw that {pen.discovery_text}, and the whole haunting changed shape: {ghost.name} was guarding {pen.animal_name}, not chasing anyone away.",
        "child",
        "ghost",
        meter_delta={"gate:danger": -1},
        meme_delta={"child:courage": 1, "ghost:trust": 1},
    )


def answer_with_care(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    shackle = SHACKLES[world.params.shackle]
    gesture = GESTURES[world.params.gesture]
    child = world.params.child_name
    tags = world.facts["combined_tags"]

    meter_delta = {
        "gate:secure": 1,
        "shackle:rest": 1,
        "animal:calm": 1,
    }
    if "quiet" in tags:
        meter_delta["gate:quiet"] = 1
    if "guide" in tags:
        meter_delta["animal:homeward"] = 1

    world.record(
        "answer",
        f"{child} chose to {gesture.action}. {gesture.effect_text.format(shackle=shackle.label, animal=pen.animal_name)}",
        "child",
        "shackle",
        meter_delta=meter_delta,
        meme_delta={"child:care": 1, "child:courage": 1, "ghost:trust": 1},
    )
    world.facts["promise"] = gesture.promise_text


def become_friends(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]

    gate = world.entities["gate"]
    animal = world.entities["animal"]
    ghost_entity = world.entities["ghost"]
    if gate.meters["secure"] < 1 or animal.meters["calm"] < 1 or ghost_entity.memes["trust"] < 2:
        raise StoryError("story world did not reach a grounded friendship ending")

    if animal.meters["homeward"] > 0:
        animal_line = f"{pen.animal_name} followed the fence line back to the safest patch of straw."
    elif "warm" in world.facts["combined_tags"]:
        animal_line = f"{pen.animal_name} tucked close to the latch instead of shrinking from it."
    else:
        animal_line = f"{pen.animal_name} stayed by the gate without trembling."

    world.record(
        "friendship",
        f"{animal_line} {ghost.name} laid transparent fingers over {shackle.label}, and this time the metal stayed still because it felt safe. {ghost.ending_line}",
        "ghost",
        "shackle",
        meter_delta={"animal:calm": 1, "shackle:rest": 1},
        meme_delta={
            "ghost:friendship": 1,
            "ghost:loneliness": -1,
            "child:friendship": 1,
            "shackle:friendship": 1,
        },
    )
    world.facts["ending"] = "friendship"


def render_story(world: PettingZooWorld) -> str:
    pen = PENS[world.params.pen]
    shackle = SHACKLES[world.params.shackle]
    ghost = GHOSTS[world.params.ghost]
    child = world.params.child_name

    intro = (
        "At closing time, the petting zoo felt like a place where every board and bucket was holding one extra secret for the dark."
    )
    history_text = " ".join(event.text for event in world.history)
    if world.entities["shackle"].memes["friendship"] > 0:
        closing = (
            f"When {child} finally walked back toward the barn, {pen.closing_image} "
            f"{ghost.name} drifted beside the fence instead of hiding in the cold, and {shackle.label} looked less like a chain than a small shining handshake."
        )
    else:
        closing = (
            f"When {child} finally walked back toward the barn, the pen was quieter, but {shackle.label} still sounded lonely in the dark."
        )
    return " ".join([intro, history_text, closing])


def tell(params: StoryParams) -> PettingZooWorld:
    world = make_world(params)
    closing_round(world)
    hear_the_shackle(world)
    reveal_ghost(world)
    understand_the_need(world)
    answer_with_care(world)
    become_friends(world)
    return world


def story_prompts(world: PettingZooWorld) -> list[str]:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    return [
        "Write a child-friendly ghost story set in a petting zoo.",
        f"Include the word shackle and let friendship grow from helping {pen.animal_name} in a physical way.",
        f"Make {ghost.name}'s haunting turn when {world.params.child_name} understands the problem instead of fleeing from it.",
    ]


def story_grounded_qa(world: PettingZooWorld) -> list[QAItem]:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]
    gesture = GESTURES[world.params.gesture]
    child = world.params.child_name
    return [
        QAItem(
            "Why did the ghost appear at the pen?",
            (
                f"{ghost.name} appeared because {ghost.worry}. "
                f"The rattling of {shackle.label} told the ghost that {pen.animal_name} might spend the night feeling unsafe."
            ),
        ),
        QAItem(
            "What was the turning point of the story?",
            (
                f"The story turned when {child} touched the shackle and realized the haunting was a warning, not a threat. "
                f"That understanding led {child} to {gesture.action}, which answered both the ghost's worry and the animal's need."
            ),
        ),
        QAItem(
            "How does the ending prove that friendship happened?",
            (
                f"The ending proves it because {ghost.name} stays beside the fence after the gate is fixed instead of vanishing in fear. "
                f"The quiet shackle becomes the physical sign of trust, and {pen.animal_name} settles down under that new peace."
            ),
        ),
    ]


def world_knowledge_qa(world: PettingZooWorld) -> list[QAItem]:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    return [
        QAItem(
            "Which physical object carried the new friendship in this world?",
            (
                f"The main carrier was {world.entities['shackle'].name}. "
                f"It held the repaired gate and also held the friendship because the ghost stopped using it as a cry for help and began sharing it as a sign of trust."
            ),
        ),
        QAItem(
            "Why is the petting zoo setting important in this story?",
            (
                "The petting zoo matters because the haunting grows out of caring for a real animal space after closing time. "
                f"The fear, the fix, and the friendship all stay grounded in {pen.name}, the gate, and the creature that needs a safe night."
            ),
        ),
        QAItem(
            "Who was the ghost trying to protect?",
            (
                f"The ghost was trying to protect {pen.animal_name}, the {pen.animal_kind} in {pen.name}. "
                f"Everything spooky in the story points back to that simple care, which is why friendship becomes possible."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=render_story(world),
        prompts=story_prompts(world),
        story_qa=story_grounded_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for pen in PENS.values():
        facts.append(asp.fact("pen", pen.id))
        for tag in pen.needed_tags:
            facts.append(asp.fact("pen_need", pen.id, tag))
    for ghost in GHOSTS.values():
        facts.append(asp.fact("ghost", ghost.id))
        facts.append(asp.fact("ghost_pen", ghost.id, ghost.home_pen))
        for gesture in ghost.accepted_gestures:
            facts.append(asp.fact("ghost_accepts", ghost.id, gesture))
        for tag in ghost.needed_tags:
            facts.append(asp.fact("ghost_need", ghost.id, tag))
    for shackle in SHACKLES.values():
        facts.append(asp.fact("shackle", shackle.id))
        for tag in shackle.tags:
            facts.append(asp.fact("shackle_tag", shackle.id, tag))
    for gesture in GESTURES.values():
        facts.append(asp.fact("gesture", gesture.id))
        for tag in gesture.tags:
            facts.append(asp.fact("gesture_tag", gesture.id, tag))
    return "\n".join(facts)


ASP_RULES = r"""
combined_tag(S, A, T) :- shackle_tag(S, T), gesture(A).
combined_tag(S, A, T) :- gesture_tag(A, T), shackle(S).

invalid(P, G, S, A) :-
    pen(P), ghost(G), shackle(S), gesture(A),
    ghost_pen(G, GP),
    GP != P.

invalid(P, G, S, A) :-
    pen(P), ghost(G), shackle(S), gesture(A),
    not ghost_accepts(G, A).

invalid(P, G, S, A) :-
    pen(P), ghost(G), shackle(S), gesture(A),
    pen_need(P, T),
    not combined_tag(S, A, T).

invalid(P, G, S, A) :-
    pen(P), ghost(G), shackle(S), gesture(A),
    ghost_need(G, T),
    not combined_tag(S, A, T).

valid(P, G, S, A) :-
    pen(P), ghost(G), shackle(S), gesture(A),
    not invalid(P, G, S, A).
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/4.\n"


def verify() -> str:
    import asp

    py_valid = set(all_valid_combos())
    model = asp.one_model(asp_program())
    asp_valid = {
        tuple(str(piece) for piece in atom)
        for atom in asp.atoms(model, "valid")
    }
    if py_valid != asp_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")

    exercised = 0
    for index, combo in enumerate(sorted(py_valid)):
        params = pick_story_params(combo, random.Random(1000 + index), 1000 + index)
        sample = generate(params)
        exercised += 1
        story_text = sample.story.lower()
        if "shackle" not in story_text:
            raise StoryError("generated story failed to include the seed word 'shackle'")
        if "petting zoo" not in story_text:
            raise StoryError("generated story failed to keep the requested setting visible")
        if len(sample.prompts) != 3 or len(sample.story_qa) != 3 or len(sample.world_qa) != 3:
            raise StoryError("generated story did not emit the required prompt and QA sets")
        if sample.world.facts.get("ending") != "friendship":
            raise StoryError("generated story did not reach the intended friendship ending")
        if sample.world.entities["shackle"].memes.get("friendship", 0) < 1:
            raise StoryError("friendship was not embedded in the physical carrier")
        if any(qa.answer.count(".") < 2 for qa in sample.story_qa):
            raise StoryError("story-grounded QA answers must use at least two sentences")
    return f"OK: Python and ASP agree on {len(py_valid)} valid petting-zoo ghost stories; exercised {exercised} renders."


def dump_trace(world: PettingZooWorld) -> str:
    lines = ["Trace:"]
    for event in world.history:
        lines.append(f"- {event.id}: {event.text}")
    lines.append("")
    lines.append("State:")
    for entity in world.entities.values():
        lines.append(
            f"- {entity.id}: kind={entity.kind} location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["Prompts:"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("Story QA:")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("World QA:")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    combos = filtered_combos(args)
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        for index, combo in enumerate(combos):
            seed = base_seed + index
            yield generate(pick_story_params(combo, random.Random(seed), seed))
        return

    explicit_full = all((args.pen, args.ghost, args.shackle, args.gesture))
    if explicit_full:
        combo = (args.pen, args.ghost, args.shackle, args.gesture)
        for index in range(max(1, args.n)):
            seed = base_seed + index
            yield generate(pick_story_params(combo, random.Random(seed), seed))
        return

    shuffled = list(combos)
    random.Random(base_seed).shuffle(shuffled)
    count = max(1, args.n)
    for index in range(count):
        combo = shuffled[index % len(shuffled)]
        seed = base_seed + index
        yield generate(pick_story_params(combo, random.Random(seed), seed))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace:
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.asp:
            import asp

            model = asp.one_model(asp_program())
            rows = sorted(tuple(str(piece) for piece in atom) for atom in asp.atoms(model, "valid"))
            print(rows)
            return 0
        if args.verify:
            print(verify())
            return 0

        samples = list(iter_samples(args))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            header = ""
            if len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
