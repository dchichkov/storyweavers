#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ore_trestle_fake_basement_stairs_repetition_sound.py
==============================================================================

A small storyworld about two children turning the basement stairs into a tiny
pretend mine. They carry "ore" on a household quest, build a fake trestle on
the stairs, hear it wobble, and learn to change the game in a safer way.

The domain aims for a child-facing slice-of-life feel:
- a home setting (the basement stairs),
- a concrete pretend quest,
- repeated chant-like language,
- sound effects that come from world state,
- a calm adult fix that changes the ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/ore_trestle_fake_basement_stairs_repetition_sound.py
    python storyworlds/worlds/gpt-5.4/ore_trestle_fake_basement_stairs_repetition_sound.py --ore washer_ore --trestle milk_crates
    python storyworlds/worlds/gpt-5.4/ore_trestle_fake_basement_stairs_repetition_sound.py --plan tiptoe_faster
    python storyworlds/worlds/gpt-5.4/ore_trestle_fake_basement_stairs_repetition_sound.py --all --qa
    python storyworlds/worlds/gpt-5.4/ore_trestle_fake_basement_stairs_repetition_sound.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or this nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CAUTIOUS_TRAITS = {"careful", "steady", "sensible"}


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
class Ore:
    id: str
    label: str
    phrase: str
    clink: str
    weight: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Trestle:
    id: str
    label: str
    phrase: str
    wobble: int
    sound: str
    shape: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Plan:
    id: str
    label: str
    sense: int
    power: int
    text: str
    end_image: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    ore: str
    trestle: str
    plan: str
    destination: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    seeker_age: int = 5
    helper_age: int = 6
    chant: str = "Ore for the tunnel!"
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"seeker", "helper"}]

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


def _r_wobble_fear(world: World) -> list[str]:
    trestle = world.entities.get("trestle")
    if trestle is None:
        return []
    if trestle.meters["wobble"] < THRESHOLD:
        return []
    sig = ("wobble", "fear")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    if "stairs" in world.entities:
        world.get("stairs").meters["danger"] += 1
    return ["__wobble__"]


def _r_spill_disappointment(world: World) -> list[str]:
    ore = world.entities.get("ore")
    if ore is None or ore.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill", "sad")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["disappointment"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wobble_fear", tag="physical", apply=_r_wobble_fear),
    Rule(name="spill_disappointment", tag="emotional", apply=_r_spill_disappointment),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(s for s in produced if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


ORES = {
    "washer_ore": Ore(
        id="washer_ore",
        label="ore",
        phrase="a tin cup full of washer ore",
        clink="clink, clink, clink",
        weight=1,
        tags={"ore", "metal", "sound"},
    ),
    "river_ore": Ore(
        id="river_ore",
        label="ore",
        phrase="a bucket of smooth gray ore pebbles",
        clink="clack, clack",
        weight=2,
        tags={"ore", "rock", "sound"},
    ),
    "brick_ore": Ore(
        id="brick_ore",
        label="ore",
        phrase="three heavy red ore chunks",
        clink="thunk, thunk",
        weight=3,
        tags={"ore", "rock", "heavy"},
    ),
}

TRESTLES = {
    "milk_crates": Trestle(
        id="milk_crates",
        label="fake trestle",
        phrase="a fake trestle made from two milk crates and a board",
        wobble=1,
        sound="creak, creak",
        shape="sat across the bottom steps like a skinny little bridge",
        tags={"trestle", "bridge"},
    ),
    "cardboard_boxes": Trestle(
        id="cardboard_boxes",
        label="fake trestle",
        phrase="a fake trestle made from cardboard boxes and a shelf board",
        wobble=2,
        sound="fwump, creak",
        shape="leaned across the stairs in a brave-looking but wobbly line",
        tags={"trestle", "cardboard"},
    ),
    "laundry_basket": Trestle(
        id="laundry_basket",
        label="fake trestle",
        phrase="a fake trestle balanced on an upside-down laundry basket and a stool",
        wobble=2,
        sound="rattle, creak",
        shape="rose over the steps like something borrowed from a game and not from real builders",
        tags={"trestle", "laundry"},
    ),
}

PLANS = {
    "move_floor": Plan(
        id="move_floor",
        label="move the quest to the basement floor",
        sense=3,
        power=5,
        text="helped them carry the bridge pieces off the stairs and rebuild the quest on the flat basement floor",
        end_image="The pretend track now ran safely beside the washer, not over the stairs.",
        qa_text="moved the pretend mine off the stairs and onto the basement floor",
        tags={"safe_floor", "adult_help"},
    ),
    "small_pan": Plan(
        id="small_pan",
        label="use a small pan and walk one trip at a time",
        sense=3,
        power=3,
        text="gave them a small metal pan for the ore and had them take one slow trip at a time while holding the rail",
        end_image="Each tiny load made a bright little ring in the pan, and the game slowed down into something steady.",
        qa_text="gave them a small pan and made the trips smaller and steadier",
        tags={"small_load", "handrail"},
    ),
    "handrail": Plan(
        id="handrail",
        label="hold the handrail with a light load",
        sense=2,
        power=2,
        text="poured half the ore back into the bowl and reminded them that one hand was for the rail and one hand was for the cup",
        end_image="The cup was light, the rail was firm, and their feet made small careful taps instead of wild stomps.",
        qa_text="lightened the load and had them keep one hand on the rail",
        tags={"handrail"},
    ),
    "tiptoe_faster": Plan(
        id="tiptoe_faster",
        label="tiptoe faster",
        sense=1,
        power=1,
        text="told them to go faster before the bridge could wobble",
        end_image="",
        qa_text="told them to hurry across",
        tags={"bad_idea"},
    ),
}

DESTINATIONS = {
    "coal_bin": Destination(
        id="coal_bin",
        label="the coal-bin cave",
        phrase="the old coal-bin cave under the stairs",
        ending="their pretend mine had reached the coal-bin cave at last",
        tags={"quest", "basement"},
    ),
    "workbench": Destination(
        id="workbench",
        label="the workbench station",
        phrase="the workbench station at the far end of the basement",
        ending="their pretend ore train finally reached the workbench station",
        tags={"quest", "basement"},
    ),
    "paint_shelf": Destination(
        id="paint_shelf",
        label="the paint-shelf tunnel",
        phrase="the paint-shelf tunnel near the wall",
        ending="their little ore quest ended at the paint-shelf tunnel with a satisfied clink",
        tags={"quest", "basement"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "curious", "steady", "brave", "sensible", "thoughtful"]
CHANTS = [
    "Ore for the tunnel!",
    "Ore for the tunnel, ore for the tunnel!",
    "Clink and carry, clink and carry!",
]


def severity(ore: Ore, trestle: Trestle) -> int:
    return ore.weight + trestle.wobble


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def plan_works(ore: Ore, trestle: Trestle, plan: Plan) -> bool:
    return plan.sense >= SENSE_MIN and plan.power >= severity(ore, trestle)


def cautious_value(trait: str) -> int:
    return 5 if trait in CAUTIOUS_TRAITS else 3


def would_avert(relation: str, seeker_age: int, helper_age: int, trait: str) -> bool:
    return relation == "siblings" and helper_age > seeker_age and cautious_value(trait) >= 5


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for ore_id, ore in ORES.items():
        for trestle_id, trestle in TRESTLES.items():
            for plan_id, plan in PLANS.items():
                if plan_works(ore, trestle, plan):
                    combos.append((ore_id, trestle_id, plan_id))
    return combos


def explain_rejection(plan: Plan, ore: Ore, trestle: Trestle) -> str:
    if plan.sense < SENSE_MIN:
        better = ", ".join(sorted(p.id for p in sensible_plans()))
        return (
            f"(Refusing plan '{plan.id}': it is not sensible enough for a storyworld "
            f"(sense={plan.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {plan.label} does not really solve the risk of {ore.phrase} on "
        f"{trestle.phrase} over the basement stairs. The load is too heavy or the "
        f"bridge is too wobbly, so pick a stronger plan.)"
    )


def predict_crossing(world: World, ore_cfg: Ore, trestle_cfg: Trestle) -> dict:
    sim = world.copy()
    ore = sim.get("ore")
    trestle = sim.get("trestle")
    ore.meters["carried"] += 1
    trestle.meters["loaded"] += 1
    trestle.meters["wobble"] += trestle_cfg.wobble
    if severity(ore_cfg, trestle_cfg) >= 3:
        ore.meters["spilled"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": trestle.meters["wobble"],
        "spill": ore.meters["spilled"],
        "danger": sim.get("stairs").meters["danger"],
    }


def setup_story(world: World, seeker: Entity, helper: Entity, parent: Entity,
                ore_cfg: Ore, trestle_cfg: Trestle, destination: Destination,
                chant: str) -> None:
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After dinner, {seeker.id} and {helper.id} played on the basement stairs while "
        f"{parent.label_word} folded towels nearby. The stairs had that cool basement smell, "
        f"and the light over the landing made every dusty thing look a little mysterious."
    )
    world.say(
        f"They were on a quest to bring {ore_cfg.label} to {destination.phrase}. "
        f"{seeker.id} carried {ore_cfg.phrase}, and {helper.id} pointed the way."
    )
    world.say(
        f"Across the bottom steps they had built {trestle_cfg.phrase}. It {trestle_cfg.shape}."
    )
    world.say(
        f'"{chant}" they said together. "{chant}"'
    )


def sound_and_need(world: World, seeker: Entity, helper: Entity,
                   ore_cfg: Ore, trestle_cfg: Trestle, destination: Destination) -> None:
    world.say(
        f"When {seeker.id} lifted the cup, the pieces inside went {ore_cfg.clink}. "
        f"The sound made the quest feel real enough to hurry."
    )
    world.say(
        f"{helper.id} looked from the shiny pretend ore to {destination.label} and then back at "
        f"the bridge. The stairs were steep enough that even a game needed thinking."
    )
    world.say(
        f"Then the board answered with {trestle_cfg.sound}."
    )


def warning(world: World, seeker: Entity, helper: Entity, parent: Entity,
            ore_cfg: Ore, trestle_cfg: Trestle, chant: str) -> None:
    pred = predict_crossing(world, ore_cfg, trestle_cfg)
    helper.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_spill"] = pred["spill"]
    world.say(
        f'{helper.id} held up a hand. "{seeker.id}, wait," {helper.pronoun()} said. '
        f'"That fake trestle is on the stairs, and it sounds wobbly."'
    )
    if pred["spill"] >= THRESHOLD:
        world.say(
            f'{helper.id} listened again and added, "If you carry all that ore over it, it could tip and spill."'
        )
    else:
        world.say(
            f'{helper.id} listened again and added, "If you rush, your cup could still bump and wobble."'
        )
    world.say(
        f'{parent.label_word.capitalize()} looked over from the towels but let them think for one more beat.'
    )
    world.say(
        f'The chant came back smaller this time. "{chant}" {seeker.id} whispered, but not as loudly.'
    )


def back_down(world: World, seeker: Entity, helper: Entity, parent: Entity,
              plan: Plan, destination: Destination) -> None:
    seeker.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{seeker.id} looked at the stairs, then at {helper.id}, and let out the breath "
        f"{seeker.pronoun()} had been holding. The quest suddenly felt more important than hurrying."
    )
    world.say(
        f'"Okay," {seeker.pronoun()} said. "A real miner would fix the path first."'
    )
    world.say(
        f"{parent.label_word.capitalize()} smiled and {plan.text}."
    )
    world.say(
        f"{plan.end_image} Soon {destination.ending}."
    )


def step_and_wobble(world: World, seeker: Entity, helper: Entity,
                    ore_cfg: Ore, trestle_cfg: Trestle) -> None:
    ore = world.get("ore")
    trestle = world.get("trestle")
    ore.meters["carried"] += 1
    trestle.meters["loaded"] += 1
    trestle.meters["wobble"] += trestle_cfg.wobble
    propagate(world, narrate=False)
    world.say(
        f"{seeker.id} set one foot onto the board. {ore_cfg.clink}. {trestle_cfg.sound}. "
        f"The whole fake trestle gave a tiny shiver."
    )
    if severity(ore_cfg, trestle_cfg) >= 3:
        ore.meters["spilled"] += 1
        propagate(world, narrate=False)
        world.say(
            f"One piece of ore hopped out and went tink-tink-tink down two steps. "
            f"Nobody fell, but everybody froze."
        )
    else:
        world.say(
            f"{helper.id} grabbed the cup before it tipped. Nobody fell, but the wobble said enough."
        )


def calm_fix(world: World, seeker: Entity, helper: Entity, parent: Entity,
             plan: Plan, destination: Destination) -> None:
    seeker.memes["relief"] += 1
    helper.memes["relief"] += 1
    seeker.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came over right away, not angry, just brisk and calm. "
        f'"Basement stairs are for careful feet," {parent.pronoun()} said. "A fake trestle belongs in a safer spot."'
    )
    world.say(
        f"Then {parent.pronoun()} {plan.text}."
    )
    world.say(
        f'Soon the chant was back at a better speed. "Ore for the tunnel, ore for the tunnel," '
        f"the children said, this time in slow happy voices."
    )
    world.say(
        f"{plan.end_image} At last {destination.ending}."
    )


def tell(ore_cfg: Ore, trestle_cfg: Trestle, plan: Plan, destination: Destination,
         seeker_name: str = "Ben", seeker_gender: str = "boy",
         helper_name: str = "Lily", helper_gender: str = "girl",
         parent_type: str = "mother", trait: str = "careful",
         relation: str = "siblings", seeker_age: int = 5, helper_age: int = 6,
         chant: str = "Ore for the tunnel!") -> World:
    world = World()
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_gender,
        label=seeker_name,
        role="seeker",
        age=seeker_age,
        attrs={"relation": relation},
        traits=["eager"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        age=helper_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(id="stairs", type="stairs", label="basement stairs"))
    ore = world.add(Entity(id="ore", type="ore", label=ore_cfg.label, phrase=ore_cfg.phrase, tags=set(ore_cfg.tags)))
    trestle = world.add(Entity(id="trestle", type="trestle", label=trestle_cfg.label, phrase=trestle_cfg.phrase, tags=set(trestle_cfg.tags)))
    world.facts["chant"] = chant

    setup_story(world, seeker, helper, parent, ore_cfg, trestle_cfg, destination, chant)
    world.para()
    sound_and_need(world, seeker, helper, ore_cfg, trestle_cfg, destination)
    warning(world, seeker, helper, parent, ore_cfg, trestle_cfg, chant)

    averted = would_avert(relation, seeker_age, helper_age, trait)
    world.para()
    if averted:
        back_down(world, seeker, helper, parent, plan, destination)
        outcome = "averted"
    else:
        step_and_wobble(world, seeker, helper, ore_cfg, trestle_cfg)
        calm_fix(world, seeker, helper, parent, plan, destination)
        outcome = "rerouted"

    world.facts.update(
        seeker=seeker,
        helper=helper,
        parent=parent,
        ore_cfg=ore_cfg,
        trestle_cfg=trestle_cfg,
        plan=plan,
        destination=destination,
        relation=relation,
        outcome=outcome,
        averted=averted,
        spilled=ore.meters["spilled"] >= THRESHOLD,
        danger=world.get("stairs").meters["danger"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    destination = f["destination"]
    plan = f["plan"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old set on basement stairs. Include the words "ore", "trestle", and "fake".',
        f"Tell a homey quest story where {seeker.id} and {helper.id} carry pretend ore across a fake trestle toward {destination.label}, but a safer plan changes the game.",
        f"Write a gentle story with repetition and sound effects on basement stairs, ending when a grown-up {plan.qa_text}.",
    ]


KNOWLEDGE = {
    "ore": [(
        "What is ore?",
        "Ore is rock that has useful metal inside it. In a pretend game, children might call any shiny or heavy little stones ore."
    )],
    "trestle": [(
        "What is a trestle?",
        "A trestle is a support structure that holds something up, like a small bridge or track. A fake trestle in a game only pretends to be strong."
    )],
    "fake": [(
        "What does fake mean?",
        "Fake means something is pretend and not the real thing. A fake bridge in a game should never be trusted like a real bridge."
    )],
    "stairs": [(
        "Why do people need to be careful on stairs?",
        "Stairs have edges and height changes, so a slip or wobble can make someone fall. Slow feet and a free hand help keep people safe."
    )],
    "handrail": [(
        "What is a handrail for?",
        "A handrail gives your hand something firm to hold while you go up or down stairs. It helps your body stay balanced."
    )],
    "small_load": [(
        "Why is a smaller load easier to carry safely?",
        "A smaller load is lighter and easier to keep steady. When your hands and feet are not struggling, you are less likely to spill or trip."
    )],
    "safe_floor": [(
        "Why is a flat floor safer than stairs for a pretend bridge?",
        "A flat floor does not have step edges under you, so it is steadier for play. If something tips, it is much less likely to send anyone tumbling."
    )],
}

KNOWLEDGE_ORDER = ["ore", "trestle", "fake", "stairs", "handrail", "small_load", "safe_floor"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    parent = f["parent"]
    ore_cfg = f["ore_cfg"]
    trestle_cfg = f["trestle_cfg"]
    plan = f["plan"]
    destination = f["destination"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id} and {helper.id}, two children on the basement stairs, and their {parent.label_word} nearby. They turn an ordinary part of the house into a little quest."
        ),
        (
            "What was their quest?",
            f"They wanted to carry pretend ore to {destination.phrase}. The quest made the basement stairs feel like part of a mine."
        ),
        (
            "What had they built?",
            f"They had built {trestle_cfg.phrase} across the bottom steps. It was only pretend, so the story treats it as a game object and not a real safe bridge."
        ),
        (
            f"Why did {helper.id} tell {seeker.id} to wait?",
            f"{helper.id} heard the bridge answer with {trestle_cfg.sound} and understood that the fake trestle was wobbling. The warning came before anyone got hurt, because the stairs made even a small wobble matter."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What did {seeker.id} do after the warning?",
            f"{seeker.id} stopped before stepping onto the board and agreed to fix the path first. That changed the quest from a risky hurry into a safer game."
        ))
    else:
        if f["spilled"]:
            qa.append((
                "What happened when the child stepped onto the trestle?",
                f"The bridge gave a wobble and one piece of ore jumped out and bounced down the steps. Nobody fell, but the little spill proved the warning was right."
            ))
        else:
            qa.append((
                "What happened when the child stepped onto the trestle?",
                f"The bridge gave a wobble and the cup nearly tipped, so everyone froze. Nobody fell, but the sound and shake were enough to stop the rush."
            ))
    qa.append((
        f"How did the {parent.label_word} solve the problem?",
        f"The {parent.label_word} {plan.qa_text}. That let the children keep their quest while changing the dangerous part of the setup."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with the ore quest going on in a calmer, safer way. The final image proves the change because the game keeps going without trusting the fake trestle on the stairs."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ore", "trestle", "fake", "stairs"} | set(f["plan"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        ore="washer_ore",
        trestle="milk_crates",
        plan="handrail",
        destination="coal_bin",
        seeker="Ben",
        seeker_gender="boy",
        helper="Lily",
        helper_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        seeker_age=5,
        helper_age=7,
        chant="Ore for the tunnel, ore for the tunnel!",
    ),
    StoryParams(
        ore="river_ore",
        trestle="cardboard_boxes",
        plan="move_floor",
        destination="workbench",
        seeker="Mia",
        seeker_gender="girl",
        helper="Max",
        helper_gender="boy",
        parent="father",
        trait="curious",
        relation="friends",
        seeker_age=6,
        helper_age=6,
        chant="Clink and carry, clink and carry!",
    ),
    StoryParams(
        ore="river_ore",
        trestle="milk_crates",
        plan="small_pan",
        destination="paint_shelf",
        seeker="Theo",
        seeker_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        parent="mother",
        trait="steady",
        relation="siblings",
        seeker_age=6,
        helper_age=8,
        chant="Ore for the tunnel!",
    ),
    StoryParams(
        ore="brick_ore",
        trestle="laundry_basket",
        plan="move_floor",
        destination="coal_bin",
        seeker="Ava",
        seeker_gender="girl",
        helper="Finn",
        helper_gender="boy",
        parent="father",
        trait="sensible",
        relation="friends",
        seeker_age=5,
        helper_age=5,
        chant="Clink and carry, clink and carry!",
    ),
]


ASP_RULES = r"""
sensible_plan(P) :- plan(P), sense(P, S), sense_min(M), S >= M.
severity(O, T, V) :- ore(O), trestle(T), weight(O, W), wobble(T, B), V = W + B.
valid(O, T, P) :- ore(O), trestle(T), plan(P), sensible_plan(P),
                  severity(O, T, V), power(P, R), R >= V.

cautious_now(T) :- trait(T), is_cautious(T).
averted :- relation(siblings), helper_age(H), seeker_age(S), H > S, trait(T), cautious_now(T).
outcome(averted) :- averted.
outcome(rerouted) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ore_id, ore in ORES.items():
        lines.append(asp.fact("ore", ore_id))
        lines.append(asp.fact("weight", ore_id, ore.weight))
    for trestle_id, trestle in TRESTLES.items():
        lines.append(asp.fact("trestle", trestle_id))
        lines.append(asp.fact("wobble", trestle_id, trestle.wobble))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("power", plan_id, plan.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
        asp.fact("relation", params.relation),
        asp.fact("helper_age", params.helper_age),
        asp.fact("seeker_age", params.seeker_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.seeker_age, params.helper_age, params.trait) else "rerouted"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes on {len(bad)} scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        if not smoke.story_qa:
            raise StoryError("missing story QA in smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pretend ore quest on basement stairs with a fake trestle and a safer fix."
    )
    ap.add_argument("--ore", choices=ORES)
    ap.add_argument("--trestle", choices=TRESTLES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (ore, trestle, plan) set from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan is not None:
        chosen_plan = PLANS[args.plan]
        if chosen_plan.sense < SENSE_MIN:
            example_ore = ORES[args.ore] if args.ore else next(iter(ORES.values()))
            example_trestle = TRESTLES[args.trestle] if args.trestle else next(iter(TRESTLES.values()))
            raise StoryError(explain_rejection(chosen_plan, example_ore, example_trestle))

    if args.ore and args.trestle and args.plan:
        ore_cfg = ORES[args.ore]
        trestle_cfg = TRESTLES[args.trestle]
        plan_cfg = PLANS[args.plan]
        if not plan_works(ore_cfg, trestle_cfg, plan_cfg):
            raise StoryError(explain_rejection(plan_cfg, ore_cfg, trestle_cfg))

    combos = [
        combo for combo in valid_combos()
        if (args.ore is None or combo[0] == args.ore)
        and (args.trestle is None or combo[1] == args.trestle)
        and (args.plan is None or combo[2] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ore_id, trestle_id, plan_id = rng.choice(sorted(combos))
    destination = args.destination or rng.choice(sorted(DESTINATIONS))
    seeker, seeker_gender = pick_child(rng)
    helper, helper_gender = pick_child(rng, avoid=seeker)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    seeker_age, helper_age = rng.sample([4, 5, 6, 7, 8], 2)
    chant = rng.choice(CHANTS)
    return StoryParams(
        ore=ore_id,
        trestle=trestle_id,
        plan=plan_id,
        destination=destination,
        seeker=seeker,
        seeker_gender=seeker_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        seeker_age=seeker_age,
        helper_age=helper_age,
        chant=chant,
    )


def generate(params: StoryParams) -> StorySample:
    if params.ore not in ORES:
        raise StoryError(f"(Unknown ore: {params.ore})")
    if params.trestle not in TRESTLES:
        raise StoryError(f"(Unknown trestle: {params.trestle})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")

    ore_cfg = ORES[params.ore]
    trestle_cfg = TRESTLES[params.trestle]
    plan = PLANS[params.plan]
    destination = DESTINATIONS[params.destination]

    if not plan_works(ore_cfg, trestle_cfg, plan):
        raise StoryError(explain_rejection(plan, ore_cfg, trestle_cfg))

    world = tell(
        ore_cfg=ore_cfg,
        trestle_cfg=trestle_cfg,
        plan=plan,
        destination=destination,
        seeker_name=params.seeker,
        seeker_gender=params.seeker_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        seeker_age=params.seeker_age,
        helper_age=params.helper_age,
        chant=params.chant,
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
        print(f"{len(combos)} compatible (ore, trestle, plan) combos:\n")
        for ore_id, trestle_id, plan_id in combos:
            print(f"  {ore_id:12} {trestle_id:16} {plan_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.seeker} & {p.helper}: {p.ore} on {p.trestle} with {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
