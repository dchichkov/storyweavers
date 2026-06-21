#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dote_sushi_blab_bad_ending_twist_whodunit.py
=======================================================================

A standalone storyworld for a tiny whodunit domain:

A child notices that a box of sushi has vanished. A clue points at the wrong
friend. Wanting to solve the mystery quickly, the child blurts out a private
secret instead of keeping quiet. Then comes the twist: an animal took the sushi,
not the friend. The mystery is solved, but the ending is sad because the friend
was hurt by the public accusation.

This world keeps the schema small and explicit:
- typed entities with physical meters and emotional memes
- a simple causal engine
- a Python reasonableness gate plus an inline ASP twin
- state-driven prose with a beginning, turn, twist, and bad ending

Run it
------
    python storyworlds/worlds/gpt-5.4/dote_sushi_blab_bad_ending_twist_whodunit.py
    python storyworlds/worlds/gpt-5.4/dote_sushi_blab_bad_ending_twist_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/dote_sushi_blab_bad_ending_twist_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/dote_sushi_blab_bad_ending_twist_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/dote_sushi_blab_bad_ending_twist_whodunit.py --verify
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

# Make shared result containers importable when this nested script is run
# directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CARE_MIN = 2


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
    edible: bool = False
    sneaky: bool = False
    loud: bool = False
    # shared state axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"cat", "dog", "gull"}
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
class Setting:
    id: str
    place: str
    scene: str
    animals: set[str] = field(default_factory=set)
    hiding_spot: str = ""
    echo: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SushiKind:
    id: str
    label: str
    phrase: str
    smell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectSecret:
    id: str
    secret: str
    cover_story: str
    innocent_reason: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CulpritKind:
    id: str
    label: str
    type: str
    enters: str
    action: str
    trace: str
    reveal: str
    likes_fish: bool = True
    sneaky: bool = True
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_hurt_friendship(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.memes["blabbed"] < THRESHOLD or suspect.memes["humiliation"] < THRESHOLD:
        return out
    sig = ("friendship_hurt", detective.id, suspect.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["guilt"] += 1
    suspect.memes["trust_lost"] += 1
    out.append("__friendship_hurt__")
    return out


def _r_empty_meal_sadness(world: World) -> list[str]:
    out: list[str] = []
    owner = world.get("owner")
    lunch = world.get("lunch")
    if lunch.meters["gone"] < THRESHOLD:
        return out
    sig = ("missing_food", owner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    owner.memes["disappointment"] += 1
    out.append("__missing_food__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_friendship", tag="social", apply=_r_hurt_friendship),
    Rule(name="empty_meal_sadness", tag="emotional", apply=_r_empty_meal_sadness),
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
            if item == "__friendship_hurt__":
                detective = world.get("detective")
                suspect = world.get("suspect")
                world.say(
                    f"{suspect.id}'s face changed at once, and {detective.id} felt the room turn colder."
                )
            elif item == "__missing_food__":
                owner = world.get("owner")
                world.say(
                    f"{owner.id}'s stomach gave a small, unhappy growl. Lunch was truly gone."
                )
    return produced


def culprit_allowed(setting: Setting, culprit: CulpritKind) -> bool:
    return culprit.id in setting.animals


def clue_is_reasonable(secret: SuspectSecret, sushi: SushiKind) -> bool:
    return bool(secret.clue) and bool(sushi.smell)


def valid_combo(setting: Setting, sushi: SushiKind, secret: SuspectSecret, culprit: CulpritKind) -> bool:
    return culprit_allowed(setting, culprit) and culprit.likes_fish and clue_is_reasonable(secret, sushi)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for sushi_id, sushi in SUSHI.items():
            for secret_id, secret in SECRETS.items():
                for culprit_id, culprit in CULPRITS.items():
                    if valid_combo(setting, sushi, secret, culprit):
                        combos.append((setting_id, sushi_id, secret_id, culprit_id))
    return combos


def would_blab(care_level: int) -> bool:
    return care_level < CARE_MIN


def explain_rejection(setting: Setting, sushi: SushiKind, secret: SuspectSecret, culprit: CulpritKind) -> str:
    if not culprit_allowed(setting, culprit):
        return (
            f"(No story: a {culprit.label} does not plausibly wander into {setting.place}. "
            f"Pick a culprit that belongs in that setting.)"
        )
    if not culprit.likes_fish:
        return (
            f"(No story: this culprit would not sensibly be drawn to {sushi.label}. "
            f"The twist needs a believable food thief.)"
        )
    if not clue_is_reasonable(secret, sushi):
        return (
            "(No story: the suspect needs an innocent clue strong enough to create a real mystery.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_wrong_accusation(world: World) -> dict:
    sim = world.copy()
    detective = sim.get("detective")
    suspect = sim.get("suspect")
    detective.memes["blabbed"] += 1
    suspect.memes["humiliation"] += 1
    propagate(sim, narrate=False)
    return {
        "friendship_hurt": sim.get("suspect").memes["trust_lost"] >= THRESHOLD,
        "detective_guilt": sim.get("detective").memes["guilt"] >= THRESHOLD,
    }


def introduce(world: World, detective: Entity, owner: Entity, suspect: Entity, setting: Setting, sushi: SushiKind) -> None:
    owner.memes["love_lunch"] += 1
    world.say(
        f"At {setting.place}, {setting.scene}."
    )
    world.say(
        f"{detective.id} liked mysteries so much that {detective.pronoun()} sometimes pretended every ordinary afternoon was a case."
    )
    world.say(
        f"That day, {owner.id} opened {owner.pronoun('possessive')} lunch bag and smiled at {sushi.phrase}. "
        f"{owner.id}'s grandmother used to dote on {owner.pronoun('object')} by tucking in the neat little rolls."
    )
    world.say(
        f"{suspect.id} was there too, trying hard to act normal."
    )


def hiding_beat(world: World, suspect: Entity, secret: SuspectSecret, setting: Setting) -> None:
    suspect.memes["worry"] += 1
    world.say(
        f"Before snack time, {suspect.id} had slipped near {setting.hiding_spot} because {secret.secret}. "
        f"{secret.cover_story}"
    )


def discover_loss(world: World, owner: Entity, sushi: SushiKind) -> None:
    lunch = world.get("lunch")
    lunch.meters["gone"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the lunch bag was opened again, the {sushi.label} was gone."
    )
    world.say(
        f'"A mystery," whispered {detective_name(world)}. {world.setting.echo}'
    )


def detective_name(world: World) -> str:
    return world.get("detective").id


def inspect_clue(world: World, detective: Entity, suspect: Entity, secret: SuspectSecret, sushi: SushiKind) -> None:
    detective.memes["suspicion"] += 1
    world.say(
        f"Near the bench, {detective.id} spotted {secret.clue}. It seemed to point straight at {suspect.id}."
    )
    world.say(
        f"The clue fit too neatly with the missing {sushi.label}, and that made {detective.id} feel very sure."
    )


def accusation(world: World, detective: Entity, suspect: Entity, owner: Entity, secret: SuspectSecret, care_level: int) -> None:
    pred = predict_wrong_accusation(world)
    world.facts["predicted_hurt"] = pred["friendship_hurt"]
    detective.memes["certainty"] += 1
    if would_blab(care_level):
        detective.memes["blabbed"] += 1
        suspect.memes["humiliation"] += 1
        propagate(world, narrate=True)
        world.say(
            f'"I know why you were sneaking around," {detective.id} said too loudly. '
            f'"You were hiding because {secret.secret.lower()}"'
        )
        world.say(
            f"Everyone stared at {suspect.id}. {owner.id} forgot the missing lunch for a moment."
        )
    else:
        detective.memes["care"] += 1
        world.say(
            f"{detective.id} almost blurted out the secret, but kept quiet and asked {suspect.id} to step aside instead."
        )
        world.say(
            f'"Did you take the lunch?" {detective.id} asked in a small voice.'
        )


def suspect_reply(world: World, suspect: Entity, secret: SuspectSecret) -> None:
    if world.get("detective").memes["blabbed"] >= THRESHOLD:
        world.say(
            f'{suspect.id} went red and shook {suspect.pronoun("possessive")} head. '
            f'"No," {suspect.pronoun()} said. "{secret.innocent_reason}"'
        )
    else:
        world.say(
            f'{suspect.id} whispered, "{secret.innocent_reason} I did not take it."'
        )


def reveal_twist(world: World, culprit_ent: Entity, culprit: CulpritKind, sushi: SushiKind, owner: Entity) -> None:
    culprit_ent.meters["seen_with_food"] += 1
    world.say(
        f"Then came the twist."
    )
    world.say(
        f"From {culprit.enters}, {culprit.action} with a piece of nori stuck to {culprit_ent.pronoun('possessive')} mouth."
    )
    world.say(
        f"{culprit.reveal} It had taken the {sushi.label} all along."
    )
    owner.memes["shock"] += 1


def bad_ending(world: World, detective: Entity, suspect: Entity, owner: Entity, secret: SuspectSecret) -> None:
    detective.memes["regret"] += 1
    suspect.memes["sadness"] += 1
    owner.memes["hunger"] += 1
    world.say(
        f"No one cheered. The case was solved, but the good feeling was gone."
    )
    if detective.memes["blabbed"] >= THRESHOLD:
        world.say(
            f"{suspect.id} picked up {suspect.pronoun('possessive')} bag and said nothing else. "
            f"The secret had already been told, and it could not be untold."
        )
        world.say(
            f"{detective.id} wanted to say sorry at once, yet the words came too late and too small."
        )
    else:
        world.say(
            f"{suspect.id} was still shaken by the question, and {detective.id} still felt ashamed for suspecting {suspect.pronoun('object')}."
        )
    world.say(
        f"{owner.id} went home hungry, and the mystery club did not meet again that week."
    )


def closing_image(world: World, detective: Entity, setting: Setting, culprit: CulpritKind) -> None:
    world.say(
        f"At the edge of {setting.place}, {detective.id} watched the last crumbs disappear and understood something harder than any riddle: "
        f"solving a mystery means little if you blab and hurt a friend before you know the truth."
    )


def tell(
    setting: Setting,
    sushi: SushiKind,
    secret: SuspectSecret,
    culprit: CulpritKind,
    detective_name_value: str = "Nina",
    detective_gender: str = "girl",
    owner_name: str = "Owen",
    owner_gender: str = "boy",
    suspect_name: str = "Mara",
    suspect_gender: str = "girl",
    parent_type: str = "mother",
    care_level: int = 0,
) -> World:
    world = World(setting)
    detective = world.add(
        Entity(
            id="detective",
            kind="character",
            type=detective_gender,
            label=detective_name_value,
            role="detective",
            traits=["observant"],
        )
    )
    owner = world.add(
        Entity(
            id="owner",
            kind="character",
            type=owner_gender,
            label=owner_name,
            role="owner",
            traits=["hopeful"],
        )
    )
    suspect_ent = world.add(
        Entity(
            id="suspect",
            kind="character",
            type=suspect_gender,
            label=suspect_name,
            role="suspect",
            traits=["private"],
        )
    )
    culprit_ent = world.add(
        Entity(
            id="culprit",
            kind="thing",
            type=culprit.type,
            label=culprit.label,
            phrase=f"the {culprit.label}",
            role="culprit",
            sneaky=culprit.sneaky,
            edible=False,
            tags=set(culprit.tags),
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the grown-up",
            role="adult",
        )
    )
    lunch = world.add(
        Entity(
            id="lunch",
            kind="thing",
            type="food",
            label=sushi.label,
            phrase=sushi.phrase,
            role="lunch",
            edible=True,
            tags=set(sushi.tags),
        )
    )

    world.facts["detective_public_name"] = detective_name_value
    world.facts["owner_public_name"] = owner_name
    world.facts["suspect_public_name"] = suspect_name

    introduce(world, detective, owner, suspect_ent, setting, sushi)
    hiding_beat(world, suspect_ent, secret, setting)

    world.para()
    discover_loss(world, owner, sushi)
    inspect_clue(world, detective, suspect_ent, secret, sushi)
    accusation(world, detective, suspect_ent, owner, secret, care_level)
    suspect_reply(world, suspect_ent, secret)

    world.para()
    reveal_twist(world, culprit_ent, culprit, sushi, owner)
    bad_ending(world, detective, suspect_ent, owner, secret)
    closing_image(world, detective, setting, culprit)

    outcome = "bad_blab_twist" if detective.memes["blabbed"] >= THRESHOLD else "bad_quiet_twist"
    world.facts.update(
        setting=setting,
        sushi=sushi,
        secret_cfg=secret,
        culprit_cfg=culprit,
        detective=detective,
        owner=owner,
        suspect=suspect_ent,
        culprit=culprit_ent,
        lunch=lunch,
        parent=parent,
        care_level=care_level,
        blabbed=detective.memes["blabbed"] >= THRESHOLD,
        outcome=outcome,
        friendship_hurt=suspect_ent.memes["trust_lost"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    sushi: str
    secret: str
    culprit: str
    detective_name: str
    detective_gender: str
    owner_name: str
    owner_gender: str
    suspect_name: str
    suspect_gender: str
    parent: str
    care_level: int
    seed: Optional[int] = None


SETTINGS = {
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard picnic table",
        scene="the noon bell had already rung, and little shadows lay under the bench",
        animals={"cat", "gull"},
        hiding_spot="the bench",
        echo="The place suddenly felt like a tiny detective office with no walls.",
        tags={"school", "mystery"},
    ),
    "park": Setting(
        id="park",
        place="the park by the duck pond",
        scene="the wind moved the reeds, and wrappers crackled softly in lunch bags",
        animals={"dog", "gull"},
        hiding_spot="the big stone planter",
        echo="Even the pond seemed to hold its breath.",
        tags={"park", "mystery"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch steps",
        scene="the boards were warm from the sun, and afternoon sat quiet in the garden",
        animals={"cat", "dog"},
        hiding_spot="the shoe basket",
        echo="For one second, the porch felt like the start of a very serious case.",
        tags={"home", "mystery"},
    ),
}

SUSHI = {
    "cucumber_rolls": SushiKind(
        id="cucumber_rolls",
        label="sushi",
        phrase="a tidy little box of sushi rolls",
        smell="a light vinegar smell",
        tags={"sushi", "food"},
    ),
    "salmon_nigiri": SushiKind(
        id="salmon_nigiri",
        label="salmon sushi",
        phrase="a neat tray of salmon sushi",
        smell="the rich fish smell",
        tags={"sushi", "fish"},
    ),
    "tuna_rolls": SushiKind(
        id="tuna_rolls",
        label="tuna sushi",
        phrase="a bright box of tuna sushi",
        smell="the salty sea smell",
        tags={"sushi", "fish"},
    ),
}

SECRETS = {
    "birthday_card": SuspectSecret(
        id="birthday_card",
        secret="she was hiding a birthday card she had made",
        cover_story="That was why she kept glancing around and tucking paper behind her back.",
        innocent_reason="I was hiding a surprise card for my brother",
        clue="a paper scrap with a little drawn fish on it",
        tags={"secret", "paper"},
    ),
    "crooked_chopsticks": SuspectSecret(
        id="crooked_chopsticks",
        secret="he had borrowed chopsticks and was practicing in secret because he kept dropping noodles",
        cover_story="That was why he looked guilty whenever someone came near.",
        innocent_reason="I was only practicing with chopsticks because I did not want anyone to laugh",
        clue="a pair of chopsticks peeking from a backpack pocket",
        tags={"secret", "chopsticks"},
    ),
    "poem": SuspectSecret(
        id="poem",
        secret="she was writing a shy poem and did not want anyone to read it yet",
        cover_story="That was why she had been crouching in the corner with a crayon.",
        innocent_reason="I was hiding a poem because it was private",
        clue="a crumpled note with hearts drawn in one corner",
        tags={"secret", "poem"},
    ),
}

CULPRITS = {
    "cat": CulpritKind(
        id="cat",
        label="striped cat",
        type="cat",
        enters="under the bench",
        action="padded out, licking happily",
        trace="tiny paw prints",
        reveal="A striped cat blinked as if the whole case had never been mysterious at all",
        likes_fish=True,
        sneaky=True,
        tags={"cat", "animal"},
    ),
    "dog": CulpritKind(
        id="dog",
        label="small dog",
        type="dog",
        enters="behind the planter",
        action="trotted out with the lunch ribbon hanging from its collar",
        trace="muddy paw marks",
        reveal="A small dog wagged once, guilty and cheerful together",
        likes_fish=True,
        sneaky=False,
        tags={"dog", "animal"},
    ),
    "gull": CulpritKind(
        id="gull",
        label="bold gull",
        type="gull",
        enters="the railing",
        action="hopped down, flapping, with rice stuck to its beak",
        trace="white feather and peck marks",
        reveal="A bold gull gave a sharp cry, as if announcing the answer itself",
        likes_fish=True,
        sneaky=True,
        tags={"gull", "animal"},
    ),
}

GIRL_NAMES = ["Nina", "Ruby", "Mila", "Tess", "Lena", "Ivy", "Cora", "June"]
BOY_NAMES = ["Owen", "Max", "Theo", "Ben", "Eli", "Noah", "Milo", "Finn"]


KNOWLEDGE = {
    "sushi": [
        (
            "What is sushi?",
            "Sushi is a food often made with rice and small toppings or fillings. Some sushi has fish, and some has vegetables."
        )
    ],
    "fish": [
        (
            "Why might an animal try to grab fishy food?",
            "Many animals notice strong food smells very quickly. Fish smells can attract them from far away."
        )
    ],
    "cat": [
        (
            "Why do cats sneak around food?",
            "Cats are quiet and curious, and they often creep close to food that smells interesting. They can snatch a bite before people notice."
        )
    ],
    "dog": [
        (
            "Why do dogs steal food sometimes?",
            "Dogs often follow their noses. If food smells good and is left where they can reach it, they may gulp it down fast."
        )
    ],
    "gull": [
        (
            "Why are gulls bold around lunches?",
            "Gulls learn that people sometimes leave tasty food out in the open. They can swoop or hop in quickly to grab it."
        )
    ],
    "secret": [
        (
            "What is a secret?",
            "A secret is something private that a person does not want shared yet. Kind people do not tell it around others without permission."
        )
    ],
    "blab": [
        (
            "What does blab mean?",
            "To blab means to tell something that should have been kept private. It can hurt someone's feelings or break trust."
        )
    ],
    "mystery": [
        (
            "What should a good detective do before accusing someone?",
            "A good detective should look for enough clues and check if there could be another answer. Guessing too fast can hurt innocent people."
        )
    ],
}
KNOWLEDGE_ORDER = ["sushi", "fish", "cat", "dog", "gull", "secret", "blab", "mystery"]


def public_name(ent: Entity, world: World) -> str:
    if ent.id == "detective":
        return world.facts["detective_public_name"]
    if ent.id == "owner":
        return world.facts["owner_public_name"]
    if ent.id == "suspect":
        return world.facts["suspect_public_name"]
    return ent.label or ent.id


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = public_name(f["detective"], world)
    suspect = public_name(f["suspect"], world)
    sushi = f["sushi"]
    setting = f["setting"]
    return [
        (
            f'Write a short whodunit for a 3-to-5-year-old where a child tries to solve the mystery of missing {sushi.label} at {setting.place}. '
            'Include the words "dote", "sushi", and "blab", and use a twist with a sad ending.'
        ),
        (
            f"Tell a tiny mystery story where {detective} accuses {suspect} too quickly, blurts out a private secret, and then learns an animal was the real thief."
        ),
        (
            'Write a gentle but unhappy detective story for children that teaches not to blab before you know the truth.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = public_name(f["detective"], world)
    owner = public_name(f["owner"], world)
    suspect = public_name(f["suspect"], world)
    culprit = f["culprit_cfg"]
    secret = f["secret_cfg"]
    sushi = f["sushi"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective}, who wanted to solve a mystery, {owner}, whose lunch went missing, and {suspect}, who was wrongly suspected."
        ),
        (
            "What was missing?",
            f"The missing thing was {sushi.phrase}. It disappeared from the lunch bag before anyone was ready to eat."
        ),
        (
            f"Why did {detective} suspect {suspect}?",
            f"{detective} saw {secret.clue} and connected it to the missing lunch too quickly. The clue looked suspicious, but it really came from {secret.innocent_reason.lower()}."
        ),
    ]
    if f["blabbed"]:
        qa.append(
            (
                f"What bad thing did {detective} do while trying to solve the case?",
                f"{detective} chose to blab {suspect}'s private secret in front of everyone. That hurt {suspect}'s feelings before the mystery was even solved."
            )
        )
    qa.append(
        (
            "What was the twist?",
            f"The twist was that a {culprit.label} had taken the sushi, not {suspect}. The real answer appeared only after the accusation had already done harm."
        )
    )
    qa.append(
        (
            "Why is the ending sad even after the mystery is solved?",
            f"The lunch was gone, so {owner} still lost the meal. Worse, {suspect}'s private secret had been exposed, so the friendship felt hurt even after the truth came out."
        )
    )
    qa.append(
        (
            "What lesson does the story teach?",
            f"It teaches that you should not accuse people or blab private things just because a clue seems neat. A mystery needs patience, because the first answer can be wrong."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sushi", "secret", "blab", "mystery"}
    tags |= set(f["sushi"].tags)
    tags |= set(f["culprit_cfg"].tags)
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
    for eid, e in world.entities.items():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = [f"type={e.type}"]
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {eid:10} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Reasonableness gate.
valid(Setting, Sushi, Secret, Culprit) :-
    setting(Setting), sushi(Sushi), secret(Secret), culprit(Culprit),
    allows(Setting, Culprit), likes_fish(Culprit), has_clue(Secret).

% Outcome model.
blabbed :- care_level(C), care_min(M), C < M.
outcome(bad_blab_twist) :- blabbed.
outcome(bad_quiet_twist) :- not blabbed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for animal in sorted(setting.animals):
            lines.append(asp.fact("allows", sid, animal))
    for sid in SUSHI:
        lines.append(asp.fact("sushi", sid))
    for secret_id, secret in SECRETS.items():
        lines.append(asp.fact("secret", secret_id))
        if clue_is_reasonable(secret, next(iter(SUSHI.values()))):
            lines.append(asp.fact("has_clue", secret_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        if culprit.likes_fish:
            lines.append(asp.fact("likes_fish", culprit_id))
    lines.append(asp.fact("care_min", CARE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("care_level", params.care_level),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def outcome_of(params: StoryParams) -> str:
    return "bad_blab_twist" if would_blab(params.care_level) else "bad_quiet_twist"


CURATED = [
    StoryParams(
        setting="schoolyard",
        sushi="salmon_nigiri",
        secret="birthday_card",
        culprit="cat",
        detective_name="Nina",
        detective_gender="girl",
        owner_name="Owen",
        owner_gender="boy",
        suspect_name="Mila",
        suspect_gender="girl",
        parent="mother",
        care_level=0,
    ),
    StoryParams(
        setting="park",
        sushi="tuna_rolls",
        secret="crooked_chopsticks",
        culprit="dog",
        detective_name="Theo",
        detective_gender="boy",
        owner_name="Ruby",
        owner_gender="girl",
        suspect_name="Ben",
        suspect_gender="boy",
        parent="father",
        care_level=1,
    ),
    StoryParams(
        setting="porch",
        sushi="cucumber_rolls",
        secret="poem",
        culprit="cat",
        detective_name="June",
        detective_gender="girl",
        owner_name="Finn",
        owner_gender="boy",
        suspect_name="Ivy",
        suspect_gender="girl",
        parent="mother",
        care_level=0,
    ),
    StoryParams(
        setting="schoolyard",
        sushi="tuna_rolls",
        secret="poem",
        culprit="gull",
        detective_name="Max",
        detective_gender="boy",
        owner_name="Lena",
        owner_gender="girl",
        suspect_name="Cora",
        suspect_gender="girl",
        parent="father",
        care_level=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a small whodunit about missing sushi, a wrong accusation, a blabbed secret, and a sad twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sushi", choices=SUSHI)
    ap.add_argument("--secret", choices=SECRETS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--detective-name")
    ap.add_argument("--owner-name")
    ap.add_argument("--suspect-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument(
        "--care-level",
        type=int,
        choices=[0, 1, 2, 3],
        help="how careful the detective is with secrets; low values lead to blabbing",
    )
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python and ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.sushi and args.secret and args.culprit:
        setting = SETTINGS[args.setting]
        sushi = SUSHI[args.sushi]
        secret = SECRETS[args.secret]
        culprit = CULPRITS[args.culprit]
        if not valid_combo(setting, sushi, secret, culprit):
            raise StoryError(explain_rejection(setting, sushi, secret, culprit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.sushi is None or combo[1] == args.sushi)
        and (args.secret is None or combo[2] == args.secret)
        and (args.culprit is None or combo[3] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sushi_id, secret_id, culprit_id = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    suspect_gender = args.suspect_gender or rng.choice(["girl", "boy"])

    used: set[str] = set()
    detective_name = args.detective_name or pick_name(rng, detective_gender, used)
    used.add(detective_name)
    owner_name = args.owner_name or pick_name(rng, owner_gender, used)
    used.add(owner_name)
    suspect_name = args.suspect_name or pick_name(rng, suspect_gender, used)

    return StoryParams(
        setting=setting_id,
        sushi=sushi_id,
        secret=secret_id,
        culprit=culprit_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
        suspect_name=suspect_name,
        suspect_gender=suspect_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        care_level=args.care_level if args.care_level is not None else rng.choice([0, 1, 2]),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        sushi = SUSHI[params.sushi]
        secret = SECRETS[params.secret]
        culprit = CULPRITS[params.culprit]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from err

    if not valid_combo(setting, sushi, secret, culprit):
        raise StoryError(explain_rejection(setting, sushi, secret, culprit))

    world = tell(
        setting=setting,
        sushi=sushi,
        secret=secret,
        culprit=culprit,
        detective_name_value=params.detective_name,
        detective_gender=params.detective_gender,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        suspect_name=params.suspect_name,
        suspect_gender=params.suspect_gender,
        parent_type=params.parent,
        care_level=params.care_level,
    )

    story = world.render()
    if "{" in story or "}" in story:
        raise StoryError("(Rendering failed: unresolved template text leaked into story output.)")

    return StorySample(
        params=params,
        story=story,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases: list[StoryParams] = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story is empty.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, sushi, secret, culprit) combos:\n")
        for setting, sushi, secret, culprit in combos:
            print(f"  {setting:10} {sushi:15} {secret:18} {culprit}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.sushi} missing at {p.setting} ({p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
