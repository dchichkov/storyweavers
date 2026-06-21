#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ethnic_inner_monologue_cautionary_curiosity_rhyming_story.py
=======================================================================================

A standalone storyworld about a curious child, a bowl of strong color, and a
special family costume laid out for a celebration. The prose aims for a simple
rhyming-story feel, while the simulation underneath tracks physical state
(spills, stains, cleanup) and emotional state (curiosity, worry, relief, pride).

The seed requested the word "ethnic" plus the instruments Inner Monologue,
Cautionary, and Curiosity. This world uses them concretely:

* Curiosity: a child wants to add "one more pretty mark" to a special outfit.
* Inner Monologue: the child thinks in little private rhyming thoughts.
* Cautionary: a warning is grounded in stain risk and whether cleanup can work.

Run it
------
python storyworlds/worlds/gpt-5.4/ethnic_inner_monologue_cautionary_curiosity_rhyming_story.py
python storyworlds/worlds/gpt-5.4/ethnic_inner_monologue_cautionary_curiosity_rhyming_story.py --all
python storyworlds/worlds/gpt-5.4/ethnic_inner_monologue_cautionary_curiosity_rhyming_story.py --verify
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
CURIOSITY_INIT = 5.0
CAREFUL_TRAITS = {"careful", "patient", "steady", "wise"}


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
    absorbent: bool = False
    delicate: bool = False
    keepsake: bool = False
    stain_power: int = 0
    washable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "grandmother", "sister", "cousin_girl"}
        male = {"boy", "man", "father", "uncle", "grandfather", "brother", "cousin_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Celebration:
    id: str
    place: str
    event: str
    music: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ColorMedium:
    id: str
    label: str
    phrase: str
    color: str
    source: str
    stain_power: int
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Garment:
    id: str
    label: str
    phrase: str
    fabric: str
    absorbent: bool
    delicate: bool
    keepsake: bool
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeSurface:
    id: str
    label: str
    phrase: str
    ending_line: str
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


def _r_stain(world: World) -> list[str]:
    out: list[str] = []
    bowl = world.get("bowl")
    cloth = world.get("garment")
    if bowl.meters["spilled"] < THRESHOLD:
        return out
    if not cloth.absorbent:
        return out
    sig = ("stain", bowl.id, cloth.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cloth.meters["stained"] += 1
    cloth.meters["severity"] += bowl.stain_power + cloth.attrs.get("severity", 0)
    out.append("__stain__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    cloth = world.get("garment")
    if cloth.meters["stained"] < THRESHOLD:
        return out
    sig = ("worry", cloth.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper = world.get("helper")
    child = world.get("child")
    helper.memes["worry"] += 1
    child.memes["guilt"] += 1
    out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="stain", tag="physical", apply=_r_stain),
    Rule(name="worry", tag="emotional", apply=_r_worry),
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


def stain_risk(medium: ColorMedium, garment: Garment) -> bool:
    return garment.absorbent and medium.stain_power > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def stain_severity(medium: ColorMedium, garment: Garment) -> int:
    return medium.stain_power + garment.severity


def stain_saved(response: Response, medium: ColorMedium, garment: Garment) -> bool:
    return response.power >= stain_severity(medium, garment)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, child_age: int, helper_age: int, trait: str) -> bool:
    elder = relation in {"siblings", "cousins"} and helper_age > child_age
    authority = initial_care(trait) + (3.0 if elder else 0.0)
    return elder and authority > CURIOSITY_INIT


def _do_spill(world: World, narrate: bool = True) -> None:
    bowl = world.get("bowl")
    bowl.meters["spilled"] += 1
    propagate(world, narrate=narrate)


def predict_spill(world: World) -> dict:
    sim = world.copy()
    _do_spill(sim, narrate=False)
    cloth = sim.get("garment")
    return {
        "stained": cloth.meters["stained"] >= THRESHOLD,
        "severity": int(cloth.meters["severity"]),
    }


def opening(world: World, child: Entity, helper: Entity, celebration: Celebration, garment: Garment) -> None:
    child.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"In {celebration.place}, drums gave a {celebration.music} hum, and "
        f"{child.id} watched celebration things come one by one."
    )
    world.say(
        f"On the bed lay {garment.phrase} for {celebration.event}, with careful folds and shining thread. "
        f'"It is part of our family\'s ethnic celebration," {helper.id} said.'
    )


def curiosity(world: World, child: Entity, medium: ColorMedium, garment: Garment) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Beside it sat {medium.phrase}, bright as a little sun. "
        f"{child.id} leaned close and wondered if one more swirl might make the cloth even prettier."
    )
    world.say(
        f'"If I add one tiny line, it may look grand and fine," '
        f"{child.id} thought. "
        f'"Just one small touch, then I am done; a secret helper, not a naughty one."'
    )


def warning(world: World, helper: Entity, child: Entity, medium: ColorMedium, garment: Garment) -> None:
    pred = predict_spill(world)
    child.memes["hesitation"] += 1
    world.facts["predicted_stained"] = pred["stained"]
    world.facts["predicted_severity"] = pred["severity"]
    world.say(
        f'{helper.id} saw those curious eyes and gently shook {helper.pronoun("possessive")} head. '
        f'"Not that bowl for {garment.label}," {helper.pronoun()} said. '
        f'"{medium.warning} Once it sinks into {garment.fabric}, it does not leave in a hurry."'
    )
    world.say(
        f'"I only want to see, I only want to know," {child.id} thought, '
        f'"but curious hands can start a stain and make the trouble grow."'
    )


def back_down(world: World, child: Entity, helper: Entity, surface: SafeSurface) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{child.id} tucked both hands behind {child.pronoun('possessive')} back and took one careful breath. "
        f"The warning settled in."
    )
    world.say(
        f'"I can be curious and careful too," {child.id} thought. '
        f'"I do not have to touch the special thing to learn what colors do."'
    )
    world.say(
        f'So {helper.id} slid over {surface.phrase}, and together they traced loops and flowers there instead.'
    )


def defy(world: World, child: Entity, medium: ColorMedium) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Just one quick try before the grown-ups spy," {child.id} thought. '
        f"Curiosity hurried faster than caution, and {child.pronoun()} reached for the {medium.label}."
    )


def spill(world: World, child: Entity, medium: ColorMedium, garment: Garment) -> None:
    _do_spill(world, narrate=True)
    world.say(
        f"But the bowl tipped with a soft, sad plop, and {medium.color} color kissed {garment.label} drop by drop."
    )
    world.say(
        f'"Oh no," {child.id} thought, '
        f'"my tiny try has made a blot; a little secret is not little now, and this is not what I had sought."'
    )


def rescue(world: World, helper: Entity, response: Response, garment: Garment) -> None:
    cloth = world.get("garment")
    cloth.meters["stained"] = 0.0
    cloth.meters["saved"] += 1
    body = response.text.format(garment=garment.label)
    world.say(
        f"{helper.id} moved quickly and {body}. The bright mark faded before it could settle deep."
    )


def rescue_fail(world: World, helper: Entity, response: Response, garment: Garment) -> None:
    cloth = world.get("garment")
    cloth.meters["ruined"] += 1
    body = response.fail.format(garment=garment.label)
    world.say(
        f"{helper.id} tried to help and {body}. But the color stayed like a hard little shadow."
    )


def lesson(world: World, helper: Entity, child: Entity, medium: ColorMedium, garment: Garment, saved: bool) -> None:
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    helper.memes["love"] += 1
    if saved:
        world.say(
            f"{helper.id} knelt close and hugged {child.pronoun('object')}. "
            f'"I am glad you stayed and told the truth," {helper.pronoun()} said. '
            f'"Strong color is for guided hands, not secret plans."'
        )
    else:
        world.say(
            f"{helper.id} sat beside {child.id} and held {child.pronoun('possessive')} hand. "
            f'"We cannot undo every mark," {helper.pronoun()} said softly, '
            f'"but we can learn from this one."'
        )
    world.say(
        f'"Next time I will ask before I try," {child.id} thought. '
        f'"Curious minds can still be wise, and special things deserve gentle eyes."'
    )


def safe_ending(world: World, child: Entity, helper: Entity, celebration: Celebration, surface: SafeSurface, garment: Garment, saved: bool) -> None:
    child.memes["pride"] += 1
    helper.memes["pride"] += 1
    if saved:
        world.say(
            f"Soon {garment.phrase} was ready again, and {child.id} helped in a safer lane."
        )
    else:
        world.say(
            f"The family chose another neat outfit for the dance, and kindness gave the evening room to mend."
        )
    world.say(
        f"On {surface.label}, colors curled in happy light, and {celebration.ending}."
    )


def tell(
    celebration: Celebration,
    medium: ColorMedium,
    garment_cfg: Garment,
    surface: SafeSurface,
    response: Response,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_name: str = "Auntie",
    helper_type: str = "aunt",
    trait: str = "careful",
    relation: str = "cousins",
    child_age: int = 5,
    helper_age: int = 8,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            age=child_age,
            traits=["curious"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            age=helper_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    bowl = world.add(
        Entity(
            id="bowl",
            type="medium",
            label=medium.label,
            phrase=medium.phrase,
            role="medium",
            stain_power=medium.stain_power,
            washable=False,
            tags=set(medium.tags),
        )
    )
    garment = world.add(
        Entity(
            id="garment",
            type="garment",
            label=garment_cfg.label,
            phrase=garment_cfg.phrase,
            role="garment",
            absorbent=garment_cfg.absorbent,
            delicate=garment_cfg.delicate,
            keepsake=garment_cfg.keepsake,
            attrs={"fabric": garment_cfg.fabric, "severity": garment_cfg.severity},
            tags=set(garment_cfg.tags),
        )
    )
    pad = world.add(
        Entity(
            id="surface",
            type="surface",
            label=surface.label,
            phrase=surface.phrase,
            role="surface",
            washable=True,
            tags=set(surface.tags),
        )
    )

    child.memes["curiosity"] = CURIOSITY_INIT
    helper.memes["care"] = initial_care(trait)

    opening(world, child, helper, celebration, garment_cfg)
    curiosity(world, child, medium, garment_cfg)

    world.para()
    warning(world, helper, child, medium, garment_cfg)
    averted = would_avert(relation, child_age, helper_age, trait)

    if averted:
        back_down(world, child, helper, surface)
        saved = True
        outcome = "averted"
    else:
        defy(world, child, medium)
        world.para()
        spill(world, child, medium, garment_cfg)
        saved = stain_saved(response, medium, garment_cfg)
        world.para()
        if saved:
            rescue(world, helper, response, garment_cfg)
            lesson(world, helper, child, medium, garment_cfg, True)
            outcome = "saved"
        else:
            rescue_fail(world, helper, response, garment_cfg)
            lesson(world, helper, child, medium, garment_cfg, False)
            outcome = "marked"

    world.para()
    safe_ending(world, child, helper, celebration, surface, garment_cfg, saved)

    world.facts.update(
        child=child,
        helper=helper,
        celebration=celebration,
        medium=medium,
        garment_cfg=garment_cfg,
        garment=garment,
        surface=surface,
        response=response,
        relation=relation,
        averted=averted,
        saved=saved,
        outcome=outcome,
        stained=garment.meters["stained"] >= THRESHOLD or garment.meters["ruined"] >= THRESHOLD,
    )
    return world


CELEBRATIONS = {
    "fair": Celebration(
        id="fair",
        place="a small family room before the neighborhood fair",
        event="the evening fair",
        music="dum-da-dum",
        ending="soon the room rang with music, soft feet, and proud smiles",
        tags={"festival", "music"},
    ),
    "parade": Celebration(
        id="parade",
        place="a bright bedroom before the street parade",
        event="the parade",
        music="tap-tap-clap",
        ending="soon the hallway sparkled with steps, claps, and grins",
        tags={"festival", "music"},
    ),
    "dance": Celebration(
        id="dance",
        place="a warm house before the family dance",
        event="the dance",
        music="swish-swish-drum",
        ending="soon the house filled with turns, laughter, and gentle drums",
        tags={"festival", "music"},
    ),
}

MEDIA = {
    "turmeric": ColorMedium(
        id="turmeric",
        label="turmeric bowl",
        phrase="a bowl of turmeric paste",
        color="golden",
        source="spice",
        stain_power=2,
        warning="Turmeric leaves a yellow stain",
        tags={"turmeric", "stain"},
    ),
    "berry": ColorMedium(
        id="berry",
        label="berry dye",
        phrase="a cup of berry dye",
        color="purple",
        source="berries",
        stain_power=2,
        warning="Berry dye stains deep purple",
        tags={"dye", "stain"},
    ),
    "henna": ColorMedium(
        id="henna",
        label="henna paste",
        phrase="a cone and bowl of henna paste",
        color="reddish-brown",
        source="henna",
        stain_power=3,
        warning="Henna leaves a dark mark that lingers",
        tags={"henna", "stain"},
    ),
}

GARMENTS = {
    "shawl": Garment(
        id="shawl",
        label="shawl",
        phrase="a soft family shawl",
        fabric="cotton",
        absorbent=True,
        delicate=False,
        keepsake=True,
        severity=1,
        tags={"shawl", "cloth"},
    ),
    "sash": Garment(
        id="sash",
        label="sash",
        phrase="a bright woven sash",
        fabric="cotton",
        absorbent=True,
        delicate=False,
        keepsake=True,
        severity=1,
        tags={"sash", "cloth"},
    ),
    "silk_vest": Garment(
        id="silk_vest",
        label="silk vest",
        phrase="a tiny silk vest with stitched stars",
        fabric="silk",
        absorbent=True,
        delicate=True,
        keepsake=True,
        severity=2,
        tags={"silk", "cloth"},
    ),
    "bead_belt": Garment(
        id="bead_belt",
        label="bead belt",
        phrase="a bead belt with shiny loops",
        fabric="beads and cord",
        absorbent=False,
        delicate=False,
        keepsake=True,
        severity=0,
        tags={"beads"},
    ),
}

SURFACES = {
    "paper": SafeSurface(
        id="paper",
        label="paper",
        phrase="a big sheet of practice paper",
        ending_line="paper bloomed with winding lines",
        tags={"paper"},
    ),
    "cloth": SafeSurface(
        id="cloth",
        label="practice cloth",
        phrase="a square of practice cloth",
        ending_line="the practice cloth wore the brave little swirls instead",
        tags={"practice_cloth"},
    ),
    "card": SafeSurface(
        id="card",
        label="card",
        phrase="a thick little card for trying patterns",
        ending_line="the little card shone with careful curls and dots",
        tags={"paper"},
    ),
}

RESPONSES = {
    "rinse_blot": Response(
        id="rinse_blot",
        sense=3,
        power=4,
        text="lifted the {garment} at once, rinsed the fresh spot with cool water, and blotted it with a clean towel",
        fail="rinsed and blotted the {garment} quickly",
        qa_text="rinsed the fresh spot with cool water and blotted it clean",
        tags={"cleaning", "water"},
    ),
    "dab_soap": Response(
        id="dab_soap",
        sense=2,
        power=3,
        text="dabbed the mark with gentle soap and cool water before the color could settle",
        fail="dabbed the {garment} with soap and water",
        qa_text="dabbed the fresh stain with gentle soap and cool water",
        tags={"cleaning", "soap"},
    ),
    "rub_hard": Response(
        id="rub_hard",
        sense=1,
        power=1,
        text="rubbed the cloth hard with a dry towel",
        fail="rubbed the {garment} hard with a dry towel",
        qa_text="rubbed it hard with a dry towel",
        tags={"cleaning"},
    ),
}

GIRL_NAMES = ["Mina", "Asha", "Lila", "Zoya", "Nila", "Rani", "Sara", "Leela"]
BOY_NAMES = ["Omar", "Ravi", "Imran", "Niko", "Arun", "Samir", "Noah", "Eli"]
HELPER_NAMES = ["Auntie", "Cousin Reva", "Cousin Amir", "Grandma", "Mama"]
TRAITS = ["careful", "patient", "steady", "wise", "kind", "gentle"]


@dataclass
class StoryParams:
    celebration: str
    medium: str
    garment: str
    surface: str
    response: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    trait: str
    relation: str
    child_age: int
    helper_age: int
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for celebration in CELEBRATIONS:
        for medium_id, medium in MEDIA.items():
            for garment_id, garment in GARMENTS.items():
                if stain_risk(medium, garment):
                    combos.append((celebration, medium_id, garment_id))
    return combos


KNOWLEDGE = {
    "turmeric": [
        (
            "What is turmeric?",
            "Turmeric is a bright yellow spice. It can color food, hands, and cloth very strongly.",
        )
    ],
    "henna": [
        (
            "What is henna?",
            "Henna is a plant paste used to make dark orange-brown designs. It leaves a mark that can last for a while.",
        )
    ],
    "dye": [
        (
            "What does dye do?",
            "Dye adds color to cloth or other things. That is why it can also make stains if it spills where it should not.",
        )
    ],
    "stain": [
        (
            "Why are stains hard to remove?",
            "A stain happens when color sinks into a material. The deeper it soaks in, the harder it is to wash away.",
        )
    ],
    "silk": [
        (
            "Why must silk be treated gently?",
            "Silk is a soft, delicate fabric. Strong rubbing can hurt it, so gentle cleaning is better.",
        )
    ],
    "paper": [
        (
            "Why is practice paper a good place to test colors?",
            "Practice paper is safe to mark on. It lets you try ideas without hurting something special.",
        )
    ],
    "practice_cloth": [
        (
            "What is a practice cloth for?",
            "A practice cloth is a spare piece of fabric for trying patterns first. It helps you learn before you touch the real thing.",
        )
    ],
    "cleaning": [
        (
            "Why is it smart to clean a spill quickly?",
            "A fresh spill is easier to lift before it sinks in deeply. Fast help can stop a small accident from becoming a big stain.",
        )
    ],
    "festival": [
        (
            "What is a family celebration outfit for?",
            "A celebration outfit is worn for a special event. Families often care for it gently because it can hold memories and tradition.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "festival",
    "turmeric",
    "henna",
    "dye",
    "stain",
    "silk",
    "paper",
    "practice_cloth",
    "cleaning",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    celebration = f["celebration"]
    medium = f["medium"]
    garment = f["garment_cfg"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the word "ethnic" and shows a curious child near {medium.label}.',
        f"Tell a gentle cautionary story where {child.id} is curious about coloring a special {garment.label} before {celebration.event}, and {helper.id} helps turn that curiosity into a safer choice.",
        f"Write a simple story with inner monologue, light rhyme, and a lesson about asking first when something special might be stained.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    medium = f["medium"]
    garment = f["garment_cfg"]
    surface = f["surface"]
    response = f["response"]
    celebration = f["celebration"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and {helper.id}, who was helping get ready for {celebration.event}. The story also centers on a special {garment.label} laid out for the family celebration.",
        ),
        (
            f"Why was {child.id} interested in the {medium.label}?",
            f"{child.id} thought the bright color might make the {garment.label} even prettier. That curious idea is what started the trouble in the story.",
        ),
        (
            f"Why did {helper.id} warn {child.id} not to use the {medium.label} on the {garment.label}?",
            f"{helper.id} knew that {medium.warning.lower()}. Because the {garment.label} was special and made of {garment.fabric}, a spill could leave a mark that would be hard to remove.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed after the warning?",
                f"{child.id} stopped before touching the special {garment.label}. Then the color was moved to {surface.phrase}, so curiosity became safe practice instead of a stain.",
            )
        )
    elif outcome == "saved":
        qa.append(
            (
                f"What happened when the color spilled?",
                f"The bowl tipped and some color landed on the {garment.label}. {helper.id} acted fast and {response.qa_text}, which kept the mark from settling deep.",
            )
        )
        qa.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned to ask before trying something on a special object. The lesson came from seeing how one tiny secret choice could have become a lasting stain.",
            )
        )
    else:
        qa.append(
            (
                f"Was the {garment.label} saved?",
                f"No. {helper.id} tried to help, but the mark stayed. That made the warning feel real, because some mistakes on special things cannot be fully undone.",
            )
        )
        qa.append(
            (
                f"How did the story still end gently?",
                f"The family chose kindness and another outfit for the celebration. {child.id} still got to learn and help safely on {surface.label}, even after the mistake.",
            )
        )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["celebration"].tags) | set(f["medium"].tags) | set(f["surface"].tags)
    tags |= set(f["response"].tags)
    tags |= set(f["garment_cfg"].tags)
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(x[0] for x in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(M, G) :- medium(M), garment(G), stain_power(M, P), P > 0, absorbent(G).
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(C, M, G) :- celebration(C), hazard(M, G).

care_now(T, 5) :- careful_trait(T).
care_now(T, 3) :- trait(T), not careful_trait(T).

elder_helper :- relation(siblings), helper_age(HA), child_age(CA), HA > CA.
elder_helper :- relation(cousins), helper_age(HA), child_age(CA), HA > CA.

authority(V + 3) :- care_now(T, V), elder_helper, trait(T).
authority(V) :- care_now(T, V), not elder_helper, trait(T).

averted :- elder_helper, authority(A), curiosity_init(C), A > C.

severity(SP + GS) :- chosen_medium(M), stain_power(M, SP), chosen_garment(G), garment_severity(G, GS).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(saved) :- not averted, contained.
outcome(marked) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CELEBRATIONS:
        lines.append(asp.fact("celebration", cid))
    for mid, medium in MEDIA.items():
        lines.append(asp.fact("medium", mid))
        lines.append(asp.fact("stain_power", mid, medium.stain_power))
    for gid, garment in GARMENTS.items():
        lines.append(asp.fact("garment", gid))
        lines.append(asp.fact("garment_severity", gid, garment.severity))
        if garment.absorbent:
            lines.append(asp.fact("absorbent", gid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_medium", params.medium),
            asp.fact("chosen_garment", params.garment),
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("child_age", params.child_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.child_age, params.helper_age, params.trait):
        return "averted"
    if stain_saved(RESPONSES[params.response], MEDIA[params.medium], GARMENTS[params.garment]):
        return "saved"
    return "marked"


def explain_rejection(medium: ColorMedium, garment: Garment) -> str:
    if not garment.absorbent:
        return (
            f"(No story: {garment.phrase} does not soak up spilled color the way cloth does, "
            f"so there is no honest stain problem. Pick a cloth item like a shawl, sash, or silk vest.)"
        )
    return (
        f"(No story: {medium.label} would not create a meaningful stain risk on {garment.label}.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is below the common-sense threshold "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


CURATED = [
    StoryParams(
        celebration="fair",
        medium="turmeric",
        garment="shawl",
        surface="paper",
        response="rinse_blot",
        child_name="Mina",
        child_type="girl",
        helper_name="Auntie",
        helper_type="aunt",
        trait="careful",
        relation="cousins",
        child_age=5,
        helper_age=8,
    ),
    StoryParams(
        celebration="parade",
        medium="berry",
        garment="sash",
        surface="cloth",
        response="dab_soap",
        child_name="Ravi",
        child_type="boy",
        helper_name="Grandma",
        helper_type="grandmother",
        trait="patient",
        relation="siblings",
        child_age=4,
        helper_age=7,
    ),
    StoryParams(
        celebration="dance",
        medium="henna",
        garment="silk_vest",
        surface="card",
        response="dab_soap",
        child_name="Asha",
        child_type="girl",
        helper_name="Mama",
        helper_type="mother",
        trait="gentle",
        relation="friends",
        child_age=6,
        helper_age=6,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a curious child, a special outfit, and a stain warning. Unspecified choices are seeded and randomized."
    )
    ap.add_argument("--celebration", choices=CELEBRATIONS)
    ap.add_argument("--medium", choices=MEDIA)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    child_type = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    return name, child_type


def _pick_helper(rng: random.Random, child_type: str) -> tuple[str, str]:
    choice = rng.choice(
        [
            ("Auntie", "aunt"),
            ("Grandma", "grandmother"),
            ("Mama", "mother"),
            ("Cousin Reva", "cousin_girl"),
            ("Cousin Amir", "cousin_boy"),
        ]
    )
    return choice


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.medium and args.garment:
        medium = MEDIA[args.medium]
        garment = GARMENTS[args.garment]
        if not stain_risk(medium, garment):
            raise StoryError(explain_rejection(medium, garment))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.celebration is None or combo[0] == args.celebration)
        and (args.medium is None or combo[1] == args.medium)
        and (args.garment is None or combo[2] == args.garment)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    celebration, medium, garment = rng.choice(sorted(combos))
    surface = args.surface or rng.choice(sorted(SURFACES))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_type = _pick_child(rng)
    helper_name, helper_type = _pick_helper(rng, child_type)
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "cousins", "friends"])
    child_age = rng.randint(4, 6)
    helper_age = rng.randint(5, 9)
    return StoryParams(
        celebration=celebration,
        medium=medium,
        garment=garment,
        surface=surface,
        response=response,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
        relation=relation,
        child_age=child_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        celebration = CELEBRATIONS[params.celebration]
        medium = MEDIA[params.medium]
        garment = GARMENTS[params.garment]
        surface = SURFACES[params.surface]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(Invalid story parameter: {exc.args[0]})") from exc

    if not stain_risk(medium, garment):
        raise StoryError(explain_rejection(medium, garment))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        celebration=celebration,
        medium=medium,
        garment_cfg=garment,
        surface=surface,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
        relation=params.relation,
        child_age=params.child_age,
        helper_age=params.helper_age,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: gate matches valid_combos() ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in clingo:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in python:", sorted(py_combos - asp_combos))

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (celebration, medium, garment) combos:\n")
        for celebration, medium, garment in combos:
            print(f"  {celebration:10} {medium:10} {garment}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name}: {p.medium} near {p.garment} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
