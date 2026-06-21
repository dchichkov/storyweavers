#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dose_coupe_foreshadowing_happy_ending_detective_story.py

A small detective-story storyworld about a child sleuth solving the case of a
missing pet after a vet visit. The seed words "dose" and "coupe" are built into
the world: a careful dose of medicine makes the pet drowsy, and the old family
coupe becomes both the hiding place and the final answer. The opening plants a
real clue early, so the resolution feels earned rather than random.

Run it
------
python storyworlds/worlds/gpt-5.4/dose_coupe_foreshadowing_happy_ending_detective_story.py
python storyworlds/worlds/gpt-5.4/dose_coupe_foreshadowing_happy_ending_detective_story.py --pet kitten --hideout back_seat --clue paw_print
python storyworlds/worlds/gpt-5.4/dose_coupe_foreshadowing_happy_ending_detective_story.py --pet puppy --hideout basket
python storyworlds/worlds/gpt-5.4/dose_coupe_foreshadowing_happy_ending_detective_story.py --all --qa
python storyworlds/worlds/gpt-5.4/dose_coupe_foreshadowing_happy_ending_detective_story.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        animal = {"kitten", "cat", "puppy", "dog", "rabbit", "bunny"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class PetCfg:
    id: str
    label: str
    phrase: str
    type: str
    voice: str
    medicine: str
    fit: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SymptomCfg:
    id: str
    problem: str
    vet_line: str
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HideoutCfg:
    id: str
    label: str
    phrase: str
    inside_phrase: str
    cozy: str
    allowed_pets: set[str] = field(default_factory=set)
    clue_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ClueCfg:
    id: str
    label: str
    early_glimpse: str
    found_text: str
    inference: str
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


def _r_pet_hides(world: World) -> list[str]:
    out: list[str] = []
    pet = world.entities.get("pet")
    car = world.entities.get("car")
    if not pet or not car:
        return out
    if pet.meters["sleepy"] < THRESHOLD:
        return out
    if car.meters["door_ajar"] < THRESHOLD:
        return out
    hideout = pet.attrs.get("chosen_hideout")
    if not hideout:
        return out
    sig = ("hide", pet.id, hideout)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pet.meters["hidden"] += 1
    pet.attrs["location"] = hideout
    car.meters["occupied"] += 1
    clue_id = pet.attrs.get("chosen_clue")
    if clue_id:
        world.facts["active_clue"] = clue_id
    out.append("__hide__")
    return out


def _r_worry(world: World) -> list[str]:
    pet = world.entities.get("pet")
    child = world.entities.get("detective")
    helper = world.entities.get("helper")
    caregiver = world.entities.get("caregiver")
    if not pet or pet.meters["hidden"] < THRESHOLD:
        return []
    sig = ("worry", pet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in (child, helper, caregiver):
        if ent is not None:
            ent.memes["worry"] += 1
    return ["__worry__"]


def _r_found_relief(world: World) -> list[str]:
    pet = world.entities.get("pet")
    if not pet or pet.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", pet.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for name in ("detective", "helper", "caregiver"):
        ent = world.entities.get(name)
        if ent is not None:
            ent.memes["worry"] = 0.0
            ent.memes["relief"] += 1
            ent.memes["joy"] += 1
    pet.meters["hidden"] = 0.0
    pet.memes["safe"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="pet_hides", tag="physical", apply=_r_pet_hides),
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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


PETS = {
    "kitten": PetCfg(
        id="kitten",
        label="kitten",
        phrase="a striped kitten named Pip",
        type="kitten",
        voice="mew",
        medicine="sweet pink syrup",
        fit={"back_seat", "footwell", "basket"},
        tags={"pet", "kitten"},
    ),
    "puppy": PetCfg(
        id="puppy",
        label="puppy",
        phrase="a bouncy puppy named Dot",
        type="puppy",
        voice="woof",
        medicine="banana-flavored syrup",
        fit={"back_seat", "footwell"},
        tags={"pet", "puppy"},
    ),
    "rabbit": PetCfg(
        id="rabbit",
        label="rabbit",
        phrase="a soft rabbit named Clover",
        type="rabbit",
        voice="sniff",
        medicine="herb-smelling drops",
        fit={"back_seat", "basket"},
        tags={"pet", "rabbit"},
    ),
}

SYMPTOMS = {
    "sneeze": SymptomCfg(
        id="sneeze",
        problem="sneezing all morning",
        vet_line="The vet said one small dose would make the pet feel better and a little sleepy.",
        comfort_line="Sleep was part of the medicine working.",
        tags={"medicine"},
    ),
    "tummy": SymptomCfg(
        id="tummy",
        problem="a fluttery tummy",
        vet_line="The vet said one careful dose would settle the pet's tummy and leave it drowsy for a while.",
        comfort_line="A quiet rest would help the medicine do its job.",
        tags={"medicine"},
    ),
    "paw": SymptomCfg(
        id="paw",
        problem="a sore paw",
        vet_line="The vet said one measured dose would ease the ache and make the pet want a nap.",
        comfort_line="The pet mostly needed rest after the medicine.",
        tags={"medicine"},
    ),
}

HIDEOUTS = {
    "back_seat": HideoutCfg(
        id="back_seat",
        label="back seat",
        phrase="the back seat under a little blanket",
        inside_phrase="on the back seat of the coupe",
        cozy="The back seat was soft and dim, a perfect little cave for a sleepy pet.",
        allowed_pets={"kitten", "puppy", "rabbit"},
        clue_ids={"paw_print", "blanket_fold", "bell_jingle"},
        tags={"coupe", "hideout"},
    ),
    "footwell": HideoutCfg(
        id="footwell",
        label="front footwell",
        phrase="the front footwell beside the seat",
        inside_phrase="curled in the front footwell of the coupe",
        cozy="The floor mat felt dark and tucked away, just right for a nervous, sleepy pet.",
        allowed_pets={"kitten", "puppy"},
        clue_ids={"paw_print", "bell_jingle"},
        tags={"coupe", "hideout"},
    ),
    "basket": HideoutCfg(
        id="basket",
        label="picnic basket",
        phrase="the picnic basket on the back seat",
        inside_phrase="inside the picnic basket in the coupe",
        cozy="The basket smelled like straw and cloth, cozy enough for a pet that wanted to disappear and sleep.",
        allowed_pets={"kitten", "rabbit"},
        clue_ids={"fur_tuft", "blanket_fold"},
        tags={"coupe", "hideout"},
    ),
}

CLUES = {
    "paw_print": ClueCfg(
        id="paw_print",
        label="a dusty paw print",
        early_glimpse="On the shiny step below the coupe door, there was a dusty paw print that looked almost like a tiny stamp.",
        found_text="Then {detective} spotted a dusty paw print on the shiny step below the coupe door.",
        inference="A paw print on the car meant the pet had climbed toward the coupe, not away from it.",
        tags={"clue", "tracks"},
    ),
    "bell_jingle": ClueCfg(
        id="bell_jingle",
        label="a faint bell jingle",
        early_glimpse="When the wind stirred, a very faint bell jingle came from the coupe, so soft that it could almost be missed.",
        found_text="Just when everything went quiet, {helper} heard a faint bell jingle from the coupe.",
        inference="Only the pet wore that little bell, so the sound pointed straight to the car.",
        tags={"clue", "sound"},
    ),
    "blanket_fold": ClueCfg(
        id="blanket_fold",
        label="a blanket corner sticking out",
        early_glimpse="A blanket corner poked from the half-open coupe door, as if someone small had nosed it there.",
        found_text="By the coupe, {detective} noticed a blanket corner sticking from the half-open door.",
        inference="A moved blanket suggested something small had wriggled underneath to make a nest.",
        tags={"clue", "blanket"},
    ),
    "fur_tuft": ClueCfg(
        id="fur_tuft",
        label="a soft tuft of fur",
        early_glimpse="Caught on the coupe seat belt was a soft tuft of fur, bright in the afternoon light.",
        found_text="Near the coupe, {helper} found a soft tuft of fur caught on the seat belt.",
        inference="That tuft of fur showed the pet had brushed past the seat and hidden somewhere inside the car.",
        tags={"clue", "fur"},
    ),
}


def pet_can_hide(pet_id: str, hideout_id: str) -> bool:
    pet = PETS[pet_id]
    hideout = HIDEOUTS[hideout_id]
    return hideout_id in pet.fit and pet_id in hideout.allowed_pets


def clue_fits(hideout_id: str, clue_id: str) -> bool:
    return clue_id in HIDEOUTS[hideout_id].clue_ids


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pet_id in PETS:
        for hideout_id in HIDEOUTS:
            if not pet_can_hide(pet_id, hideout_id):
                continue
            for clue_id in CLUES:
                if clue_fits(hideout_id, clue_id):
                    combos.append((pet_id, hideout_id, clue_id))
    return sorted(combos)


@dataclass
class StoryParams:
    pet: str
    symptom: str
    hideout: str
    clue: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    caregiver: str
    vehicle_color: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lila", "Nora", "Mina", "Ada", "Ruby", "June", "Tess", "Maya"]
BOY_NAMES = ["Owen", "Milo", "Ben", "Theo", "Eli", "Finn", "Sam", "Leo"]
CAR_COLORS = ["blue", "red", "green", "cream"]
CAREGIVERS = ["mother", "father"]

CURATED = [
    StoryParams(
        pet="kitten",
        symptom="sneeze",
        hideout="back_seat",
        clue="paw_print",
        detective="Lila",
        detective_gender="girl",
        helper="Ben",
        helper_gender="boy",
        caregiver="mother",
        vehicle_color="blue",
        seed=101,
    ),
    StoryParams(
        pet="puppy",
        symptom="paw",
        hideout="footwell",
        clue="bell_jingle",
        detective="Theo",
        detective_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        caregiver="father",
        vehicle_color="red",
        seed=102,
    ),
    StoryParams(
        pet="rabbit",
        symptom="tummy",
        hideout="basket",
        clue="fur_tuft",
        detective="Mina",
        detective_gender="girl",
        helper="Owen",
        helper_gender="boy",
        caregiver="mother",
        vehicle_color="cream",
        seed=103,
    ),
    StoryParams(
        pet="kitten",
        symptom="paw",
        hideout="basket",
        clue="blanket_fold",
        detective="Finn",
        detective_gender="boy",
        helper="June",
        helper_gender="girl",
        caregiver="father",
        vehicle_color="green",
        seed=104,
    ),
]


def explain_rejection(pet_id: str, hideout_id: str, clue_id: Optional[str] = None) -> str:
    if not pet_can_hide(pet_id, hideout_id):
        pet = PETS[pet_id]
        hideout = HIDEOUTS[hideout_id]
        return (
            f"(No story: a {pet.label} would not reasonably hide in {hideout.phrase}. "
            f"Pick a hideout that fits the pet and feels cozy enough for a sleepy animal.)"
        )
    if clue_id is not None and not clue_fits(hideout_id, clue_id):
        clue = CLUES[clue_id]
        hideout = HIDEOUTS[hideout_id]
        return (
            f"(No story: {clue.label} does not naturally lead to {hideout.label}. "
            f"Choose a clue that could honestly come from that hiding place.)"
        )
    return "(No story: the requested combination is not reasonable.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def predict_case(world: World) -> dict:
    sim = world.copy()
    pet = sim.get("pet")
    pet.meters["sleepy"] += 1
    propagate(sim, narrate=False)
    return {
        "hidden": pet.meters["hidden"] >= THRESHOLD,
        "location": pet.attrs.get("location", ""),
        "clue": sim.facts.get("active_clue", ""),
    }


def setup_scene(world: World, detective: Entity, helper: Entity, caregiver: Entity,
                pet: Entity, symptom: SymptomCfg) -> None:
    car = world.get("car")
    world.say(
        f"After lunch, {detective.id} decided the day felt perfect for detective work. "
        f"{caregiver.label_word.capitalize()}'s old {car.attrs['color']} coupe had just rolled back from the vet, "
        f"and {pet.id}, {pet.phrase}, had been {symptom.problem}."
    )
    world.say(symptom.vet_line)
    if world.facts.get("foreshadow"):
        world.say(world.facts["foreshadow"])


def give_dose(world: World, caregiver: Entity, pet: Entity, symptom: SymptomCfg, pet_cfg: PetCfg) -> None:
    pet.meters["dosed"] += 1
    pet.meters["sleepy"] += 1
    pet.memes["trust"] += 1
    world.say(
        f"{caregiver.label_word.capitalize()} measured one careful dose of {pet_cfg.medicine} "
        f"and tipped it into {pet.id}'s mouth. {pet.id.capitalize()} made a tiny {pet_cfg.voice} and blinked slowly."
    )
    world.say(symptom.comfort_line)
    propagate(world, narrate=False)


def missing_pet(world: World, detective: Entity, helper: Entity, pet: Entity) -> None:
    pet.meters["missing"] += 1
    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"A little later, the house grew too quiet. {pet.id.capitalize()} was gone from the rug by the window."
    )
    world.say(
        f'"Case of the Missing {pet.label.capitalize()}," {detective.id} whispered. '
        f'{helper.id} nodded at once and followed close behind.'
    )
    propagate(world, narrate=False)


def search_wrong_places(world: World, detective: Entity, helper: Entity, pet: Entity) -> None:
    detective.meters["searched"] += 1
    helper.meters["searched"] += 1
    world.say(
        f"They checked under the table, behind the curtain, and in the laundry basket, but there was no sleepy {pet.label} there."
    )
    if world.get("detective").memes["worry"] >= THRESHOLD:
        world.say(
            f"{helper.id} squeezed {detective.id}'s hand. Even brave detectives can feel worried during a hard case."
        )


def inspect_clue(world: World, detective: Entity, helper: Entity, clue: ClueCfg) -> None:
    detective.meters["insight"] += 1
    helper.meters["insight"] += 1
    world.facts["clue_found"] = True
    text = clue.found_text.format(detective=detective.id, helper=helper.id)
    world.say(text)
    world.say(clue.inference)


def solve_case(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["confidence"] += 1
    helper.memes["confidence"] += 1
    world.say(
        f'"The clue was waving at us from the very start," {detective.id} said. '
        f'"We need to check the coupe."'
    )


def find_pet(world: World, caregiver: Entity, pet: Entity, hideout: HideoutCfg) -> None:
    pet.meters["found"] += 1
    pet.attrs["location"] = hideout.id
    world.say(
        f"{caregiver.label_word.capitalize()} opened the coupe door gently, and there was {pet.id}, {hideout.inside_phrase}, fast asleep."
    )
    world.say(hideout.cozy)
    propagate(world, narrate=False)


def happy_ending(world: World, detective: Entity, helper: Entity, caregiver: Entity,
                 pet: Entity) -> None:
    pet.memes["love"] += 1
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{pet.id.capitalize()} woke, stretched, and blinked at the three detectives as if the whole mystery had only been a nap."
    )
    world.say(
        f'{caregiver.label_word.capitalize()} laughed with relief. "Good spotting," {caregiver.pronoun()} said. '
        f'"The medicine worked, and so did your careful noticing."'
    )
    world.say(
        f"{detective.id} rubbed {pet.id}'s head, {helper.id} brought a bowl of water, "
        f"and the case was closed with everyone safe, smiling, and together again."
    )


def tell(params: StoryParams) -> World:
    if params.pet not in PETS:
        raise StoryError(f"(Unknown pet '{params.pet}'.)")
    if params.symptom not in SYMPTOMS:
        raise StoryError(f"(Unknown symptom '{params.symptom}'.)")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout '{params.hideout}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue '{params.clue}'.)")
    if not pet_can_hide(params.pet, params.hideout):
        raise StoryError(explain_rejection(params.pet, params.hideout))
    if not clue_fits(params.hideout, params.clue):
        raise StoryError(explain_rejection(params.pet, params.hideout, params.clue))

    pet_cfg = PETS[params.pet]
    symptom = SYMPTOMS[params.symptom]
    hideout = HIDEOUTS[params.hideout]
    clue = CLUES[params.clue]

    world = World()
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=params.detective_gender,
        label=params.detective,
        phrase=params.detective,
        role="detective",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_gender,
        label=params.helper,
        phrase=params.helper,
        role="helper",
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=params.caregiver,
        label="the parent",
        phrase="the parent",
        role="caregiver",
    ))
    pet = world.add(Entity(
        id="pet",
        kind="thing",
        type=pet_cfg.type,
        label=pet_cfg.label,
        phrase=pet_cfg.phrase,
        role="pet",
        tags=set(pet_cfg.tags),
        attrs={"chosen_hideout": hideout.id, "chosen_clue": clue.id, "location": "rug"},
    ))
    car = world.add(Entity(
        id="car",
        kind="thing",
        type="car",
        label="coupe",
        phrase=f"the old {params.vehicle_color} coupe",
        role="vehicle",
        attrs={"color": params.vehicle_color},
    ))
    car.meters["door_ajar"] = 1.0

    detective.id = params.detective
    helper.id = params.helper
    pet.id = pet_cfg.label.capitalize() if pet_cfg.id == "rabbit" else pet_cfg.label.capitalize()
    caregiver.id = caregiver.label_word.capitalize()

    world.facts["foreshadow"] = clue.early_glimpse
    world.facts["pet_cfg"] = pet_cfg
    world.facts["symptom_cfg"] = symptom
    world.facts["hideout_cfg"] = hideout
    world.facts["clue_cfg"] = clue
    world.facts["detective_name"] = detective.id
    world.facts["helper_name"] = helper.id
    world.facts["caregiver_word"] = caregiver.label_word
    world.facts["car_phrase"] = car.phrase

    setup_scene(world, detective, helper, caregiver, pet, symptom)
    world.para()
    give_dose(world, caregiver, pet, symptom, pet_cfg)
    missing_pet(world, detective, helper, pet)
    world.para()
    search_wrong_places(world, detective, helper, pet)
    inspect_clue(world, detective, helper, clue)
    solve_case(world, detective, helper)
    world.para()
    find_pet(world, caregiver, pet, hideout)
    happy_ending(world, detective, helper, caregiver, pet)

    world.facts.update(
        detective=detective,
        helper=helper,
        caregiver=caregiver,
        pet=pet,
        car=car,
        found=pet.meters["found"] >= THRESHOLD,
        hideout=hideout,
        clue=clue,
        symptom=symptom,
    )
    return world


KNOWLEDGE = {
    "medicine": [
        (
            "What is a dose of medicine?",
            "A dose is the right amount of medicine to take at one time. Grown-ups measure it carefully so it helps and stays safe."
        )
    ],
    "coupe": [
        (
            "What is a coupe?",
            "A coupe is a small car with a fixed roof. Some families have an old coupe that feels cozy inside."
        )
    ],
    "tracks": [
        (
            "Why are paw prints useful clues?",
            "Paw prints can show where an animal walked. A detective follows them because tracks connect a creature to a place."
        )
    ],
    "sound": [
        (
            "Why can a small sound be a clue?",
            "A tiny sound can tell you something is nearby even when you cannot see it. Good detectives listen as carefully as they look."
        )
    ],
    "blanket": [
        (
            "Why might an animal hide under a blanket?",
            "A blanket feels warm, dark, and snug. A sleepy or worried animal often chooses a place like that to rest."
        )
    ],
    "fur": [
        (
            "What can a tuft of fur tell you?",
            "A tuft of fur shows that an animal brushed past something. It is a clue that the animal was there recently."
        )
    ],
    "pet": [
        (
            "Why do pets sometimes hide after medicine or a vet visit?",
            "Pets can feel sleepy or unsure after medicine or a noisy trip. They often look for a quiet, cozy place to rest."
        )
    ],
}
KNOWLEDGE_ORDER = ["medicine", "coupe", "tracks", "sound", "blanket", "fur", "pet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    pet_cfg = f["pet_cfg"]
    clue = f["clue_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the words "dose" and "coupe".',
        f"Tell a child-friendly mystery where a young detective notices {clue.label} and uses it to find a missing {pet_cfg.label}.",
        f"Write a foreshadowing story with a happy ending in which a pet disappears after a careful dose of medicine and is found safe in a coupe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    caregiver = f["caregiver"]
    pet = f["pet"]
    hideout = f["hideout"]
    clue = f["clue"]
    symptom = f["symptom"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, {helper.id}, a helpful partner, and {pet.id}, the missing pet they wanted to find."
        ),
        (
            f"Why had {pet.id} been given a dose of medicine?",
            f"{pet.id} had been {symptom.problem}, so the vet told the family to give one careful dose of medicine. The medicine was meant to help, but it also made {pet.pronoun('object')} sleepy."
        ),
        (
            f"Why did everyone think {pet.id} was missing?",
            f"{pet.id} had been resting on the rug, and then suddenly {pet.pronoun()} was gone. Because the house had grown quiet and the sleepy pet could not be seen anywhere, the children knew they had a real case to solve."
        ),
        (
            "What clue solved the mystery?",
            f"The clue was {clue.label}. It mattered because {clue.inference[0].lower()}{clue.inference[1:]}"
        ),
        (
            f"Where did they finally find {pet.id}?",
            f"They found {pet.id} {hideout.inside_phrase}. {hideout.cozy}"
        ),
        (
            "How was the ending happy?",
            f"The pet was not lost or hurt at all, only sleepy and hidden. In the end, everyone felt relieved because the medicine had helped and the detectives had brought the whole family back together."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"medicine", "coupe", "pet"}
    clue = world.facts["clue"]
    tags |= set(clue.tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(P, H) :- pet_fit(P, H), hideout_allows(H, P).
supports(H, C) :- hideout_clue(H, C).
valid(P, H, C) :- pet(P), hideout(H), clue(C), fits(P, H), supports(H, C).

sleepy_after_dose.
door_ajar.
hidden(H) :- chosen_hideout(H), sleepy_after_dose, door_ajar.
found :- hidden(H), chosen_clue(C), supports(H, C).
outcome(happy) :- found.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pet_id, pet in PETS.items():
        lines.append(asp.fact("pet", pet_id))
        for fit in sorted(pet.fit):
            lines.append(asp.fact("pet_fit", pet_id, fit))
    for hideout_id, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hideout_id))
        for pet_id in sorted(hideout.allowed_pets):
            lines.append(asp.fact("hideout_allows", hideout_id, pet_id))
        for clue_id in sorted(hideout.clue_ids):
            lines.append(asp.fact("hideout_clue", hideout_id, clue_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
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
        asp.fact("chosen_hideout", params.hideout),
        asp.fact("chosen_clue", params.clue),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    for params in CURATED:
        outcome = asp_outcome(params)
        if outcome != "happy":
            rc = 1
            print(f"MISMATCH: expected happy outcome for curated params, got {outcome}: {params}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        with io.StringIO() as _buf:
            old_stdout = sys.stdout
            try:
                sys.stdout = _buf
                emit(sample, trace=False, qa=False, header="")
            finally:
                sys.stdout = old_stdout
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    else:
        print("OK: smoke test generate()/emit() passed.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective storyworld: a careful dose, a missing pet, a clue, and a coupe."
    )
    ap.add_argument("--pet", choices=sorted(PETS))
    ap.add_argument("--symptom", choices=sorted(SYMPTOMS))
    ap.add_argument("--hideout", choices=sorted(HIDEOUTS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--caregiver", choices=sorted(CAREGIVERS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (pet, hideout, clue) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pet and args.hideout and not pet_can_hide(args.pet, args.hideout):
        raise StoryError(explain_rejection(args.pet, args.hideout))
    if args.hideout and args.clue and not clue_fits(args.hideout, args.clue):
        pet_id = args.pet or "kitten"
        raise StoryError(explain_rejection(pet_id, args.hideout, args.clue))

    combos = [
        combo for combo in valid_combos()
        if (args.pet is None or combo[0] == args.pet)
        and (args.hideout is None or combo[1] == args.hideout)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    pet_id, hideout_id, clue_id = rng.choice(combos)
    symptom_id = args.symptom or rng.choice(sorted(SYMPTOMS))
    caregiver = args.caregiver or rng.choice(sorted(CAREGIVERS))
    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    detective = _pick_name(rng, detective_gender)
    helper = _pick_name(rng, helper_gender, avoid=detective)
    vehicle_color = rng.choice(CAR_COLORS)
    return StoryParams(
        pet=pet_id,
        symptom=symptom_id,
        hideout=hideout_id,
        clue=clue_id,
        detective=detective,
        detective_gender=detective_gender,
        helper=helper,
        helper_gender=helper_gender,
        caregiver=caregiver,
        vehicle_color=vehicle_color,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(f"{len(combos)} compatible (pet, hideout, clue) combos:\n")
        for pet_id, hideout_id, clue_id in combos:
            print(f"  {pet_id:7} {hideout_id:10} {clue_id}")
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
            header = f"### {p.detective}: {p.pet} in {p.hideout} ({p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
