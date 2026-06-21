#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/kayak_veterinarian_rhyme_suspense_nursery_rhyme.py
=============================================================================

A standalone storyworld for a tiny child-facing domain:

A child in a little kayak hears a worried animal cry across the water. The
animal is in trouble near the reeds. The child must stay calm, use the right
safe helper gear, and get the animal to a veterinarian. The tale is rendered in
a gentle nursery-rhyme voice with a suspenseful middle and a clear ending image
that proves what changed.

The world model prefers a small set of plausible rescue patterns over broad
coverage. Every generated story includes the words "kayak" and "veterinarian".

Run it
------
    python storyworlds/worlds/gpt-5.4/kayak_veterinarian_rhyme_suspense_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/kayak_veterinarian_rhyme_suspense_nursery_rhyme.py --animal duckling --trouble line
    python storyworlds/worlds/gpt-5.4/kayak_veterinarian_rhyme_suspense_nursery_rhyme.py --response splash_chase
    python storyworlds/worlds/gpt-5.4/kayak_veterinarian_rhyme_suspense_nursery_rhyme.py --all --qa
    python storyworlds/worlds/gpt-5.4/kayak_veterinarian_rhyme_suspense_nursery_rhyme.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    can_swim: bool = False
    can_fly: bool = False
    small: bool = False
    # shared physical / emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "veterinarian_female"}
        male = {"boy", "father", "man", "veterinarian_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "veterinarian_female": "veterinarian",
            "veterinarian_male": "veterinarian",
        }.get(self.type, self.label or self.type)


@dataclass
class Setting:
    id: str
    water: str
    launch: str
    reeds: str
    bank: str
    sky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnimalCfg:
    id: str
    label: str
    phrase: str
    call: str
    home: str
    can_swim: bool
    can_fly: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class TroubleCfg:
    id: str
    label: str
    danger_line: str
    sight_line: str
    hurts: str
    needs_vet: bool = True
    water_only: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class GearCfg:
    id: str
    label: str
    phrase: str
    use_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ResponseCfg:
    id: str
    label: str
    sense: int
    calm: bool
    uses_gear: bool
    success_line: str
    fail_line: str
    qa_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_tension(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    pond = world.get("pond")
    if animal.meters["stuck"] < THRESHOLD:
        return []
    sig = ("tension", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["fear"] += 1
    child.memes["worry"] += 1
    pond.meters["risk"] += 1
    return ["__tension__"]


def _r_relief(world: World) -> list[str]:
    animal = world.get("animal")
    child = world.get("child")
    if animal.meters["freed"] < THRESHOLD and animal.meters["treated"] < THRESHOLD:
        return []
    sig = ("relief", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.memes["calm"] += 1
    child.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="tension", tag="emotion", apply=_r_tension),
    Rule(name="relief", tag="emotion", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for item in produced:
            if not item.startswith("__"):
                world.say(item)
    return produced


def problem_requires_water(trouble: TroubleCfg) -> bool:
    return trouble.water_only


def sensible_responses() -> list[ResponseCfg]:
    return [cfg for cfg in RESPONSES.values() if cfg.sense >= SENSE_MIN]


def valid_combo(animal: AnimalCfg, trouble: TroubleCfg, gear: GearCfg, response: ResponseCfg) -> bool:
    if not problem_requires_water(trouble):
        return False
    if not trouble.needs_vet:
        return False
    if response.sense < SENSE_MIN:
        return False
    if response.uses_gear and gear.id == "bare_hands":
        return False
    if animal.id == "froglet" and trouble.id == "hook":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for aid, animal in ANIMALS.items():
        for tid, trouble in TROUBLES.items():
            for gid, gear in GEARS.items():
                for rid, response in RESPONSES.items():
                    if valid_combo(animal, trouble, gear, response):
                        combos.append((aid, tid, gid, rid))
    return combos


def explain_rejection(animal: AnimalCfg, trouble: TroubleCfg, gear: GearCfg, response: ResponseCfg) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it is too wild for a child rescue "
            f"(sense={response.sense} < {SENSE_MIN}). Calm help works better here.)"
        )
    if response.uses_gear and gear.id == "bare_hands":
        return (
            "(No story: this rescue method needs a safe helper tool, not bare hands. "
            "Choose a towel or a basket.)"
        )
    if animal.id == "froglet" and trouble.id == "hook":
        return (
            "(No story: a fishhook rescue for a tiny froglet is not a good fit here. "
            "Pick line or reeds, or choose another animal.)"
        )
    return "(No valid combination matches the given options.)"


def predict_rescue(world: World, response: ResponseCfg) -> dict:
    sim = world.copy()
    animal = sim.get("animal")
    if response.calm:
        animal.meters["freed"] += 1
        animal.meters["treated"] += 1
    else:
        animal.meters["panic"] += 1
        animal.meters["drifting"] += 1
    propagate(sim, narrate=False)
    return {
        "freed": animal.meters["freed"] >= THRESHOLD,
        "treated": animal.meters["treated"] >= THRESHOLD,
        "panic": animal.meters["panic"],
    }


def introduce(world: World, child: Entity, parent: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"In {setting.sky}, by {setting.water}, went {child.id} one day, "
        f"in a little red kayak with a soft-swish sway."
    )
    world.say(
        f"{parent.label_word.capitalize()} rowed near {setting.launch}, not far away, "
        f"while ripples made silver loops where the bright minnows play."
    )


def notice(world: World, child: Entity, animal: Entity, animal_cfg: AnimalCfg, trouble: TroubleCfg, setting: Setting) -> None:
    world.say(
        f"Then out by {setting.reeds} came a {animal_cfg.call}, thin and small—"
        f"\"{animal_cfg.call}! {animal_cfg.call}!\" through the hush of it all."
    )
    animal.meters["stuck"] += 1
    animal.meters["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} looked left, then right, with a blink and a shake. "
        f"There, by the dark reeds, was {animal_cfg.phrase} caught in {trouble.label}."
    )


def worry(world: World, child: Entity, trouble: TroubleCfg) -> None:
    world.say(
        f"The water said hish, and the reeds said hush-hush. "
        f"{child.id}'s heart gave a quick little drum-drum rush."
    )
    world.say(
        f'"Oh dear," said {child.id}, "that poor one looks sore. '
        f'{trouble.hurts.capitalize()}, and it may hurt more."'
    )


def choose_gear(world: World, parent: Entity, gear: GearCfg, response: ResponseCfg) -> None:
    if response.uses_gear:
        world.say(
            f"{parent.label_word.capitalize()} did not splash, did not shout, did not flare. "
            f"{parent.pronoun().capitalize()} reached for {gear.phrase} with sensible care."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} kept the kayak still in the breeze. "
            f"{parent.pronoun().capitalize()} spoke in a whisper that settled the trees."
        )


def warn_prediction(world: World, child: Entity, parent: Entity, response: ResponseCfg) -> None:
    pred = predict_rescue(world, response)
    world.facts["predicted_panic"] = pred["panic"]
    if pred["freed"]:
        world.say(
            f'"Slow and low is the way we should go," said {parent.label_word}. '
            f'"A calm little rescue gives frightened hearts room."'
        )
    else:
        world.say(
            f'"Fast splashes would frighten it more," said {parent.label_word}. '
            f'"A wild little rush could turn trouble to gloom."'
        )
    child.memes["care"] += 1


def rescue(world: World, child: Entity, parent: Entity, veterinarian: Entity,
           animal: Entity, animal_cfg: AnimalCfg, trouble: TroubleCfg,
           gear: GearCfg, response: ResponseCfg, setting: Setting) -> None:
    if response.calm:
        animal.meters["freed"] += 1
        animal.meters["treated"] += 1
        propagate(world, narrate=False)
        line = response.success_line.format(
            gear=gear.label,
            trouble=trouble.label,
            animal=animal_cfg.label,
            bank=setting.bank,
        )
        world.say(line)
        world.say(
            f"Wrapped snug and warm, with the kayak turned round, "
            f"they glided to {setting.bank} without a bumping sound."
        )
        world.say(
            f"There waited the veterinarian, steady and kind, "
            f"with gentle sure hands and a sharp, careful mind."
        )
        world.say(
            f'The veterinarian checked the little one over and said, '
            f'"The hurt is small now because help came ahead."'
        )
    else:
        animal.meters["panic"] += 1
        animal.meters["drifting"] += 1
        world.say(response.fail_line.format(animal=animal_cfg.label))
        world.say(
            f"The reeds shook harder, and the poor creature hid. "
            f"The more they chased after it, the worse the fright did."
        )


def release(world: World, child: Entity, animal_cfg: AnimalCfg, setting: Setting) -> None:
    world.say(
        f"Soon by {animal_cfg.home}, in the last honey light, "
        f"the small one gave one happy shake and tucked in for night."
    )
    world.say(
        f"{child.id} touched the side of the quiet old kayak and smiled. "
        f"What had begun with a tremble now ended soft and mild."
    )


def bad_end(world: World, child: Entity, parent: Entity, veterinarian: Entity,
            animal_cfg: AnimalCfg, setting: Setting) -> None:
    world.say(
        f"Back at {setting.launch}, they hurried to the veterinarian's door, "
        f"but the poor little {animal_cfg.label} had slipped from sight before."
    )
    world.say(
        f"{child.id} felt sad, and {parent.label_word} held {child.pronoun('object')} tight. "
        f"They learned that calm care matters most when hearts are full of fright."
    )


def tell(setting: Setting, animal_cfg: AnimalCfg, trouble: TroubleCfg,
         gear_cfg: GearCfg, response_cfg: ResponseCfg,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother", veterinarian_type: str = "veterinarian_female") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name, kind="character", type=child_gender, role="child", label=child_name
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent", label="the parent"
    ))
    veterinarian = world.add(Entity(
        id="Vet", kind="character", type=veterinarian_type, role="veterinarian", label="the veterinarian"
    ))
    pond = world.add(Entity(
        id="pond", kind="thing", type="water", label=setting.water, phrase=setting.water
    ))
    kayak = world.add(Entity(
        id="kayak", kind="thing", type="boat", label="kayak", phrase="little red kayak"
    ))
    animal = world.add(Entity(
        id="animal",
        kind="thing",
        type=animal_cfg.id,
        label=animal_cfg.label,
        phrase=animal_cfg.phrase,
        can_swim=animal_cfg.can_swim,
        can_fly=animal_cfg.can_fly,
        small=True,
        tags=set(animal_cfg.tags),
    ))
    gear = world.add(Entity(
        id="gear", kind="thing", type="gear", label=gear_cfg.label, phrase=gear_cfg.phrase, tags=set(gear_cfg.tags)
    ))

    introduce(world, child, parent, setting)
    notice(world, child, animal, animal_cfg, trouble, setting)

    world.para()
    worry(world, child, trouble)
    choose_gear(world, parent, gear_cfg, response_cfg)
    warn_prediction(world, child, parent, response_cfg)

    world.para()
    rescue(world, child, parent, veterinarian, animal, animal_cfg, trouble, gear_cfg, response_cfg, setting)

    world.para()
    if response_cfg.calm:
        release(world, child, animal_cfg, setting)
        outcome = "rescued"
    else:
        bad_end(world, child, parent, veterinarian, animal_cfg, setting)
        outcome = "lost"

    world.facts.update(
        child=child,
        parent=parent,
        veterinarian=veterinarian,
        pond=pond,
        kayak=kayak,
        animal=animal,
        animal_cfg=animal_cfg,
        trouble=trouble,
        gear_cfg=gear_cfg,
        gear=gear,
        response=response_cfg,
        setting=setting,
        outcome=outcome,
        treated=animal.meters["treated"] >= THRESHOLD,
        freed=animal.meters["freed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "pond": Setting(
        id="pond",
        water="the moon-bright pond",
        launch="the willow dock",
        reeds="the whispering reeds",
        bank="the pebbly bank",
        sky="a pearly afternoon",
        tags={"pond"},
    ),
    "lake": Setting(
        id="lake",
        water="the still blue lake",
        launch="the little wooden pier",
        reeds="the tall green rushes",
        bank="the sandy shore",
        sky="a breezy golden evening",
        tags={"lake"},
    ),
}

ANIMALS = {
    "duckling": AnimalCfg(
        id="duckling",
        label="duckling",
        phrase="a yellow duckling",
        call="peep",
        home="the cattail nook",
        can_swim=True,
        can_fly=False,
        tags={"duckling", "water_animal"},
    ),
    "otter_pup": AnimalCfg(
        id="otter_pup",
        label="otter pup",
        phrase="a brown otter pup",
        call="eep",
        home="the snug bank den",
        can_swim=True,
        can_fly=False,
        tags={"otter", "water_animal"},
    ),
    "froglet": AnimalCfg(
        id="froglet",
        label="froglet",
        phrase="a tiny froglet",
        call="pip",
        home="the lily-pad bend",
        can_swim=True,
        can_fly=False,
        tags={"frog", "water_animal"},
    ),
}

TROUBLES = {
    "line": TroubleCfg(
        id="line",
        label="a loop of fishing line",
        danger_line="The line could tighten if the little one kicked.",
        sight_line="A silver line gleamed in the weeds.",
        hurts="the line is pinching one leg",
        needs_vet=True,
        water_only=True,
        tags={"line", "tangle"},
    ),
    "reeds": TroubleCfg(
        id="reeds",
        label="a knot of scratchy reeds",
        danger_line="The reeds could twist tighter if the boat bumped in.",
        sight_line="The reeds had wrapped around one foot.",
        hurts="the reeds have twisted around one foot",
        needs_vet=True,
        water_only=True,
        tags={"reeds", "tangle"},
    ),
    "hook": TroubleCfg(
        id="hook",
        label="a bent fishhook and string",
        danger_line="The hook could tear if anyone pulled too fast.",
        sight_line="A small hook flashed near the creature's side.",
        hurts="a little hook is snagging its fur",
        needs_vet=True,
        water_only=True,
        tags={"hook", "injury"},
    ),
}

GEARS = {
    "towel": GearCfg(
        id="towel",
        label="soft towel",
        phrase="a soft towel",
        use_line="The towel could wrap the tiny body without a nip.",
        tags={"towel", "gentle_catch"},
    ),
    "basket": GearCfg(
        id="basket",
        label="reed basket",
        phrase="a little reed basket",
        use_line="The basket could lift the little one without squeezing.",
        tags={"basket", "gentle_catch"},
    ),
    "bare_hands": GearCfg(
        id="bare_hands",
        label="bare hands",
        phrase="bare hands alone",
        use_line="Bare hands might slip and scare the little one.",
        tags={"hands"},
    ),
}

RESPONSES = {
    "wrap_and_row": ResponseCfg(
        id="wrap_and_row",
        label="wrap and row",
        sense=3,
        calm=True,
        uses_gear=True,
        success_line=(
            f"With a hush and a glide, using the {{gear}}, they eased the small one free "
            f"from {{trouble}}. No splash and no snatch—just a patient rescue at {{bank}}."
        ),
        fail_line="",
        qa_line="They used a calm tool to lift the animal safely and rowed it to help.",
        tags={"calm_rescue", "veterinarian"},
    ),
    "basket_and_call": ResponseCfg(
        id="basket_and_call",
        label="basket and call",
        sense=3,
        calm=True,
        uses_gear=True,
        success_line=(
            f"Very slow, very low, they slipped the {{gear}} beneath the {{animal}} "
            f"and loosened {{trouble}}. Then they carried the little patient to {{bank}}."
        ),
        fail_line="",
        qa_line="They steadied the animal with a basket and brought it to the veterinarian.",
        tags={"calm_rescue", "veterinarian"},
    ),
    "splash_chase": ResponseCfg(
        id="splash_chase",
        label="splash chase",
        sense=1,
        calm=False,
        uses_gear=False,
        success_line="",
        fail_line="They splashed and lunged after the {animal}, but panic sent it deeper into the reeds.",
        qa_line="They rushed instead of staying calm, and that made the rescue worse.",
        tags={"panic"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Poppy", "Tess", "Wren"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Jude", "Ben"]


@dataclass
class StoryParams:
    setting: str
    animal: str
    trouble: str
    gear: str
    response: str
    child_name: str
    child_gender: str
    parent: str
    veterinarian: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kayak": [
        (
            "What is a kayak?",
            "A kayak is a small narrow boat that floats on the water. People sit low inside it and use a paddle to move."
        )
    ],
    "veterinarian": [
        (
            "What does a veterinarian do?",
            "A veterinarian is a doctor for animals. A veterinarian checks sick or hurt animals and helps them heal."
        )
    ],
    "duckling": [
        (
            "What is a duckling?",
            "A duckling is a baby duck. Ducklings are small, soft, and often stay close to safe water."
        )
    ],
    "otter": [
        (
            "What is an otter pup?",
            "An otter pup is a baby otter. Otters live near water and need to stay safe and warm."
        )
    ],
    "frog": [
        (
            "What is a froglet?",
            "A froglet is a very young frog. It is tiny and can be easy to frighten."
        )
    ],
    "line": [
        (
            "Why is fishing line dangerous for small animals?",
            "Fishing line can wrap around a small body or leg and pinch tightly. That can hurt the animal and keep it from moving well."
        )
    ],
    "reeds": [
        (
            "How can reeds trap a small animal?",
            "Reeds can twist around little feet or legs when an animal struggles. The more it wriggles, the tighter the tangle can feel."
        )
    ],
    "hook": [
        (
            "Why should a fishhook be removed carefully?",
            "A hook is sharp and can tear if it is yanked. Careful hands and a veterinarian help keep the hurt from getting worse."
        )
    ],
    "calm_rescue": [
        (
            "Why is staying calm important in an animal rescue?",
            "A calm rescue keeps a scared animal from panicking more. Slow movements can make it easier to help without causing extra hurt."
        )
    ],
    "towel": [
        (
            "Why might a towel help rescue a small animal?",
            "A towel can hold a little animal gently and keep it from slipping. It also helps the rescuer avoid grabbing too hard."
        )
    ],
    "basket": [
        (
            "Why can a basket be useful in a rescue?",
            "A basket gives a small animal a steady place to sit. That makes it easier to carry the animal to safe help."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "kayak",
    "veterinarian",
    "duckling",
    "otter",
    "frog",
    "line",
    "reeds",
    "hook",
    "calm_rescue",
    "towel",
    "basket",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal_cfg"]
    trouble = f["trouble"]
    setting = f["setting"]
    child = f["child"]
    outcome = f["outcome"]
    base = (
        f'Write a suspenseful nursery-rhyme story for a 3-to-5-year-old that includes the words '
        f'"kayak" and "veterinarian". The story should happen at {setting.water} and involve a {animal.label} in trouble.'
    )
    if outcome == "rescued":
        return [
            base,
            f"Tell a rhyming story where {child.id} hears a frightened {animal.label} from a kayak, stays calm, and brings it to a veterinarian.",
            f"Write a gentle rescue rhyme in which a child avoids splashing panic, uses safe help, and ends with the little animal resting safely near {animal.home}.",
        ]
    return [
        base,
        f"Tell a cautionary rhyme where {child.id} is tempted to rush the rescue from the kayak, and the story teaches why calm help matters.",
        f"Write a nursery-rhyme suspense story showing that a frightened {animal.label} near {trouble.label} needs patient care and a veterinarian, not a wild chase.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    animal = f["animal_cfg"]
    trouble = f["trouble"]
    response = f["response"]
    gear = f["gear_cfg"]
    setting = f["setting"]
    veterinarian = f["veterinarian"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and a little {animal.label} they found from a kayak. A veterinarian also helps when the rescue reaches shore."
        ),
        (
            "Why did the story feel suspenseful?",
            f"The animal was hurt and stuck by {trouble.label} near {setting.reeds}, so nobody knew at first if it would be safe. The quiet water and whispering plants made the moment feel tense."
        ),
        (
            f"What trouble was the {animal.label} in?",
            f"The little {animal.label} was caught in {trouble.label}. That hurt it and made it hard for it to move away safely."
        ),
    ]
    if outcome == "rescued":
        qa.append(
            (
                f"How did {child.id} and {parent.label_word} help without making things worse?",
                f"They stayed calm in the kayak and used {gear.phrase} as part of the rescue. Slow, careful movements kept the frightened animal from panicking more."
            )
        )
        qa.append(
            (
                "Why did they take the animal to the veterinarian?",
                f"They took the animal to the veterinarian because it was hurt and needed careful checking. The veterinarian made sure the trouble from {trouble.label} did not keep hurting it."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended softly and safely, with the little {animal.label} settled near {animal.home}. The quiet ending shows that the danger had passed."
            )
        )
    else:
        qa.append(
            (
                "What went wrong in the rescue?",
                f"They rushed instead of staying calm, and that frightened the little {animal.label}. Because the rescue became noisy and fast, the animal slipped away before the veterinarian could help."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned that a scared animal needs calm care, not a splashy chase. That lesson matters because rushing can turn a hard moment into a worse one."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"kayak", "veterinarian"} | set(f["animal_cfg"].tags) | set(f["trouble"].tags)
    if f["response"].id in ("wrap_and_row", "basket_and_call"):
        tags |= {"calm_rescue"}
    if f["gear_cfg"].id == "towel":
        tags |= {"towel"}
    if f["gear_cfg"].id == "basket":
        tags |= {"basket"}
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:20}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pond",
        animal="duckling",
        trouble="line",
        gear="towel",
        response="wrap_and_row",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        veterinarian="veterinarian_female",
    ),
    StoryParams(
        setting="lake",
        animal="otter_pup",
        trouble="reeds",
        gear="basket",
        response="basket_and_call",
        child_name="Owen",
        child_gender="boy",
        parent="father",
        veterinarian="veterinarian_male",
    ),
    StoryParams(
        setting="pond",
        animal="froglet",
        trouble="line",
        gear="basket",
        response="basket_and_call",
        child_name="Lila",
        child_gender="girl",
        parent="mother",
        veterinarian="veterinarian_female",
    ),
]


ASP_RULES = r"""
% Base validity.
valid_combo(A, T, G, R) :-
    animal(A), trouble(T), gear(G), response(R),
    water_only(T), needs_vet(T),
    sense(R, S), sense_min(M), S >= M,
    not needs_tool_but_bare(G, R),
    not bad_pair(A, T).

needs_tool_but_bare(bare_hands, R) :- uses_gear(R).
bad_pair(froglet, hook).

% Outcome model.
rescued(R) :- response(R), calm(R).
lost(R)    :- response(R), not calm(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for tid, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        if trouble.water_only:
            lines.append(asp.fact("water_only", tid))
        if trouble.needs_vet:
            lines.append(asp.fact("needs_vet", tid))
    for gid in GEARS:
        lines.append(asp.fact("gear", gid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        if response.uses_gear:
            lines.append(asp.fact("uses_gear", rid))
        if response.calm:
            lines.append(asp.fact("calm", rid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([asp.fact("chosen_response", params.response)])
    rules = r"""
outcome(rescued) :- chosen_response(R), rescued(R).
outcome(lost) :- chosen_response(R), lost(R).
"""
    model = asp.one_model(f"{asp_facts()}\n{ASP_RULES}\n{rules}\n{extra}\n#show outcome/1.\n")
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    return "rescued" if response.calm else "lost"


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

    checked = 0
    for params in CURATED:
        ao = asp_outcome(params)
        po = outcome_of(params)
        checked += 1
        if ao != po:
            rc = 1
            print(f"MISMATCH outcome for {params}: asp={ao} python={po}")
    if rc == 0:
        print(f"OK: outcome model matches on {checked} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as exc:  # pragma: no cover - verify path
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a kayak rescue rhyme with suspense and a veterinarian."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    animal_id = args.animal
    trouble_id = args.trouble
    gear_id = args.gear
    response_id = args.response

    if animal_id and trouble_id and gear_id and response_id:
        animal = ANIMALS[animal_id]
        trouble = TROUBLES[trouble_id]
        gear = GEARS[gear_id]
        response = RESPONSES[response_id]
        if not valid_combo(animal, trouble, gear, response):
            raise StoryError(explain_rejection(animal, trouble, gear, response))
    elif response_id and RESPONSES[response_id].sense < SENSE_MIN:
        animal = ANIMALS[animal_id] if animal_id else next(iter(ANIMALS.values()))
        trouble = TROUBLES[trouble_id] if trouble_id else next(iter(TROUBLES.values()))
        gear = GEARS[gear_id] if gear_id else next(iter(GEARS.values()))
        raise StoryError(explain_rejection(animal, trouble, gear, RESPONSES[response_id]))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.gear is None or combo[2] == args.gear)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, trouble_id, gear_id, response_id = rng.choice(sorted(combos))
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    veterinarian = rng.choice(["veterinarian_female", "veterinarian_male"])
    return StoryParams(
        setting=setting_id,
        animal=animal_id,
        trouble=trouble_id,
        gear=gear_id,
        response=response_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        veterinarian=veterinarian,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    animal = ANIMALS[params.animal]
    trouble = TROUBLES[params.trouble]
    gear = GEARS[params.gear]
    response = RESPONSES[params.response]
    if not valid_combo(animal, trouble, gear, response):
        raise StoryError(explain_rejection(animal, trouble, gear, response))

    world = tell(
        setting=SETTINGS[params.setting],
        animal_cfg=animal,
        trouble=trouble,
        gear_cfg=gear,
        response_cfg=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        veterinarian_type=params.veterinarian,
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
        print(asp_program("", "#show valid_combo/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, trouble, gear, response) combos:\n")
        for animal, trouble, gear, response in combos:
            print(f"  {animal:10} {trouble:8} {gear:10} {response}")
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
                f"### {p.child_name}: {p.animal} in {p.trouble} "
                f"({p.gear}, {p.response})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
