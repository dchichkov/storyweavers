#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wallaby_shrink_ouch_flashback_nursery_rhyme.py
========================================================================

A small story world for a nursery-rhyme-like tale about a wallaby, a wool
garment that might shrink, and a remembered rhyme that changes what happens.

The world model is deliberately narrow:

* A little wallaby gets a washable mess on a favorite garment.
* The grown-up feels tempted to hurry with hot water.
* A flashback recalls an older rhyme: wool should be washed cool and gently.
* If the warning is heeded, the garment stays soft and roomy.
* If the warning is ignored, the wool shrinks and the wallaby says "ouch."

The reasonableness gate is also narrow: this world only tells stories where
"shrink" is a real possibility, so garments that do not plausibly shrink in a
hot wash are rejected.

Run it
------
    python storyworlds/worlds/gpt-5.4/wallaby_shrink_ouch_flashback_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/wallaby_shrink_ouch_flashback_nursery_rhyme.py --garment scarf
    python storyworlds/worlds/gpt-5.4/wallaby_shrink_ouch_flashback_nursery_rhyme.py --choice rush
    python storyworlds/worlds/gpt-5.4/wallaby_shrink_ouch_flashback_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/wallaby_shrink_ouch_flashback_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4/wallaby_shrink_ouch_flashback_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "gran", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "gran": "gran"}.get(self.type, self.type)


@dataclass
class Tune:
    id: str
    opening: str
    room: str
    beat: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mess:
    id: str
    label: str
    splash: str
    wash_word: str
    stain_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Garment:
    id: str
    label: str
    phrase: str
    wear_line: str
    tight_line: str
    material: str = "wool"
    shrinkable: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    title: str
    flashback_from: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    tune: str
    mess: str
    garment: str
    helper: str
    choice: str
    name: str
    gender: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

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


def _r_shrink(world: World) -> list[str]:
    out: list[str] = []
    garment = world.get("garment")
    if garment.meters["heat"] < THRESHOLD:
        return out
    if garment.attrs.get("material") != "wool":
        return out
    sig = ("shrink", garment.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    garment.meters["shrunk"] += 1
    garment.meters["small"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    out.append("__shrunk__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="shrink", tag="physical", apply=_r_shrink),
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


TUNES = {
    "moon": Tune(
        id="moon",
        opening="Under a spoon-bright moon sang a sleepy room,",
        room="the window made a silver square on the floor",
        beat="tap-a-toe, sway-a-slow",
        closing="So the moon looked in, and the rhyme tucked in too.",
        tags={"moon", "rhyme"},
    ),
    "garden": Tune(
        id="garden",
        opening="In a dew-bright garden by the rosemary gate,",
        room="a basket sat beside the steps",
        beat="skip-a-soft, hop-a-light",
        closing="So the rosemary nodded, and the rhyme ended right.",
        tags={"garden", "rhyme"},
    ),
    "nursery": Tune(
        id="nursery",
        opening="In a hush-a-by nursery with a lantern low,",
        room="the rocking chair creaked a little by the wall",
        beat="rock-a-round, hum-a-low",
        closing="So the lantern glowed, and the rhyme grew slow.",
        tags={"nursery", "rhyme"},
    ),
}

MESSES = {
    "berry": Mess(
        id="berry",
        label="berry jam",
        splash="a purple berry blot",
        wash_word="rinse",
        stain_word="sticky and purple",
        tags={"berries", "washing"},
    ),
    "mud": Mess(
        id="mud",
        label="garden mud",
        splash="a brown muddy smudge",
        wash_word="wash",
        stain_word="muddy",
        tags={"mud", "washing"},
    ),
    "honey": Mess(
        id="honey",
        label="honey",
        splash="a gold sticky drip",
        wash_word="clean",
        stain_word="sticky",
        tags={"honey", "washing"},
    ),
}

GARMENTS = {
    "jumper": Garment(
        id="jumper",
        label="jumper",
        phrase="a soft wool jumper",
        wear_line="The little wallaby loved to bounce in that soft wool jumper.",
        tight_line="When the wallaby tried it on again, the jumper pinched under the arms.",
        material="wool",
        shrinkable=True,
        plural=False,
        tags={"jumper", "wool"},
    ),
    "bonnet": Garment(
        id="bonnet",
        label="bonnet",
        phrase="a blue wool bonnet",
        wear_line="The little wallaby loved to tip that blue wool bonnet over one bright ear.",
        tight_line="When the wallaby tried it on again, the bonnet tugged too tight at the chin.",
        material="wool",
        shrinkable=True,
        plural=False,
        tags={"bonnet", "wool"},
    ),
    "mittens": Garment(
        id="mittens",
        label="mittens",
        phrase="a pair of wool mittens",
        wear_line="The little wallaby loved to clap in that pair of wool mittens.",
        tight_line="When the wallaby tried them on again, the mittens squeezed the paws.",
        material="wool",
        shrinkable=True,
        plural=True,
        tags={"mittens", "wool"},
    ),
    "scarf": Garment(
        id="scarf",
        label="scarf",
        phrase="a cotton scarf",
        wear_line="The little wallaby liked to swish that cotton scarf in a breeze.",
        tight_line="The scarf did not grow tight at all.",
        material="cotton",
        shrinkable=False,
        plural=False,
        tags={"scarf", "cotton"},
    ),
}

HELPERS = {
    "mother": HelperCfg(
        id="mother",
        type="mother",
        title="mom",
        flashback_from="her own gran",
        tags={"mother", "grownup"},
    ),
    "father": HelperCfg(
        id="father",
        type="father",
        title="dad",
        flashback_from="his own gran",
        tags={"father", "grownup"},
    ),
    "gran": HelperCfg(
        id="gran",
        type="gran",
        title="gran",
        flashback_from="an even older gran",
        tags={"gran", "grownup"},
    ),
}

CHOICES = {
    "remember": "heed the flashback and wash cool",
    "rush": "ignore the flashback and hurry with hot water",
}

GIRL_NAMES = ["Willa", "Mimi", "Tansy", "Lottie", "Poppy", "Nell"]
BOY_NAMES = ["Wally", "Joey", "Toby", "Pip", "Rory", "Bram"]


def garment_can_shrink(garment: Garment) -> bool:
    return garment.shrinkable and garment.material == "wool"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for tune in TUNES:
        for mess in MESSES:
            for gid, garment in GARMENTS.items():
                if garment_can_shrink(garment):
                    combos.append((tune, mess, gid))
    return combos


def predict_hot_wash(world: World) -> dict:
    sim = world.copy()
    garment = sim.get("garment")
    garment.meters["wet"] += 1
    garment.meters["heat"] += 1
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    if garment.meters["shrunk"] >= THRESHOLD:
        hero.meters["ouch"] += 1
    return {
        "shrinks": garment.meters["shrunk"] >= THRESHOLD,
        "ouch": hero.meters["ouch"] >= THRESHOLD,
    }


def introduce(world: World, tune: Tune, hero: Entity, helper: Entity, garment: Entity) -> None:
    world.say(
        f"{tune.opening} {hero.id} the wallaby twitched {hero.pronoun('possessive')} "
        f"little nose while {helper.label_word} folded {garment.phrase}."
    )
    world.say(f"{tune.room}, and all the room kept {tune.beat}.")
    world.say(garment.attrs["wear_line"])


def make_mess(world: World, hero: Entity, mess: Mess, garment: Entity) -> None:
    hero.memes["joy"] += 1
    garment.meters["dirty"] += 1
    garment.meters[mess.id] += 1
    world.say(
        f"But one quick bounce, one turn, one twirl, and {mess.splash} "
        f"landed on the {garment.label}."
    )
    world.say(
        f'"Oh dear," said {hero.id}, peeping down. "My {garment.label} is {mess.stain_word}."'
    )


def worry(world: World, hero: Entity, helper: Entity, mess: Mess, garment: Entity) -> None:
    helper.memes["care"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'{helper.label_word.capitalize()} lifted the {garment.label} and said, '
        f'"A quick {mess.wash_word} will help, little wallaby."'
    )
    world.say(
        f"By the basin sat a kettle of hot water, puffing as if hurry were the cleverest thing."
    )


def flashback(world: World, hero: Entity, helper: Entity, garment: Entity) -> None:
    pred = predict_hot_wash(world)
    world.facts["predicted_shrink"] = pred["shrinks"]
    world.facts["predicted_ouch"] = pred["ouch"]
    helper.memes["memory"] += 1
    world.say(
        f"Then a flashback fluttered through {helper.label_word}'s mind, light as a moth in lamplight."
    )
    world.say(
        f"{helper.pronoun('possessive').capitalize()} remembered {helper.attrs['flashback_from']} singing, "
        f'"Cool bowl, slow roll; hot bowl, small wool."'
    )
    if pred["shrinks"] and pred["ouch"]:
        world.say(
            f"In that remembered picture, the little {garment.label} did shrink, "
            f"and a wallaby tugged it on and cried, \"Ouch, ouch, too small!\""
        )


def choose_remember(world: World, hero: Entity, helper: Entity, garment: Entity) -> None:
    hero.memes["trust"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{helper.label_word.capitalize()} set the hot kettle far away. '
        f'"No hurry for wool," {helper.pronoun()} said. "We will be kind to it."'
    )
    garment.meters["wet"] += 1
    garment.meters["cool"] += 1
    garment.meters["clean"] += 1
    world.say(
        f"So into a cool bowl went the {garment.label}, swish-a-gentle, press-a-light."
    )
    world.say(
        f"{helper.label_word.capitalize()} laid it flat on a towel, and the wool kept its soft old shape."
    )


def choose_rush(world: World, hero: Entity, helper: Entity, garment: Entity) -> None:
    helper.memes["hurry"] += 1
    world.say(
        f'But the kettle hissed, and hurry won. "{helper.pronoun("subject").capitalize()} will be quick," '
        f"said {helper.label_word}, reaching for the hot water."
    )
    garment.meters["wet"] += 1
    garment.meters["heat"] += 1
    garment.meters["clean"] += 1
    propagate(world, narrate=False)
    if garment.meters["shrunk"] >= THRESHOLD:
        hero.meters["ouch"] += 1
    world.say(
        f"The stain came out, but the wool drew in, smaller and snugger than before."
    )


def ending_safe(world: World, tune: Tune, hero: Entity, helper: Entity, garment: Entity) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"When the {garment.label} dried, {hero.id} slipped it on with one happy hop."
    )
    world.say(
        f'No pinch, no squeeze, no "ouch" at all -- just a neat little wallaby and a relieved {helper.label_word}.'
    )
    world.say(
        f"Then {hero.id} danced past the towel rack, soft and springy as before. {tune.closing}"
    )


def ending_shrunk(world: World, tune: Tune, hero: Entity, helper: Entity, garment: Entity) -> None:
    hero.memes["sad"] += 1
    helper.memes["regret"] += 1
    world.say(garment.attrs["tight_line"])
    world.say(
        f'"Ouch," said {hero.id}, with a startled little hop. The flashback rhyme had been right.'
    )
    world.say(
        f"{helper.label_word.capitalize()} hugged the wallaby close and promised, "
        f'"Next time, cool bowl and slow hands for wool."'
    )
    world.say(
        f"That evening {helper.pronoun()} began a roomier new knit, while the shrunken {garment.label} "
        f"rested on a shelf as a small, true reminder. {tune.closing}"
    )


def tell(
    tune: Tune,
    mess: Mess,
    garment_cfg: Garment,
    helper_cfg: HelperCfg,
    choice: str,
    name: str = "Willa",
    gender: str = "girl",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label="the wallaby",
        phrase="the wallaby",
        role="hero",
        tags={"wallaby"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        label="the helper",
        phrase="the helper",
        role="helper",
        attrs={"flashback_from": helper_cfg.flashback_from},
        tags=set(helper_cfg.tags),
    ))
    garment = world.add(Entity(
        id="garment",
        kind="thing",
        type="garment",
        label=garment_cfg.label,
        phrase=garment_cfg.phrase,
        attrs={
            "material": garment_cfg.material,
            "wear_line": garment_cfg.wear_line,
            "tight_line": garment_cfg.tight_line,
            "plural": garment_cfg.plural,
        },
        tags=set(garment_cfg.tags),
    ))

    introduce(world, tune, hero, helper, garment)
    world.para()
    make_mess(world, hero, mess, garment)
    worry(world, hero, helper, mess, garment)
    world.para()
    flashback(world, hero, helper, garment)
    world.para()

    if choice == "remember":
        choose_remember(world, hero, helper, garment)
        world.para()
        ending_safe(world, tune, hero, helper, garment)
        outcome = "safe"
    else:
        choose_rush(world, hero, helper, garment)
        world.para()
        ending_shrunk(world, tune, hero, helper, garment)
        outcome = "shrunk"

    world.facts.update(
        hero=hero,
        helper=helper,
        tune=tune,
        mess=mess,
        garment_cfg=garment_cfg,
        garment=garment,
        choice=choice,
        outcome=outcome,
        flashback_used=helper.memes["memory"] >= THRESHOLD,
        said_ouch=hero.meters["ouch"] >= THRESHOLD,
        shrunk=garment.meters["shrunk"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "wallaby": [
        (
            "What is a wallaby?",
            "A wallaby is a hopping animal from Australia, a bit like a small kangaroo. Many wallabies have strong back legs and a pouch.",
        )
    ],
    "wool": [
        (
            "Why can wool shrink?",
            "Wool is made from animal fibers that can tighten up when they get hot and are rubbed around. That can make a wool garment come out smaller.",
        )
    ],
    "washing": [
        (
            "Why do some clothes need cool water?",
            "Some clothes need cool water because heat can change the fabric. Gentle washing helps them keep their shape.",
        )
    ],
    "berries": [
        (
            "Why does berry jam leave a stain?",
            "Berry jam is sticky and full of color, so it can leave dark marks on cloth. It usually needs washing to come out.",
        )
    ],
    "mud": [
        (
            "Why does mud make clothes dirty?",
            "Mud is wet dirt, so it sticks to cloth and dries there. That leaves a brown mark until someone washes it off.",
        )
    ],
    "honey": [
        (
            "Why is honey messy on clothes?",
            "Honey is sweet and sticky, so it clings to cloth instead of falling away. That is why it can make sleeves and mittens tacky.",
        )
    ],
    "rhyme": [
        (
            "What can a rhyme help you remember?",
            "A rhyme can help you remember steps because the words are easy to say again. People often use little rhymes to remember safe or careful things.",
        )
    ],
}
KNOWLEDGE_ORDER = ["wallaby", "wool", "washing", "berries", "mud", "honey", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    garment = f["garment_cfg"]
    mess = f["mess"]
    helper = f["helper"]
    outcome = f["outcome"]
    prompts = [
        'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the words "wallaby", "shrink", and "ouch".',
        f"Tell a gentle story about a wallaby named {hero.id}, a messy {garment.label}, and a grown-up who remembers a rhyme in a flashback before washing wool.",
    ]
    if outcome == "safe":
        prompts.append(
            f"Write a rhyme-like story where {helper.label_word} remembers that hot water can shrink wool, chooses a cool bowl instead, and keeps the {garment.label} from getting too small."
        )
    else:
        prompts.append(
            f"Write a nursery-rhyme cautionary tale where a flashback warning is remembered too late, the wool {garment.label} does shrink, and the wallaby says 'ouch' when trying it on."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mess = f["mess"]
    garment_cfg = f["garment_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little wallaby, and {helper.label_word}, who helps wash the favorite {garment_cfg.label}. The story follows what they do after the {garment_cfg.label} gets {mess.stain_word}.",
        ),
        (
            f"What got on the {garment_cfg.label}?",
            f"{mess.label.capitalize()} got on it and made it {mess.stain_word}. That mess is why washing the garment became part of the story.",
        ),
        (
            "What happened in the flashback?",
            f"{helper.label_word.capitalize()} remembered an older rhyme about wool: hot water can make it shrink. The flashback mattered because it showed what could happen before the washing choice was made.",
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                f"Why did the {garment_cfg.label} not shrink?",
                f"It did not shrink because {helper.label_word} listened to the remembered rhyme and used cool water instead of hot water. The gentle wash kept the wool in its old shape.",
            )
        )
        qa.append(
            (
                f"Did {hero.id} say 'ouch' at the end?",
                f"No. {hero.id} put the {garment_cfg.label} back on comfortably and did not feel any pinch. The 'ouch' only appeared in the warning picture inside the flashback, not in the real ending.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.id} say 'ouch'?",
                f"{hero.id} said 'ouch' because the wool {garment_cfg.label} had shrunk after a hot wash and felt too tight. The flashback had warned about exactly that, but hurry won anyway.",
            )
        )
        qa.append(
            (
                "How did the ending show that something changed?",
                f"The ending showed change because the old {garment_cfg.label} no longer fit the same way, and {helper.label_word} began making a roomier new one. The shrunken garment stayed on the shelf as a reminder.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"wallaby", "wool", "washing", "rhyme"}
    tags |= set(f["mess"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        tune="moon",
        mess="berry",
        garment="jumper",
        helper="mother",
        choice="remember",
        name="Willa",
        gender="girl",
    ),
    StoryParams(
        tune="garden",
        mess="mud",
        garment="bonnet",
        helper="gran",
        choice="remember",
        name="Pip",
        gender="boy",
    ),
    StoryParams(
        tune="nursery",
        mess="honey",
        garment="mittens",
        helper="father",
        choice="rush",
        name="Joey",
        gender="boy",
    ),
    StoryParams(
        tune="moon",
        mess="mud",
        garment="jumper",
        helper="gran",
        choice="rush",
        name="Mimi",
        gender="girl",
    ),
]


def explain_rejection(garment: Garment) -> str:
    return (
        f"(No story: {garment.phrase} would not meaningfully shrink in this little world. "
        f"The seed asks for a real shrink risk, so choose a wool garment like a jumper, bonnet, or mittens.)"
    )


def outcome_of(params: StoryParams) -> str:
    garment = GARMENTS[params.garment]
    if garment_can_shrink(garment) and params.choice == "rush":
        return "shrunk"
    return "safe"


ASP_RULES = r"""
shrink_risk(G) :- garment(G), material(G, wool), shrinkable(G).

valid(T, M, G) :- tune(T), mess(M), garment(G), shrink_risk(G).

hot_final :- choice(rush).
cool_final :- choice(remember).

shrinks :- chosen_garment(G), shrink_risk(G), hot_final.

outcome(shrunk) :- shrinks.
outcome(safe) :- not shrinks.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in TUNES:
        lines.append(asp.fact("tune", tid))
    for mid in MESSES:
        lines.append(asp.fact("mess", mid))
    for gid, garment in GARMENTS.items():
        lines.append(asp.fact("garment", gid))
        lines.append(asp.fact("material", gid, garment.material))
        if garment.shrinkable:
            lines.append(asp.fact("shrinkable", gid))
    for cid in CHOICES:
        lines.append(asp.fact("choice_kind", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_garment", params.garment),
            asp.fact("choice", params.choice),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = CURATED[0]
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a wallaby, a wool garment, a flashback, and the danger of shrink."
    )
    ap.add_argument("--tune", choices=TUNES)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--choice", choices=CHOICES, help="remember the rhyme or rush with hot water")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.garment and not garment_can_shrink(GARMENTS[args.garment]):
        raise StoryError(explain_rejection(GARMENTS[args.garment]))

    combos = [
        c for c in valid_combos()
        if (args.tune is None or c[0] == args.tune)
        and (args.mess is None or c[1] == args.mess)
        and (args.garment is None or c[2] == args.garment)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tune, mess, garment = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    choice = args.choice or rng.choice(sorted(CHOICES))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)

    return StoryParams(
        tune=tune,
        mess=mess,
        garment=garment,
        helper=helper,
        choice=choice,
        name=name,
        gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.tune not in TUNES:
        raise StoryError(f"(Unknown tune: {params.tune})")
    if params.mess not in MESSES:
        raise StoryError(f"(Unknown mess: {params.mess})")
    if params.garment not in GARMENTS:
        raise StoryError(f"(Unknown garment: {params.garment})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.choice not in CHOICES:
        raise StoryError(f"(Unknown choice: {params.choice})")
    if not garment_can_shrink(GARMENTS[params.garment]):
        raise StoryError(explain_rejection(GARMENTS[params.garment]))

    world = tell(
        tune=TUNES[params.tune],
        mess=MESSES[params.mess],
        garment_cfg=GARMENTS[params.garment],
        helper_cfg=HELPERS[params.helper],
        choice=params.choice,
        name=params.name,
        gender=params.gender,
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
        print(f"{len(combos)} compatible (tune, mess, garment) combos:\n")
        for tune, mess, garment in combos:
            print(f"  {tune:8} {mess:8} {garment}")
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
            header = f"### {p.name}: {p.mess} on {p.garment} ({p.tune}, {p.choice}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
