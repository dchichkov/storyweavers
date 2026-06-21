#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/brake_inner_monologue_folk_tale.py
=============================================================

A standalone storyworld for a small folk-tale-like domain built around a cart
brake, a child's inner monologue, and a lesson learned on a village hill.

Premise
-------
A village child must wheel a cart of precious goods down a path. The cart has a
brake. The path may be gentle or steep. The child is tempted to hurry, and the
story's turn comes from an inner argument: keep the brake on and go safely, or
let the cart run and trust luck. A wise elder helps if danger breaks loose.

The world model tracks physical meters (rolling, danger, broken, spilled) and
emotional memes (hurry, caution, fear, relief, pride, lesson). The rendered
story follows those state changes rather than swapping nouns into a frozen
template.

Run it
------
python storyworlds/worlds/gpt-5.4/brake_inner_monologue_folk_tale.py
python storyworlds/worlds/gpt-5.4/brake_inner_monologue_folk_tale.py --path mill_yard
python storyworlds/worlds/gpt-5.4/brake_inner_monologue_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/brake_inner_monologue_folk_tale.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/brake_inner_monologue_folk_tale.py --qa --json
python storyworlds/worlds/gpt-5.4/brake_inner_monologue_folk_tale.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives in storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to
# sys.path and then import results from there.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
HURRY_INIT = 5.0
PRUDENT_TRAITS = {"careful", "patient", "thoughtful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)


@dataclass
class Path:
    id: str
    label: str
    phrase: str
    steepness: int
    image: str
    danger_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    fragile: bool
    spill_word: str
    ending_image: str
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


def _r_runaway(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    path = world.entities.get("path")
    child = world.entities.get("child")
    if cart is None or path is None or child is None:
        return out
    if cart.meters["rolling"] < THRESHOLD:
        return out
    sig = ("runaway", "cart")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path.meters["danger"] += 1
    child.memes["fear"] += 1
    out.append("__runaway__")
    return out


def _r_breakage(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    cargo = world.entities.get("cargo")
    if cart is None or cargo is None:
        return out
    if cart.meters["crashed"] < THRESHOLD:
        return out
    sig = ("breakage", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["spilled"] += 1
    cargo.meters["broken"] += 1
    out.append("__breakage__")
    return out


CAUSAL_RULES = [
    Rule(name="runaway", tag="physical", apply=_r_runaway),
    Rule(name="breakage", tag="physical", apply=_r_breakage),
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
        for s in produced:
            world.say(s)
    return produced


def path_risky(path: Path) -> bool:
    return path.steepness > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity(path: Path, cargo: Cargo, delay: int) -> int:
    return path.steepness + cargo.weight + delay


def is_contained(response: Response, path: Path, cargo: Cargo, delay: int) -> bool:
    return response.power >= severity(path, cargo, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in PRUDENT_TRAITS else 3.0


def would_heed(trait: str, trust: int, cargo: Cargo) -> bool:
    return initial_caution(trait) + (trust / 3.0) > HURRY_INIT + (cargo.weight - 1)


def _do_release(world: World, narrate: bool = True) -> None:
    cart = world.get("cart")
    cart.meters["brake_off"] += 1
    cart.meters["rolling"] += 1
    propagate(world, narrate=narrate)


def predict_runaway(world: World, path: Path, cargo: Cargo) -> dict:
    sim = world.copy()
    sim.facts["path_cfg"] = path
    sim.facts["cargo_cfg"] = cargo
    _do_release(sim, narrate=False)
    return {
        "rolling": sim.get("cart").meters["rolling"] >= THRESHOLD,
        "danger": sim.get("path").meters["danger"],
    }


def open_tale(world: World, child: Entity, elder: Entity, path: Path, cargo: Cargo) -> None:
    world.say(
        f"In a valley village, where dawn laid gold on every roof, {child.id} was sent "
        f"to carry {cargo.phrase} along {path.phrase}."
    )
    world.say(
        f"The handcart was small, but its iron brake was strong, and the villagers said "
        f"that a strong brake was a quiet friend on a hill."
    )
    world.say(
        f"{elder.title_word.capitalize()} {elder.id} walked beside {child.pronoun('object')} at first, "
        f"and {path.image}."
    )


def elder_warning(world: World, child: Entity, elder: Entity, path: Path, cargo: Cargo) -> None:
    pred = predict_runaway(world, path, cargo)
    world.facts["predicted_danger"] = pred["danger"]
    child.memes["caution"] += 1
    world.say(
        f'When they reached the high part of the way, {elder.id} touched the cart handle and said, '
        f'"Keep your hand near the brake, {child.id}. A hill does not promise kindness to a hurried heart."'
    )


def inner_monologue(world: World, child: Entity, path: Path, cargo: Cargo) -> None:
    child.memes["hurry"] += 1
    extra = ""
    if cargo.weight >= 2:
        extra = " The load felt heavy, and the thought of letting the wheels pull ahead seemed easy."
    world.say(
        f'But inside {child.id} a little voice began to whisper: "If I loosen the brake, I shall be '
        f"at the bottom before the crows finish one song.{extra} Yet another voice answered, "
        f'"A fast wheel is not the same as a faithful wheel."'
    )


def heed(world: World, child: Entity, elder: Entity, path: Path, cargo: Cargo) -> None:
    cart = world.get("cart")
    cart.meters["brake_on"] += 1
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{child.id} drew a slow breath and thought, "Better a short delay than a long sorrow." '
        f"So {child.pronoun()} kept the brake snug beneath {child.pronoun('possessive')} palm and "
        f"walked the hill one careful step at a time."
    )
    world.say(
        f"The cart creaked, the wheels obeyed, and {cargo.label} reached {path.danger_spot} as safely "
        f"as if patient hands were carrying them."
    )
    world.say(
        f'{elder.id} smiled and said, "The wise do not wrestle with the hill. They make friends with the brake."'
    )


def release(world: World, child: Entity, cargo: Cargo) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'At last {child.id} thought, "Only for a little while. I am quick, and the hill is only earth." '
        f"With that, {child.pronoun()} eased the brake and let the cart nose forward."
    )
    world.para()
    _do_release(world)
    world.say(
        f"The wheels answered at once. What had been a cart became a clattering creature, and it ran for "
        f"{world.facts['path_cfg'].danger_spot} with {cargo.label} shaking inside."
    )


def alarm(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    world.say(
        f'"Grandmother! The brake!"' if elder.type == "grandmother"
        else f'"Grandfather! The brake!"'
    )
    world.say(
        f'{child.id} chased after the cart, but fear had made {child.pronoun("possessive")} legs smaller than the hill.'
    )


def rescue(world: World, elder: Entity, response: Response, cargo: Cargo) -> None:
    cart = world.get("cart")
    path_ent = world.get("path")
    cart.meters["rolling"] = 0.0
    path_ent.meters["danger"] = 0.0
    world.say(
        f"{elder.id} did not shout twice. {elder.pronoun().capitalize()} {response.text}."
    )
    world.say(
        f"The cart shuddered, bowed, and stopped. Inside, {cargo.label} trembled, but nothing was lost."
    )


def lesson(world: World, child: Entity, elder: Entity) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    world.say(
        f"{elder.id} set a steady hand on {child.id}'s shoulder and waited until the wild sound had gone from the wheels."
    )
    world.say(
        f'"Remember this," {elder.id} said softly. "A brake is not a chain for a cart. It is a promise that speed will '
        f"answer to sense.""
    )
    world.say(
        f'{child.id} bowed {child.pronoun("possessive")} head and thought, "I nearly traded care for pride, and pride would '
        f'have broken more than baskets."'
    )


def ending_safe(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    child.memes["joy"] += 1
    world.say(
        f"From then on, whenever {child.id} took the handcart along a slope, {child.pronoun()} listened first for the quieter "
        f"voice inside."
    )
    world.say(
        f"And in the market square that evening, {cargo.ending_image}, while {elder.id} told the tale to smiling neighbors."
    )


def rescue_fail(world: World, elder: Entity, response: Response, cargo: Cargo) -> None:
    cart = world.get("cart")
    cart.meters["crashed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{elder.id} {response.fail}."
    )
    world.say(
        f"The cart struck a stone by {world.facts['path_cfg'].danger_spot}, tipped hard, and the load flew out like startled birds."
    )
    if cargo.fragile:
        world.say(f"{cargo.label.capitalize()} broke at once.")
    else:
        world.say(f"{cargo.label.capitalize()} spilled across the dust.")

def ending_sad(world: World, child: Entity, elder: Entity, cargo: Cargo) -> None:
    child.memes["lesson"] += 1
    child.memes["grief"] += 1
    child.memes["love"] += 1
    world.say(
        f"{child.id} knelt in the road with hot cheeks and a cold heart. Inside, a plain thought answered all the proud ones: "
        f'"The brake was small, but my mistake was not."'
    )
    world.say(
        f'{elder.id} helped {child.pronoun("object")} gather what could still be saved and said, "A wise lesson costs less when it is '
        f'learned early. Keep this one."'
    )
    world.say(
        f"So the village remembered the day of the running cart, and {child.id} never again mistook haste for strength."
    )


def tell(
    path: Path,
    cargo: Cargo,
    response: Response,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_name: str = "Bela",
    elder_type: str = "grandmother",
    trait: str = "careful",
    delay: int = 0,
    trust: int = 7,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={"trust": trust},
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_type,
        role="elder",
    ))
    world.add(Entity(id="path", type="path", label=path.label, phrase=path.phrase))
    world.add(Entity(id="cart", type="cart", label="cart", phrase="a handcart"))
    world.add(Entity(id="cargo", type="cargo", label=cargo.label, phrase=cargo.phrase))

    child.memes["hurry"] = HURRY_INIT
    child.memes["caution"] = initial_caution(trait)
    world.facts["path_cfg"] = path
    world.facts["cargo_cfg"] = cargo
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["child"] = child
    world.facts["elder"] = elder

    open_tale(world, child, elder, path, cargo)
    world.para()
    elder_warning(world, child, elder, path, cargo)
    inner_monologue(world, child, path, cargo)

    if would_heed(trait, trust, cargo):
        world.para()
        heed(world, child, elder, path, cargo)
        outcome = "averted"
    else:
        world.para()
        release(world, child, cargo)
        alarm(world, child, elder, cargo)
        world.para()
        if is_contained(response, path, cargo, delay):
            rescue(world, elder, response, cargo)
            lesson(world, child, elder)
            world.para()
            ending_safe(world, child, elder, cargo)
            outcome = "contained"
        else:
            rescue_fail(world, elder, response, cargo)
            world.para()
            ending_sad(world, child, elder, cargo)
            outcome = "spilled"

    world.facts["outcome"] = outcome
    world.facts["severity"] = severity(path, cargo, delay) if outcome != "averted" else 0
    world.facts["heeded"] = outcome == "averted"
    return world


PATHS = {
    "bridge_hill": Path(
        id="bridge_hill",
        label="bridge hill",
        phrase="the steep road above the willow bridge",
        steepness=2,
        image="the road dropped in a long gray ribbon toward the river",
        danger_spot="the willow bridge",
        tags={"hill", "bridge"},
    ),
    "orchard_lane": Path(
        id="orchard_lane",
        label="orchard lane",
        phrase="the slanting lane beside the orchard wall",
        steepness=1,
        image="fallen pear leaves slid over the stones like little boats",
        danger_spot="the orchard gate",
        tags={"hill", "orchard"},
    ),
    "market_slope": Path(
        id="market_slope",
        label="market slope",
        phrase="the cobbled slope above the market square",
        steepness=2,
        image="the bell tower watched the road and the road watched the stalls below",
        danger_spot="the market square",
        tags={"hill", "market"},
    ),
    "mill_yard": Path(
        id="mill_yard",
        label="mill yard",
        phrase="the flat yard before the old mill",
        steepness=0,
        image="not a pebble there could teach a wheel to run",
        danger_spot="the mill gate",
        tags={"flat"},
    ),
}

CARGOES = {
    "eggs": Cargo(
        id="eggs",
        label="a basket of eggs",
        phrase="a basket of eggs for the baker",
        weight=1,
        fragile=True,
        spill_word="broken shells",
        ending_image="the eggs sat whole in their straw nests",
        tags={"eggs", "fragile"},
    ),
    "honey": Cargo(
        id="honey",
        label="three jars of honey",
        phrase="three jars of honey wrapped in cloth",
        weight=2,
        fragile=True,
        spill_word="sticky honey",
        ending_image="the honey jars shone amber in the late light",
        tags={"honey", "fragile"},
    ),
    "seed": Cargo(
        id="seed",
        label="a sack of seed grain",
        phrase="a sack of seed grain for the upper field",
        weight=2,
        fragile=False,
        spill_word="golden grain",
        ending_image="the seed sack rested unspilled beside the grain scales",
        tags={"seed"},
    ),
}

RESPONSES = {
    "pull_brake": Response(
        id="pull_brake",
        sense=3,
        power=4,
        text="ran beside the cart, seized the handle, and pulled the brake hard until the wheels cried and obeyed",
        fail="ran beside the cart and hauled at the brake, but the wheels had already taken too much of the hill into themselves",
        qa_text="ran beside the cart and pulled the brake hard until it stopped",
        tags={"brake", "help"},
    ),
    "wedge_wheel": Response(
        id="wedge_wheel",
        sense=3,
        power=3,
        text="snatched up a fallen branch and jammed it before the front wheel so the cart bucked and halted",
        fail="thrust a branch before the wheel, but it snapped and skittered away",
        qa_text="wedged the wheel with a branch and brought the cart to a halt",
        tags={"wheel", "help"},
    ),
    "grab_rim": Response(
        id="grab_rim",
        sense=1,
        power=2,
        text="caught the wheel rim with bare hands and somehow dragged the cart to stillness",
        fail="caught at the wheel rim with bare hands, but the spinning wood tore free",
        qa_text="caught the wheel rim with bare hands and stopped the cart",
        tags={"wheel", "help"},
    ),
}

GIRL_NAMES = ["Mira", "Tala", "Nina", "Iva", "Rosa", "Lina", "Mila", "Anya"]
BOY_NAMES = ["Toma", "Luka", "Niko", "Ivo", "Pavel", "Marek", "Jori", "Stefan"]
ELDER_NAMES = ["Bela", "Dora", "Ilma", "Marta", "Petra", "Yara", "Oren", "Milan"]
TRAITS = ["careful", "patient", "thoughtful", "steady", "eager", "proud", "restless"]


@dataclass
class StoryParams:
    path: str
    cargo: str
    response: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_type: str
    trait: str
    delay: int = 0
    trust: int = 7
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        path="bridge_hill",
        cargo="honey",
        response="pull_brake",
        child_name="Mira",
        child_gender="girl",
        elder_name="Bela",
        elder_type="grandmother",
        trait="careful",
        delay=0,
        trust=8,
    ),
    StoryParams(
        path="orchard_lane",
        cargo="eggs",
        response="wedge_wheel",
        child_name="Luka",
        child_gender="boy",
        elder_name="Marta",
        elder_type="grandmother",
        trait="proud",
        delay=0,
        trust=5,
    ),
    StoryParams(
        path="market_slope",
        cargo="honey",
        response="wedge_wheel",
        child_name="Nina",
        child_gender="girl",
        elder_name="Oren",
        elder_type="grandfather",
        trait="restless",
        delay=1,
        trust=3,
    ),
    StoryParams(
        path="bridge_hill",
        cargo="seed",
        response="pull_brake",
        child_name="Pavel",
        child_gender="boy",
        elder_name="Dora",
        elder_type="grandmother",
        trait="patient",
        delay=0,
        trust=9,
    ),
]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for path_id, path in PATHS.items():
        for cargo_id in CARGOES:
            if path_risky(path):
                combos.append((path_id, cargo_id))
    return combos


KNOWLEDGE = {
    "brake": [(
        "What does a brake do?",
        "A brake slows something down or stops it from rolling. It helps speed obey a careful hand."
    )],
    "hill": [(
        "Why is a cart harder to control on a hill?",
        "On a hill, the ground pulls the cart downward, so the wheels want to roll faster. That is why a brake matters more on a slope."
    )],
    "eggs": [(
        "Why do eggs break easily?",
        "Eggshells are thin and hard, but they crack when they are bumped or dropped. That is why people carry eggs gently."
    )],
    "honey": [(
        "Why are jars of honey tricky to carry?",
        "Glass jars can break if they bang together or hit the ground. If they break, sticky honey spills everywhere."
    )],
    "seed": [(
        "Why would spilled seed be a problem?",
        "Seed grain is meant for planting, so spilling it wastes food for the field. It can be gathered, but not every grain comes back clean."
    )],
    "help": [(
        "Why is it good to call an older helper when something runs away?",
        "A calm helper can think clearly and act fast. Asking for help early can stop a small danger from becoming a bigger one."
    )],
    "inner": [(
        "What is an inner monologue?",
        "An inner monologue is the quiet talk a person has inside their own mind. It lets a story show thoughts before a choice is made."
    )],
}
KNOWLEDGE_ORDER = ["inner", "brake", "hill", "eggs", "honey", "seed", "help"]


def explain_rejection(path: Path) -> str:
    return (
        f"(No story: {path.phrase} is flat, so a loosened brake would not create a believable runaway cart. "
        f"This world needs a real slope so the choice about the brake matters.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the safer responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_heed(params.trait, params.trust, CARGOES[params.cargo]):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], PATHS[params.path], CARGOES[params.cargo], params.delay) else "spilled"


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    path = world.facts["path_cfg"]
    cargo = world.facts["cargo_cfg"]
    outcome = world.facts["outcome"]
    if outcome == "averted":
        return [
            f'Write a folk tale for a young child that includes the word "brake" and shows a child listening to an inner voice before danger begins.',
            f"Tell a village tale where {child.id} guides a handcart down {path.label}, thinks carefully, and chooses the brake instead of speed.",
            f"Write a short folk-style story with inner monologue in which {cargo.label} reaches town safely because caution wins the argument inside the child's mind.",
        ]
    if outcome == "contained":
        return [
            f'Write a folk tale for a young child that includes the word "brake" and uses inner monologue before a runaway cart is stopped.',
            f"Tell a gentle cautionary tale where {child.id} loosens the brake on {path.label}, hears fear too late, and a wise elder saves {cargo.label}.",
            f"Write a story in folk-tale style where speed seems clever for one moment, but a child learns that a brake is a promise, not a burden.",
        ]
    return [
        f'Write a folk tale for a young child that includes the word "brake" and uses inner monologue before a mistake causes a loss.',
        f"Tell a cautionary village tale where {child.id} lets a cart run down {path.label}, and the lesson arrives after {cargo.label} is spilled or broken.",
        f"Write a sad but child-safe folk-style story in which a small proud thought beats a wiser one, and the child remembers the brake forever after.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    path = world.facts["path_cfg"]
    cargo = world.facts["cargo_cfg"]
    response = world.facts["response"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child guiding a handcart, and {elder.id}, the elder who walks the hill nearby."
        ),
        (
            "What made the brake important in this story?",
            f"The path was {path.label}, which slopes downward and can pull wheels faster than a child expects. The brake mattered because it was the one simple thing keeping the cart from running away."
        ),
        (
            f"What was {child.id} carrying?",
            f"{child.pronoun('subject').capitalize()} was carrying {cargo.phrase}. That made the trip feel important, because the load could be lost if the cart tipped."
        ),
        (
            f"What was the child's inner monologue about?",
            f"{child.id} argued with {child.pronoun('object')}self about whether to keep the brake on or let the hill do the work. One thought promised speed, but the wiser thought warned that fast wheels are not always faithful."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"Why did nothing bad happen?",
            f"Nothing bad happened because {child.id} listened to the careful voice inside and kept the brake under control. The danger stayed only a possibility, not an accident."
        ))
        qa.append((
            f"What lesson did {elder.id} teach?",
            f"{elder.id} taught that the brake was a friend, not a nuisance. The lesson is that a small careful choice can keep a whole day from turning sorrowful."
        ))
    elif outcome == "contained":
        body = response.qa_text
        qa.append((
            f"How was the runaway cart stopped?",
            f"{elder.id} {body}. That worked because the elder acted before the hill could give the cart too much speed."
        ))
        qa.append((
            f"How did {child.id} feel after the cart stopped?",
            f"{child.id} felt frightened first and relieved afterward. The fear came from seeing the cart obey the hill instead of {child.pronoun('object')}, and the relief came when the elder brought it back under control."
        ))
        qa.append((
            "What changed by the end of the story?",
            f"By the end, the brake was no longer just a piece of iron to {child.id}. It had become a lesson about listening to good sense before pride speaks too loudly."
        ))
    else:
        qa.append((
            f"What went wrong on the hill?",
            f"What went wrong was that {child.id} loosened the brake and the cart gathered too much speed. Once it struck the stone, {cargo.label} was lost because the hill had become stronger than anyone's hands."
        ))
        qa.append((
            f"What did {child.id} learn from losing {cargo.label}?",
            f"{child.id} learned that haste can cost more than patience ever does. The inner voice that warned {child.pronoun('object')} turned out to be the truest one."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"brake", "hill", "inner", "help"} | set(world.facts["cargo_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
risky_path(P) :- path(P), steepness(P, S), S > 0.
valid(P, C)   :- risky_path(P), cargo(C).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
prudent_trait(T) :- trait(T), is_prudent(T).
init_caution(5)  :- prudent_trait(T), trait(T).
init_caution(3)  :- trait(T), not prudent_trait(T).
heeding_score(C + Tr) :- init_caution(C), trust(Trust), Tr = Trust / 3.
hurry_score(H + Extra) :- hurry_init(H), cargo_weight(W), Extra = W - 1.
averted :- heeding_score(HS), hurry_score(HR), HS > HR.

severity(S + W + D) :- chosen_path(P), steepness(P, S), chosen_cargo(C), weight(C, W), delay(D).
contained :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(spilled)   :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("steepness", path_id, path.steepness))
    for cargo_id, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("weight", cargo_id, cargo.weight))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("hurry_init", int(HURRY_INIT)))
    for trait in sorted(PRUDENT_TRAITS):
        lines.append(asp.fact("is_prudent", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_path", params.path),
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("trait", params.trait),
        asp.fact("trust", params.trust),
        asp.fact("cargo_weight", CARGOES[params.cargo].weight),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folk tale of a cart brake, a hill, and an inner warning."
    )
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra breaths before the elder reaches the cart")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.path and not path_risky(PATHS[args.path]):
        raise StoryError(explain_rejection(PATHS[args.path]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.path is None or c[0] == args.path)
        and (args.cargo is None or c[1] == args.cargo)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    path_id, cargo_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = rng.choice(["girl", "boy"])
    child_name = pick_name(rng, child_gender)
    elder_name = rng.choice(ELDER_NAMES)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    trust = rng.randint(2, 9)
    return StoryParams(
        path=path_id,
        cargo=cargo_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_name=elder_name,
        elder_type=elder_type,
        trait=trait,
        delay=delay,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not path_risky(PATHS[params.path]):
        raise StoryError(explain_rejection(PATHS[params.path]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        PATHS[params.path],
        CARGOES[params.cargo],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        trait=params.trait,
        delay=params.delay,
        trust=params.trust,
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

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            case = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        case.seed = seed
        cases.append(case)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py} clingo={cl}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        sens = asp_sensible()
        print(f"sensible responses: {', '.join(sens)}\n")
        print(f"{len(combos)} compatible (path, cargo) combos:\n")
        for path_id, cargo_id in combos:
            print(f"  {path_id:12} {cargo_id}")
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
            header = f"### {p.child_name}: {p.cargo} on {p.path} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
