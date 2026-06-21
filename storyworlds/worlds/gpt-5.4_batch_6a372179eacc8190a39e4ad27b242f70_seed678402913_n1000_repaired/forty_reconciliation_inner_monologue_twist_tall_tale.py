#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/forty_reconciliation_inner_monologue_twist_tall_tale.py
==================================================================================

A standalone story world for a child-facing tall tale about an enormous ranch
problem, a misunderstanding between two friends, an inner monologue that turns
the quarrel, and a twist that reveals what really happened.

This world models a simple classical arc:

    setup -> boastful giant task -> mishap -> blame -> quiet inner choice
    -> reconciliation -> twist reveal -> shared ending image

The tone stays close to a tall tale: outsized objects, windy plains, silly
measurements, and cheerful exaggeration. But the world itself is kept small and
boring: two children, one giant animal, one missing item, one guess about what
happened, and one truth.

Run it
------
    python storyworlds/worlds/gpt-5.4/forty_reconciliation_inner_monologue_twist_tall_tale.py
    python storyworlds/worlds/gpt-5.4/forty_reconciliation_inner_monologue_twist_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/forty_reconciliation_inner_monologue_twist_tall_tale.py --animal ox --missing bell
    python storyworlds/worlds/gpt-5.4/forty_reconciliation_inner_monologue_twist_tall_tale.py --guess theft
    python storyworlds/worlds/gpt-5.4/forty_reconciliation_inner_monologue_twist_tall_tale.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    stride_line: str
    sound: str
    can_carry: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingCfg:
    id: str
    label: str
    phrase: str
    giant_line: str
    track_line: str
    carried_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class GuessCfg:
    id: str
    accusation: str
    wrong_line: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairCfg:
    id: str
    apology_line: str
    make_peace_line: str
    strength: int
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


def _r_hurt_feelings(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    pal = world.get("pal")
    if hero.memes["blaming"] < THRESHOLD:
        return out
    sig = ("hurt_feelings",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pal.memes["hurt"] += 1
    hero.memes["distance"] += 1
    pal.memes["distance"] += 1
    out.append("__hurt__")
    return out


def _r_apology_softens(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    pal = world.get("pal")
    if hero.memes["apologized"] < THRESHOLD:
        return out
    sig = ("apology_softens",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["distance"] = 0.0
    pal.memes["distance"] = 0.0
    hero.memes["peace"] += 1
    pal.memes["peace"] += 1
    out.append("__peace__")
    return out


def _r_truth_clears_blame(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    pal = world.get("pal")
    if world.get("item").meters["found"] < THRESHOLD:
        return out
    sig = ("truth_clears_blame",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["certainty"] = 0.0
    hero.memes["wonder"] += 1
    pal.memes["wonder"] += 1
    out.append("__truth__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_feelings", tag="social", apply=_r_hurt_feelings),
    Rule(name="apology_softens", tag="social", apply=_r_apology_softens),
    Rule(name="truth_clears_blame", tag="social", apply=_r_truth_clears_blame),
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


ANIMALS = {
    "ox": AnimalCfg(
        id="ox",
        label="blue ox",
        phrase="a blue ox so broad it shaded half the yard",
        stride_line="Each of its steps was long enough to cross a creek without getting a hoof damp.",
        sound="snorted like a brass band warming up",
        can_carry={"bell", "saddle"},
        tags={"ox", "ranch"},
    ),
    "hen": AnimalCfg(
        id="hen",
        label="red hen",
        phrase="a red hen tall enough to peck apples from the top branch",
        stride_line="When it crossed the field, the wheat bent politely out of the way.",
        sound="clucked so loudly the fence posts seemed to answer back",
        can_carry={"bell", "hat"},
        tags={"hen", "farm"},
    ),
    "mule": AnimalCfg(
        id="mule",
        label="gray mule",
        phrase="a gray mule with ears like sailcloth and patience longer than a dirt road",
        stride_line="It could step over a wagon tongue as if it were a skipping rope.",
        sound="brayed loud enough to rattle the weather vane",
        can_carry={"saddle", "hat"},
        tags={"mule", "ranch"},
    ),
}

MISSING = {
    "bell": MissingCfg(
        id="bell",
        label="bell",
        phrase="the brass bell",
        giant_line="That bell was so big it took both children and one fence rail to polish it.",
        track_line="In the dust lay a round mark, bright as a coin, where the bell had last rested.",
        carried_by={"ox", "hen"},
        tags={"bell", "metal"},
    ),
    "hat": MissingCfg(
        id="hat",
        label="hat",
        phrase="the ten-gallon hat",
        giant_line="That hat was so wide it could shade forty watermelons at noon.",
        track_line="In the dust lay a hat-shaped hollow, neat as if the wind had traced it with a spoon.",
        carried_by={"hen", "mule"},
        tags={"hat", "clothes"},
    ),
    "saddle": MissingCfg(
        id="saddle",
        label="saddle",
        phrase="the parade saddle",
        giant_line="That saddle was so shiny the sunset checked itself in the leather each evening.",
        track_line="In the dust lay a smooth oval print and one lonely buckle gleaming nearby.",
        carried_by={"ox", "mule"},
        tags={"saddle", "leather"},
    ),
}

GUESSES = {
    "theft": GuessCfg(
        id="theft",
        accusation="You took it to win the bragging match.",
        wrong_line="The guess felt sharp in the mouth, like biting a peppermint that had turned to a nail.",
        kind="blame",
        tags={"blame"},
    ),
    "hiding": GuessCfg(
        id="hiding",
        accusation="You hid it just to make me look foolish.",
        wrong_line="The guess came fast, quicker than good sense.",
        kind="blame",
        tags={"blame"},
    ),
    "careless": GuessCfg(
        id="careless",
        accusation="You left the gate open and let it wander off.",
        wrong_line="The guess sounded sensible for half a second and mean for the half after that.",
        kind="blame",
        tags={"blame"},
    ),
}

REPAIRS = {
    "plain_apology": RepairCfg(
        id="plain_apology",
        apology_line=' "I was wrong to snap at you," ',
        make_peace_line="The words were plain, but plain words can mend a fence fast when they are true.",
        strength=2,
        tags={"apology"},
    ),
    "share_work": RepairCfg(
        id="share_work",
        apology_line=' "I was wrong, and I will help fix this with you," ',
        make_peace_line="That promise put its shoulder to the quarrel and pushed it over.",
        strength=3,
        tags={"apology", "help"},
    ),
    "laugh_first": RepairCfg(
        id="laugh_first",
        apology_line=' "I let a silly thought boss me around. I am sorry," ',
        make_peace_line="A little laugh slipped in with the apology, and the hard knot between them loosened.",
        strength=2,
        tags={"apology", "laugh"},
    ),
}

GIRL_NAMES = ["Mira", "June", "Tess", "Lila", "Nora", "Ava", "Sadie", "Pearl"]
BOY_NAMES = ["Hank", "Eli", "Beau", "Cal", "Finn", "Wes", "Luke", "Jasper"]
TRAITS = ["bold", "steady", "quick", "cheerful", "stubborn", "kind"]


def valid_combo(animal_id: str, missing_id: str, guess_id: str, repair_id: str) -> bool:
    animal = ANIMALS[animal_id]
    missing = MISSING[missing_id]
    guess = GUESSES[guess_id]
    repair = REPAIRS[repair_id]
    if missing_id not in animal.can_carry or animal_id not in missing.carried_by:
        return False
    if guess.kind != "blame":
        return False
    if repair.strength < 2:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for animal_id in sorted(ANIMALS):
        for missing_id in sorted(MISSING):
            for guess_id in sorted(GUESSES):
                for repair_id in sorted(REPAIRS):
                    if valid_combo(animal_id, missing_id, guess_id, repair_id):
                        out.append((animal_id, missing_id, guess_id, repair_id))
    return out


@dataclass
class StoryParams:
    animal: str
    missing: str
    guess: str
    repair: str
    hero_name: str
    hero_gender: str
    pal_name: str
    pal_gender: str
    elder: str
    elder_gender: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        animal="ox",
        missing="bell",
        guess="theft",
        repair="share_work",
        hero_name="Hank",
        hero_gender="boy",
        pal_name="June",
        pal_gender="girl",
        elder="Grandma Maple",
        elder_gender="woman",
        trait="bold",
        seed=1,
    ),
    StoryParams(
        animal="hen",
        missing="hat",
        guess="hiding",
        repair="laugh_first",
        hero_name="Mira",
        hero_gender="girl",
        pal_name="Beau",
        pal_gender="boy",
        elder="Uncle Reed",
        elder_gender="man",
        trait="quick",
        seed=2,
    ),
    StoryParams(
        animal="mule",
        missing="saddle",
        guess="careless",
        repair="plain_apology",
        hero_name="Tess",
        hero_gender="girl",
        pal_name="Finn",
        pal_gender="boy",
        elder="Grandpa Clay",
        elder_gender="man",
        trait="steady",
        seed=3,
    ),
]


def predict_guess_hurts(world: World) -> bool:
    sim = world.copy()
    sim.get("hero").memes["blaming"] += 1
    propagate(sim, narrate=False)
    return sim.get("pal").memes["hurt"] >= THRESHOLD


def intro(world: World, hero: Entity, pal: Entity, elder: Entity, animal: AnimalCfg, missing: MissingCfg) -> None:
    world.say(
        f"On a windy plain where sunflowers leaned to listen and dust devils practiced square dancing, "
        f"{hero.id} and {pal.id} worked for {elder.id}."
    )
    world.say(
        f"They looked after {animal.phrase}, and they kept an eye on {missing.phrase}. "
        f"{animal.stride_line}"
    )
    world.say(
        f"{missing.giant_line} Folks on that plain said if a thing could be told in an ordinary way, "
        f"it hardly seemed worth telling."
    )


def boast(world: World, hero: Entity, pal: Entity, animal: AnimalCfg, missing: MissingCfg) -> None:
    hero.memes["joy"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"That morning the two of them were holding a bragging match, friendly as pie and loud as geese."
    )
    world.say(
        f'"I can hear that {animal.label} {animal.sound} from forty fence posts away," {hero.id} said.'
    )
    world.say(
        f'"And I can shine {missing.phrase} so bright a cloud can comb its hair in it," {pal.id} answered.'
    )


def mishap(world: World, hero: Entity, pal: Entity, animal: AnimalCfg, missing: MissingCfg) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    world.say(
        f"When the wind took a deep breath and the yard turned its head for one blink, {missing.phrase} was gone."
    )
    world.say(missing.track_line)


def accusation(world: World, hero: Entity, pal: Entity, guess: GuessCfg) -> None:
    hero.memes["certainty"] += 1
    hero.memes["blaming"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} looked at {pal.id}, and the wrong idea leaped up before patience could catch it. '
        f'"{guess.accusation}"'
    )
    world.say(guess.wrong_line)


def inner_monologue(world: World, hero: Entity, pal: Entity) -> None:
    hurts = predict_guess_hurts(world)
    hero.memes["thinking"] += 1
    if hurts:
        hero.memes["conscience"] += 1
        world.say(
            f"{hero.id} heard the words hang in the air and thought, "
            f'"That sounded bigger than the truth. {pal.id} has stood beside me in dust, rain, and chores. '
            f'If I keep feeding this quarrel, it will grow taller than the windmill."'
        )
    else:
        world.say(
            f"{hero.id} paused and thought, "
            f'"I had better sort my thoughts before they gallop away with me."'
        )


def soften(world: World, pal: Entity) -> None:
    if pal.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{pal.id}'s face fell a little. {pal.pronoun().capitalize()} did not stomp or shout. "
            f"{pal.pronoun().capitalize()} just looked more lonely than angry."
        )
    else:
        world.say(
            f"{pal.id} blinked, surprised, and the plain seemed to go quiet around them."
        )


def reconcile(world: World, hero: Entity, pal: Entity, repair: RepairCfg) -> None:
    hero.memes["apologized"] += 1
    propagate(world, narrate=False)
    elder_title = world.get("elder").id
    world.say(
        f'{hero.id} took off {hero.pronoun("possessive")} hat, scuffed the dust with one boot, and said,{repair.apology_line}{hero.id} told {pal.id}.'
    )
    world.say(repair.make_peace_line)
    world.say(
        f"{pal.id} nodded. Together they followed the strange marks instead of the mean guess."
    )
    world.facts["reconciled_before_twist"] = True
    world.facts["used_repair"] = repair.id
    world.facts["elder_name"] = elder_title


def reveal(world: World, hero: Entity, pal: Entity, animal: AnimalCfg, missing: MissingCfg) -> None:
    item = world.get("item")
    animal_ent = world.get("animal")
    item.meters["found"] += 1
    animal_ent.meters["carrying"] += 1
    propagate(world, narrate=False)
    if missing.id == "bell":
        how = f"looped over one horn like a shiny bracelet"
    elif missing.id == "hat":
        how = f"perched between its ears at a proud little angle"
    else:
        how = f"hanging from its side as neat as if it had saddled itself"
    world.say(
        f"Then came the twist that turned the whole trouble inside out: the {animal.label} strolled up from behind the barn with {missing.phrase} {how}."
    )
    world.say(
        f"It had not been stolen at all. The creature had simply wandered off wearing the answer."
    )
    world.say(
        f"{hero.id} and {pal.id} stared for one heartbeat, and then the laugh hit both of them at once."
    )
    world.facts["twist_truth"] = f"The {animal.label} had carried off {missing.phrase}."


def ending(world: World, hero: Entity, pal: Entity, elder: Entity, animal: AnimalCfg, missing: MissingCfg) -> None:
    hero.memes["joy"] += 1
    pal.memes["joy"] += 1
    hero.memes["peace"] += 1
    pal.memes["peace"] += 1
    world.say(
        f"{elder.id} laughed so hard the porch rocker tapped time. "
        f'"Well now," {elder.pronoun()} said, "the plain is big, but a hasty thought is bigger."'
    )
    world.say(
        f"By sunset, {hero.id} and {pal.id} were polishing {missing.phrase} together while the {animal.label} chewed clover and looked pleased with itself."
    )
    world.say(
        f"After that, whenever a problem blew in across the prairie, they checked the tracks before they blamed each other."
    )


def tell(
    animal: AnimalCfg,
    missing: MissingCfg,
    guess: GuessCfg,
    repair: RepairCfg,
    hero_name: str,
    hero_gender: str,
    pal_name: str,
    pal_gender: str,
    elder_name: str,
    elder_gender: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero", traits=[trait]))
    pal = world.add(Entity(id="pal", kind="character", type=pal_gender, label=pal_name, phrase=pal_name, role="pal", traits=["faithful"]))
    elder = world.add(Entity(id="elder", kind="character", type=elder_gender, label=elder_name, phrase=elder_name, role="elder"))
    animal_ent = world.add(Entity(id="animal", type="animal", label=animal.label, phrase=animal.phrase, role="animal", tags=set(animal.tags)))
    item = world.add(Entity(id="item", type="thing", label=missing.label, phrase=missing.phrase, role="item", tags=set(missing.tags)))

    world.facts.update(
        animal_cfg=animal,
        missing_cfg=missing,
        guess_cfg=guess,
        repair_cfg=repair,
        hero=hero,
        pal=pal,
        elder=elder,
        animal=animal_ent,
        item=item,
        hero_name=hero_name,
        pal_name=pal_name,
        elder_name=elder_name,
        trait=trait,
        reconciled_before_twist=False,
        twist_truth="",
    )

    intro(world, hero, pal, elder, animal, missing)
    boast(world, hero, pal, animal, missing)

    world.para()
    mishap(world, hero, pal, animal, missing)
    accusation(world, hero, pal, guess)
    soften(world, pal)

    world.para()
    inner_monologue(world, hero, pal)
    reconcile(world, hero, pal, repair)

    world.para()
    reveal(world, hero, pal, animal, missing)
    ending(world, hero, pal, elder, animal, missing)
    return world


KNOWLEDGE = {
    "tall_tale": [
        (
            "What is a tall tale?",
            "A tall tale is a story that tells something in a playful, extra-big way. It stretches the truth on purpose to make the story funny and vivid."
        )
    ],
    "blame": [
        (
            "Why is it better to ask what happened before blaming someone?",
            "Because a quick guess can be wrong and can hurt someone's feelings. Looking for the real reason first helps people stay fair and kind."
        )
    ],
    "apology": [
        (
            "What does an apology do?",
            "An apology tells someone you know you caused hurt and want to mend it. Honest apologies can help people trust each other again."
        )
    ],
    "tracks": [
        (
            "Why do tracks help solve a mystery?",
            "Tracks are signs left behind by feet, wheels, or things being dragged. They can show where something went and what really happened."
        )
    ],
    "ranch": [
        (
            "What is a ranch?",
            "A ranch is a big place where people care for animals over a lot of land. There may be barns, fences, fields, and long dusty paths."
        )
    ],
    "ox": [
        (
            "What is an ox?",
            "An ox is a strong working animal, usually a kind of cattle trained to pull or carry heavy things. In stories, an ox is often shown as steady and powerful."
        )
    ],
    "hen": [
        (
            "What is a hen?",
            "A hen is a female chicken. Real hens are much smaller than the giant one in this tall tale."
        )
    ],
    "mule": [
        (
            "What is a mule?",
            "A mule is a strong animal with long ears that is known for working hard and carrying loads. People often describe mules as sturdy and stubborn."
        )
    ],
    "bell": [
        (
            "What is a bell used for on an animal or at a farm?",
            "A bell can help people hear where an animal is, and it can also be part of a parade or decoration. Its ringing carries farther than a quiet footstep."
        )
    ],
    "hat": [
        (
            "What does a wide hat do?",
            "A wide hat gives shade from the sun. In a story, a very big hat can also make a person look grand and silly at the same time."
        )
    ],
    "saddle": [
        (
            "What is a saddle?",
            "A saddle is a seat fastened on an animal's back so a rider can sit more safely. It usually has straps and stirrups."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "tall_tale",
    "blame",
    "apology",
    "tracks",
    "ranch",
    "ox",
    "hen",
    "mule",
    "bell",
    "hat",
    "saddle",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    animal = f["animal_cfg"]
    missing = f["missing_cfg"]
    hero = f["hero"]
    pal = f["pal"]
    return [
        f'Write a child-friendly tall tale that includes the word "forty" and features a misunderstanding over {missing.phrase}.',
        f"Tell a prairie tall tale where {hero.label} wrongly blames {pal.label}, then has an inner thought that leads to reconciliation before a funny twist reveals the truth.",
        f"Write a story about a giant {animal.label}, a missing {missing.label}, hurt feelings, an apology, and an ending where the friends laugh together."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    pal = f["pal"]
    elder = f["elder"]
    animal_cfg = f["animal_cfg"]
    missing_cfg = f["missing_cfg"]
    guess_cfg = f["guess_cfg"]
    repair_cfg = f["repair_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {pal.label}, two young helpers on the plain, along with {elder.label} and a giant {animal_cfg.label}. They are trying to solve what happened to {missing_cfg.phrase}."
        ),
        (
            f"What went missing?",
            f"{missing_cfg.phrase.capitalize()} went missing in the wind. That loss started the argument because the children did not know where it had gone."
        ),
        (
            f"Why did {hero.label} blame {pal.label}?",
            f"{hero.label} made a quick guess instead of waiting for proof and said, \"{guess_cfg.accusation}\" The item had vanished so suddenly that the wrong idea jumped up before patience did."
        ),
        (
            f"What was {hero.label} thinking during the quiet moment?",
            f"{hero.label} realized the accusation had grown bigger than the truth. In that inner thought, {hero.pronoun().capitalize()} understood that feeding the quarrel would hurt a friend who had worked beside {hero.pronoun('object')}."
        ),
        (
            f"How did the children reconcile?",
            f"{hero.label} apologized using {repair_cfg.id.replace('_', ' ')} and stopped chasing the mean guess. Then both children followed the signs together, which turned them back into partners instead of opponents."
        ),
        (
            "What was the twist?",
            f"The twist was that {missing_cfg.phrase} had not been stolen or hidden by {pal.label} at all. {f['twist_truth']}"
        ),
        (
            "How did the story end?",
            f"It ended with the children laughing together and polishing {missing_cfg.phrase} side by side while {elder.label} watched. The last image shows that the friendship is mended because they are working together again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tall_tale", "blame", "apology", "tracks"}
    tags |= set(f["animal_cfg"].tags)
    tags |= set(f["missing_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label:
            bits.append(f"label={ent.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(animal_id: str, missing_id: str, guess_id: str, repair_id: str) -> str:
    animal = ANIMALS[animal_id]
    missing = MISSING[missing_id]
    guess = GUESSES[guess_id]
    repair = REPAIRS[repair_id]
    if missing_id not in animal.can_carry or animal_id not in missing.carried_by:
        return (
            f"(No story: a {animal.label} and {missing.phrase} do not fit this tiny world's twist. "
            f"The final reveal only works when that animal could plausibly wander off carrying the item.)"
        )
    if guess.kind != "blame":
        return "(No story: the middle turn needs a mistaken blame guess.)"
    if repair.strength < 2:
        return (
            f"(No story: repair '{repair.id}' is too weak for a full reconciliation. "
            f"This world requires a clear apology before the twist.)"
        )
    return "(No story: this combination is not supported.)"


ASP_RULES = r"""
can_twist(A, M) :- carries(A, M), carried_by(M, A).
valid(A, M, G, R) :- animal(A), missing(M), guess(G), repair(R),
                     can_twist(A, M), blame_guess(G), repair_strength(R, S), S >= 2.

hurt_by_blame :- chosen_guess(G), blame_guess(G).
reconciled    :- chosen_repair(R), repair_strength(R, S), S >= 2.
twist_ready   :- chosen_animal(A), chosen_missing(M), can_twist(A, M).

story_ok      :- hurt_by_blame, reconciled, twist_ready.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for missing_id in sorted(animal.can_carry):
            lines.append(asp.fact("carries", animal_id, missing_id))
    for missing_id, missing in MISSING.items():
        lines.append(asp.fact("missing", missing_id))
        for animal_id in sorted(missing.carried_by):
            lines.append(asp.fact("carried_by", missing_id, animal_id))
    for guess_id, guess in GUESSES.items():
        lines.append(asp.fact("guess", guess_id))
        if guess.kind == "blame":
            lines.append(asp.fact("blame_guess", guess_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("repair_strength", repair_id, repair.strength))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_ok(params: StoryParams) -> bool:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_animal", params.animal),
            asp.fact("chosen_missing", params.missing),
            asp.fact("chosen_guess", params.guess),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show story_ok/0."))
    return bool(asp.atoms(model, "story_ok"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a giant ranch mystery, a mistaken blame, an inner thought, and a reconciled twist."
    )
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--missing", choices=sorted(MISSING))
    ap.add_argument("--guess", choices=sorted(GUESSES))
    ap.add_argument("--repair", choices=sorted(REPAIRS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--pal-name")
    ap.add_argument("--pal-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.missing and args.guess and args.repair:
        if not valid_combo(args.animal, args.missing, args.guess, args.repair):
            raise StoryError(explain_rejection(args.animal, args.missing, args.guess, args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.missing is None or combo[1] == args.missing)
        and (args.guess is None or combo[2] == args.guess)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        animal_id = args.animal or next(iter(ANIMALS))
        missing_id = args.missing or next(iter(MISSING))
        guess_id = args.guess or next(iter(GUESSES))
        repair_id = args.repair or next(iter(REPAIRS))
        raise StoryError(explain_rejection(animal_id, missing_id, guess_id, repair_id))

    animal_id, missing_id, guess_id, repair_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    pal_gender = args.pal_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    pal_name = args.pal_name or _pick_name(rng, pal_gender, avoid=hero_name)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    if args.elder:
        elder_name = args.elder
    else:
        elder_name = rng.choice(["Grandma Maple", "Grandpa Clay", "Aunt Willow", "Uncle Reed"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        animal=animal_id,
        missing=missing_id,
        guess=guess_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        pal_name=pal_name,
        pal_gender=pal_gender,
        elder=elder_name,
        elder_gender=elder_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS or params.missing not in MISSING or params.guess not in GUESSES or params.repair not in REPAIRS:
        raise StoryError("(Invalid params: unknown registry key.)")
    if not valid_combo(params.animal, params.missing, params.guess, params.repair):
        raise StoryError(explain_rejection(params.animal, params.missing, params.guess, params.repair))

    world = tell(
        animal=ANIMALS[params.animal],
        missing=MISSING[params.missing],
        guess=GUESSES[params.guess],
        repair=REPAIRS[params.repair],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        pal_name=params.pal_name,
        pal_gender=params.pal_gender,
        elder_name=params.elder,
        elder_gender=params.elder_gender,
        trait=params.trait,
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

    for params in CURATED:
        ok_py = valid_combo(params.animal, params.missing, params.guess, params.repair)
        ok_asp = asp_story_ok(params)
        if ok_py != ok_asp:
            rc = 1
            print(f"MISMATCH in story_ok for curated params: {params}")
            break
    else:
        print(f"OK: ASP story_ok agrees on {len(CURATED)} curated scenarios.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(7))
        smoke_params.seed = 7
        sample = generate(smoke_params)
        if not sample.story or "forty" not in sample.story:
            raise StoryError("(Smoke test failed: story missing or did not include required word 'forty'.)")
        emit(sample, trace=False, qa=False, header="-- smoke test sample --")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, missing, guess, repair) combos:\n")
        for animal_id, missing_id, guess_id, repair_id in combos:
            print(f"  {animal_id:6} {missing_id:7} {guess_id:9} {repair_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.pal_name}: {p.animal} / {p.missing} / {p.guess} / {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
