#!/usr/bin/env python3
"""A child-friendly ghost story about a shackle, a petting zoo, and friendship."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from storyworlds.results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "At a petting zoo after closing time, a child hears a shackle tremble on a pen gate. "
    "A lonely little ghost is not trying to scare anyone; the ghost is trying to keep an "
    "animal from being frightened or wandering in the dark. The child notices what the "
    "shackle and gate physically need, answers with a kind repair, and turns the haunting "
    "into a friendship that can be seen in the settled pen by the end of the night."
)


@dataclass(frozen=True)
class Pen:
    id: str
    name: str
    animal_name: str
    animal_kind: str
    spooky_image: str
    risk_text: str
    ending_image: str
    required_tags: tuple[str, ...]


@dataclass(frozen=True)
class Ghost:
    id: str
    name: str
    role: str
    worry: str
    whisper: str
    request: str
    accepted_repairs: tuple[str, ...]
    required_tags: tuple[str, ...]


@dataclass(frozen=True)
class Shackle:
    id: str
    label: str
    sound: str
    texture: str
    memory: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class Repair:
    id: str
    action: str
    promise: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class StoryParams:
    pen: str
    ghost: str
    shackle: str
    repair: str
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


@dataclass
class PettingZooWorld:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def meter(self, entity_id: str, name: str, delta: int) -> None:
        entity = self.entities[entity_id]
        entity.meters[name] = entity.meters.get(name, 0) + delta

    def meme(self, entity_id: str, name: str, delta: int) -> None:
        entity = self.entities[entity_id]
        entity.memes[name] = entity.memes.get(name, 0) + delta

    def set_meter(self, entity_id: str, name: str, value: int) -> None:
        self.entities[entity_id].meters[name] = value

    def set_meme(self, entity_id: str, name: str, value: int) -> None:
        self.entities[entity_id].memes[name] = value

    def record(self, event_id: str, text: str, actor: str, target: str | None = None) -> None:
        self.history.append(Event(event_id, text, actor, target))


PENS = {
    "goat_walk": Pen(
        id="goat_walk",
        name="the goat walk behind the lantern shed",
        animal_name="Pip",
        animal_kind="goat",
        spooky_image="the moon drew fence shadows that looked like thin fingers over the straw",
        risk_text="Pip kept nudging the gate with his horns, and each hard rattle sounded close to a gate that might give up before morning.",
        ending_image="Pip folded his legs under himself beside the rail while the gate stayed still and round with moonlight",
        required_tags=("hold", "quiet"),
    ),
    "lamb_corner": Pen(
        id="lamb_corner",
        name="the lamb corner near the hand-washing pump",
        animal_name="Mallow",
        animal_kind="lamb",
        spooky_image="wet pump handles glimmered as if they were listening",
        risk_text="Mallow shrank deeper into the straw every time the latch clicked, as though the sound itself might chase sleep away from the whole pen.",
        ending_image="Mallow rested his chin on the fence board and let the night settle around his small ears",
        required_tags=("soft", "quiet"),
    ),
    "calf_yard": Pen(
        id="calf_yard",
        name="the calf yard beside the red barn door",
        animal_name="Juniper",
        animal_kind="calf",
        spooky_image="the barn windows held pale squares of moonlight like watchful eyes",
        risk_text="Juniper kept turning toward the dark aisle between the barns, and the loose latch looked too uncertain to guide her back if she startled.",
        ending_image="Juniper stood by the gate without pulling at it, listening to one gentle sound and no longer to the dark barn aisle",
        required_tags=("hold", "guide"),
    ),
}

GHOSTS = {
    "orla": Ghost(
        id="orla",
        name="Orla",
        role="a patient goat girl from long ago",
        worry="a restless gate would answer the animal with fear instead of safety",
        whisper='"I only wanted the gate to stop sounding frightened," whispered Orla.',
        request="make the shackle feel steady enough for the animal in the pen",
        accepted_repairs=("oil_cloth", "humming_knot"),
        required_tags=("hold", "care"),
    ),
    "wren": Ghost(
        id="wren",
        name="Wren",
        role="a shy lamb tender with moon-pale braids",
        worry="one sharp clink would keep the smallest animal trembling all night",
        whisper='"The little ones sleep better when the metal remembers kindness," whispered Wren.',
        request="make the shackle soft and quiet for a timid friend",
        accepted_repairs=("blanket_wrap", "oil_cloth"),
        required_tags=("soft", "care"),
    ),
    "tomas": Ghost(
        id="tomas",
        name="Tomas",
        role="an old calf groom with a gentle lantern smile",
        worry="the animal would follow the darkest aisle instead of the safe gate",
        whisper='"If the gate gives one friendly note, she will choose home," whispered Tomas.',
        request="give the shackle a calm sound that guides without frightening",
        accepted_repairs=("friendship_bell", "humming_knot"),
        required_tags=("guide", "care"),
    ),
}

SHACKLES = {
    "brass_loop": Shackle(
        id="brass_loop",
        label="a brass shackle",
        sound="a clipped clink under the moon",
        texture="worn smooth in some places and cold in others",
        memory="It still held the shape of many careful hands.",
        tags=("hold", "care"),
    ),
    "felt_loop": Shackle(
        id="felt_loop",
        label="a felt-wrapped shackle",
        sound="a muffled tap like a spoon under a blanket",
        texture="soft at the edges but thin where the cloth had frayed",
        memory="A faded strip of fair-day felt still hugged one side of the ring.",
        tags=("soft", "quiet", "care"),
    ),
    "silver_loop": Shackle(
        id="silver_loop",
        label="a silver shackle",
        sound="a light ringing thread of sound",
        texture="cool as dew and bright where the moon touched it",
        memory="It seemed made for carrying one good note through the dark.",
        tags=("quiet", "guide"),
    ),
}

REPAIRS = {
    "oil_cloth": Repair(
        id="oil_cloth",
        action="rub the shackle with lamp oil and a clean feed cloth",
        promise="quiet the scrape and show the gate it was still worth caring for",
        tags=("quiet", "care"),
    ),
    "blanket_wrap": Repair(
        id="blanket_wrap",
        action="wrap the shackle with a strip of soft stable blanket",
        promise="give the metal a gentler voice for a nervous animal",
        tags=("soft", "care"),
    ),
    "friendship_bell": Repair(
        id="friendship_bell",
        action="tie a tiny friendship bell beside the shackle",
        promise="turn the gate's sound into a friendly guide instead of a warning",
        tags=("guide", "care"),
    ),
    "humming_knot": Repair(
        id="humming_knot",
        action="thread a humming knot of twine through the shackle and pull it snug",
        promise="help the gate hold fast while answering back in a softer way",
        tags=("hold", "quiet", "care"),
    ),
}


ASP_RULES = r"""
combined_tag(S, R, T) :- shackle(S), repair(R), shackle_tag(S, T).
combined_tag(S, R, T) :- shackle(S), repair(R), repair_tag(R, T).

invalid(P, G, S, R) :- pen(P), ghost(G), shackle(S), repair(R), pen_need(P, T), not combined_tag(S, R, T).
invalid(P, G, S, R) :- pen(P), ghost(G), shackle(S), repair(R), ghost_need(G, T), not combined_tag(S, R, T).
invalid(P, G, S, R) :- pen(P), ghost(G), shackle(S), repair(R), not ghost_accepts(G, R).

valid(P, G, S, R) :- pen(P), ghost(G), shackle(S), repair(R), not invalid(P, G, S, R).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pen", choices=sorted(PENS))
    parser.add_argument("--ghost", choices=sorted(GHOSTS))
    parser.add_argument("--shackle", choices=sorted(SHACKLES))
    parser.add_argument("--repair", choices=sorted(REPAIRS))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def combined_tags(params: StoryParams) -> set[str]:
    return set(SHACKLES[params.shackle].tags) | set(REPAIRS[params.repair].tags)


def valid_params(params: StoryParams) -> tuple[bool, str]:
    if params.pen not in PENS:
        return False, f"unknown pen: {params.pen}"
    if params.ghost not in GHOSTS:
        return False, f"unknown ghost: {params.ghost}"
    if params.shackle not in SHACKLES:
        return False, f"unknown shackle: {params.shackle}"
    if params.repair not in REPAIRS:
        return False, f"unknown repair: {params.repair}"

    pen = PENS[params.pen]
    ghost = GHOSTS[params.ghost]
    tags = combined_tags(params)

    if params.repair not in ghost.accepted_repairs:
        return False, f"{ghost.name} would not trust the {params.repair} repair in this haunting"
    for tag in pen.required_tags:
        if tag not in tags:
            return False, f"{pen.name} needs a {tag} answer before the pen can settle"
    for tag in ghost.required_tags:
        if tag not in tags:
            return False, f"{ghost.name} needs a {tag} answer before friendship can happen"
    return True, ""


def all_params() -> list[StoryParams]:
    options: list[StoryParams] = []
    for pen in PENS:
        for ghost in GHOSTS:
            for shackle in SHACKLES:
                for repair in REPAIRS:
                    params = StoryParams(pen=pen, ghost=ghost, shackle=shackle, repair=repair)
                    if valid_params(params)[0]:
                        options.append(params)
    return options


def filtered_params(args: argparse.Namespace) -> list[StoryParams]:
    return [
        params
        for params in all_params()
        if (args.pen is None or params.pen == args.pen)
        and (args.ghost is None or params.ghost == args.ghost)
        and (args.shackle is None or params.shackle == args.shackle)
        and (args.repair is None or params.repair == args.repair)
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> StoryParams:
    candidates = filtered_params(args)
    if not candidates:
        probe = StoryParams(
            pen=args.pen or sorted(PENS)[0],
            ghost=args.ghost or sorted(GHOSTS)[0],
            shackle=args.shackle or sorted(SHACKLES)[0],
            repair=args.repair or sorted(REPAIRS)[0],
            seed=args.seed,
        )
        ok, reason = valid_params(probe)
        raise StoryError(reason if not ok else "no valid story matches the requested partial choices")
    chooser = rng or random.Random(args.seed)
    picked = chooser.choice(candidates)
    return StoryParams(
        pen=picked.pen,
        ghost=picked.ghost,
        shackle=picked.shackle,
        repair=picked.repair,
        seed=args.seed,
    )


def make_world(params: StoryParams) -> PettingZooWorld:
    pen = PENS[params.pen]
    ghost = GHOSTS[params.ghost]
    shackle = SHACKLES[params.shackle]
    world = PettingZooWorld(params=params)
    world.add(
        Entity(
            id="child",
            name="Mira",
            kind="child",
            location=pen.name,
            meters={"steady_hands": 1, "warmth": 1},
            memes={"fear": 1, "care": 1, "friendship": 0},
        )
    )
    world.add(
        Entity(
            id="ghost",
            name=ghost.name,
            kind="ghost",
            location=pen.name,
            meters={"visible": 0, "glow": 1},
            memes={"loneliness": 2, "trust": 0, "friendship": 0},
        )
    )
    world.add(
        Entity(
            id="animal",
            name=pen.animal_name,
            kind=pen.animal_kind,
            location=pen.name,
            meters={"calm": 0, "wander_risk": 1},
            memes={"trust": 0},
        )
    )
    world.add(
        Entity(
            id="gate",
            name="the pen gate",
            kind="gate",
            location=pen.name,
            meters={"secure": 0, "noise": 1, "guiding_sound": 0},
            memes={},
        )
    )
    world.add(
        Entity(
            id="shackle",
            name=shackle.label,
            kind="shackle",
            location=pen.name,
            meters={
                "quiet": 1 if "quiet" in shackle.tags else 0,
                "soft": 1 if "soft" in shackle.tags else 0,
                "hold": 1 if "hold" in shackle.tags else 0,
            },
            memes={"memory": 1},
        )
    )
    world.facts["source_tale"] = SOURCE_TALE
    world.facts["combined_tags"] = sorted(combined_tags(params))
    world.facts["ending"] = "unresolved"
    world.facts["friendship_object"] = shackle.label
    return world


def opening_pass(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    shackle = SHACKLES[world.params.shackle]
    world.record(
        "opening",
        f"After the petting zoo closed, Mira carried the last brush bucket past {pen.name}, where {pen.spooky_image}. "
        f"On the gate hung {shackle.label}, {shackle.texture}. {shackle.memory}",
        "child",
        "shackle",
    )


def ghost_reveal(world: PettingZooWorld) -> None:
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]
    world.set_meter("ghost", "visible", 1)
    world.meme("child", "fear", 1)
    world.record(
        "reveal",
        f"Then {shackle.label} gave {shackle.sound}, and the pale shape of {ghost.name}, {ghost.role}, rose beside the latch. "
        f"{ghost.whisper} {ghost.name} wanted Mira to {ghost.request}.",
        "ghost",
        "child",
    )


def show_risk(world: PettingZooWorld) -> None:
    pen = PENS[world.params.pen]
    world.meter("animal", "wander_risk", 1)
    world.record("risk", pen.risk_text, "animal", "gate")


def understanding_line(world: PettingZooWorld) -> str:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    needs = set(pen.required_tags) | set(ghost.required_tags)
    ghost = GHOSTS[world.params.ghost]
    if "guide" in needs:
        return f"Mira understood that {ghost.name} was trying to guide a friend home, not pull anyone into a fright."
    if "soft" in needs:
        return f"Mira understood that the haunting was asking for gentleness more than silence."
    return f"Mira understood that the ghost was guarding the gate the way a friend stands watch."


def apply_repair(world: PettingZooWorld) -> None:
    repair = REPAIRS[world.params.repair]
    tags = set(world.facts["combined_tags"])
    world.meme("child", "care", 1)
    world.meme("ghost", "trust", 1)
    if "quiet" in tags:
        world.set_meter("gate", "noise", 0)
        world.set_meter("shackle", "quiet", 2)
        world.set_meme("child", "fear", max(0, world.entities["child"].memes["fear"] - 1))
    if "soft" in tags:
        world.set_meter("shackle", "soft", 2)
        world.meter("animal", "calm", 1)
    if "hold" in tags:
        world.set_meter("gate", "secure", 2)
        world.set_meter("shackle", "hold", 2)
        world.set_meter("animal", "wander_risk", 0)
    if "guide" in tags:
        world.set_meter("gate", "guiding_sound", 1)
        world.meter("animal", "calm", 1)
        world.meme("animal", "trust", 1)
    world.record(
        "repair",
        f"Mira chose to {repair.action}. She wanted to {repair.promise}.",
        "child",
        "shackle",
    )


def friendship_turn(world: PettingZooWorld) -> None:
    animal = world.entities["animal"]
    ghost = world.entities["ghost"]
    gate = world.entities["gate"]
    pen = PENS[world.params.pen]
    ghost_cfg = GHOSTS[world.params.ghost]
    needs = set(pen.required_tags) | set(ghost_cfg.required_tags)
    if "guide" in needs and gate.meters["guiding_sound"] > 0:
        motion = f"{animal.name} listened to the new little note and stepped back toward the gate instead of the dark aisle."
    elif "soft" in needs and world.entities["shackle"].meters["soft"] > 0:
        motion = f"{animal.name} stopped trembling and leaned close enough to breathe on the quieted latch."
    else:
        motion = f"The gate gave one low answer instead of a harsh rattle, and {animal.name} no longer looked ready to bolt."
    world.record("turn", motion, "animal", "gate")

    if gate.meters["secure"] < 1:
        world.set_meter("gate", "secure", 1)
    if animal.meters["calm"] < 1:
        world.set_meter("animal", "calm", 1)
    world.meme("ghost", "trust", 1)
    world.set_meme("ghost", "loneliness", max(0, ghost.memes["loneliness"] - 1))
    world.record(
        "friendship",
        f"{ghost.name} laid transparent fingers on the rail and smiled when the gate held steady. "
        f'"You heard the work I was trying to do," {ghost.name} said.',
        "ghost",
        "child",
    )


def resolve_friendship(world: PettingZooWorld) -> None:
    child = world.entities["child"]
    ghost = world.entities["ghost"]
    animal = world.entities["animal"]
    gate = world.entities["gate"]
    if gate.meters["secure"] < 1:
        raise StoryError("the gate never became secure enough for a true ending")
    if animal.meters["calm"] < 1:
        raise StoryError("the animal never settled, so the story stays unresolved")
    if ghost.memes["trust"] < 2:
        raise StoryError("the ghost never trusted the child enough for friendship")
    child.memes["friendship"] = 1
    ghost.memes["friendship"] = 1
    animal.memes["trust"] = max(1, animal.memes["trust"])
    world.facts["ending"] = "friendship"


def render_story(world: PettingZooWorld) -> str:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]
    first = " ".join(event.text for event in world.history[:3])
    second = " ".join([understanding_line(world), world.history[3].text, world.history[4].text])
    if world.entities["gate"].meters["guiding_sound"] > 0:
        ending_hook = "The tiny friendly note kept pointing home instead of sounding an alarm."
    elif world.entities["shackle"].meters["soft"] > 1:
        ending_hook = "The shackle sounded softer than the night insects in the straw."
    else:
        ending_hook = "The old metal no longer spoke in lonely jolts."
    ending = (
        f"Before Mira left, {pen.ending_image}, and {ghost.name} stayed beside her instead of melting back into worry. "
        f"{ending_hook} From then on, Mira thought of {shackle.label} as the place where fear was fastened shut and friendship was fastened on."
    )
    intro = "The petting zoo was meant to be quiet, but one little piece of metal still had a story to tell."
    return "\n\n".join([f"{intro} {first}", second, ending])


def build_prompts(world: PettingZooWorld) -> list[str]:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    return [
        "Write a ghost story set in a petting zoo.",
        f"Make the word shackle matter physically in {pen.name}.",
        f"Let friendship grow between Mira and {ghost.name} while keeping {pen.animal_name} safe through the night.",
    ]


def build_story_qa(world: PettingZooWorld) -> list[QAItem]:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    repair = REPAIRS[world.params.repair]
    shackle = SHACKLES[world.params.shackle]
    return [
        QAItem(
            question="Why was the ghost rattling the shackle at the start?",
            answer=(
                f"{ghost.name} rattled {shackle.label} because {ghost.worry}. "
                f"The ghost used the only object on the gate that could call attention to the danger in {pen.name}."
            ),
        ),
        QAItem(
            question="How did Mira answer the haunting without running away?",
            answer=(
                f"Mira answered it by choosing to {repair.action}. "
                f"That repair changed the actual gate, so the ghost could trust that Mira understood the work of keeping {pen.animal_name} safe."
            ),
        ),
        QAItem(
            question="What proves that friendship changed the ending of the story?",
            answer=(
                f"The ending proves it because {pen.ending_image}. "
                f"The animal is calm, the gate is no longer speaking in fear, and {ghost.name} stays near Mira like a friend instead of a warning."
            ),
        ),
    ]


def build_world_qa(world: PettingZooWorld) -> list[QAItem]:
    pen = PENS[world.params.pen]
    ghost = GHOSTS[world.params.ghost]
    shackle = SHACKLES[world.params.shackle]
    return [
        QAItem(
            question="Which physical object carried the biggest change in this world?",
            answer=(
                f"The main carrier was {shackle.label}. "
                "Once the shackle changed, the gate sounded and behaved differently, so the friendship had a physical place to live."
            ),
        ),
        QAItem(
            question="Why does the petting-zoo setting matter to the ghost story?",
            answer=(
                f"The petting-zoo setting matters because the haunting grows out of caring for {pen.animal_name} in a real pen after closing time. "
                "The fear is tied to fences, straw, and latch work, not to a vague spooky feeling."
            ),
        ),
        QAItem(
            question="Why is friendship more than a feeling in this world?",
            answer=(
                f"Friendship matters because Mira and {ghost.name} cooperate to solve the exact problem in {pen.name}. "
                "Their bond is visible in the settled animal, the safer gate, and the shackle that no longer needs to cry for help."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)

    world = make_world(params)
    opening_pass(world)
    ghost_reveal(world)
    show_risk(world)
    apply_repair(world)
    friendship_turn(world)
    resolve_friendship(world)

    return StorySample(
        params=params,
        story=render_story(world),
        prompts=build_prompts(world),
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
        world=world,
    )


def asp_facts() -> str:
    from storyworlds import asp

    facts: list[str] = []
    for pen in PENS.values():
        facts.append(asp.fact("pen", pen.id))
        for tag in pen.required_tags:
            facts.append(asp.fact("pen_need", pen.id, tag))
    for ghost in GHOSTS.values():
        facts.append(asp.fact("ghost", ghost.id))
        for repair in ghost.accepted_repairs:
            facts.append(asp.fact("ghost_accepts", ghost.id, repair))
        for tag in ghost.required_tags:
            facts.append(asp.fact("ghost_need", ghost.id, tag))
    for shackle in SHACKLES.values():
        facts.append(asp.fact("shackle", shackle.id))
        for tag in shackle.tags:
            facts.append(asp.fact("shackle_tag", shackle.id, tag))
    for repair in REPAIRS.values():
        facts.append(asp.fact("repair", repair.id))
        for tag in repair.tags:
            facts.append(asp.fact("repair_tag", repair.id, tag))
    return "\n".join(facts)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid/4.\n"


def verify_asp_and_world() -> str:
    from storyworlds import asp

    py_valid = {(p.pen, p.ghost, p.shackle, p.repair) for p in all_params()}
    model = asp.one_model(asp_program())
    asp_valid = {tuple(str(piece) for piece in atom) for atom in asp.atoms(model, "valid")}
    if py_valid != asp_valid:
        only_python = sorted(py_valid - asp_valid)
        only_asp = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python[:5]} only_asp={only_asp[:5]}")

    exercised = 0
    for params in all_params():
        sample = generate(params)
        exercised += 1
        if "shackle" not in sample.story.lower():
            raise StoryError(f"generated story lost the seed word for params={params}")
        if "petting zoo" not in sample.story.lower():
            raise StoryError(f"generated story lost the setting phrase for params={params}")
        if sample.world.facts.get("ending") != "friendship":
            raise StoryError(f"generated story did not reach friendship for params={params}")
        if len(sample.prompts) != 3 or len(sample.story_qa) != 3 or len(sample.world_qa) != 3:
            raise StoryError(f"generated QA/prompts were incomplete for params={params}")
        if "{" in sample.story or "meters=" in sample.story or "memes=" in sample.story:
            raise StoryError(f"generated story leaked scaffolding for params={params}")
        if sample.story.count("\n\n") < 2:
            raise StoryError(f"generated story did not form a complete three-part arc for params={params}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid petting-zoo ghost stories; exercised {exercised} renders."


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    candidates = filtered_params(args)
    if args.all:
        for params in candidates:
            yield generate(params)
        return

    if not candidates:
        raise StoryError("no valid story matches the requested partial choices")

    rng = random.Random(args.seed)
    order = list(candidates)
    rng.shuffle(order)
    total = max(1, args.n)
    for index in range(total):
        picked = order[index % len(order)]
        yield generate(
            StoryParams(
                pen=picked.pen,
                ghost=picked.ghost,
                shackle=picked.shackle,
                repair=picked.repair,
                seed=args.seed,
            )
        )


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if header:
        print(header)
    print(sample.story)
    if args.trace:
        print("\nTrace:")
        for event in sample.world.history:
            print(f"- {event.id}: {event.text}")
        print("\nState:")
        for entity in sample.world.entities.values():
            print(f"- {entity.id}: meters={entity.meters} memes={entity.memes}")
    if args.qa:
        print("\nPrompts:")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nStory QA:")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\nWorld QA:")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.asp:
            from storyworlds import asp

            model = asp.one_model(asp_program())
            tuples = sorted(tuple(str(piece) for piece in atom) for atom in asp.atoms(model, "valid"))
            print(tuples)
            return 0
        if args.verify:
            print(verify_asp_and_world())
            return 0

        samples = list(iter_samples(args))
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            if index:
                print("\n---\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
