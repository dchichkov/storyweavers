#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mention_humor_lesson_learned_nursery_rhyme.py
=========================================================================

A standalone storyworld in a light nursery-rhyme style: a child in a sunny yard
wants to use a noisy horn to hurry a goose along, but a wiser child warns that
the horn will startle a hen carrying eggs. A calm grown-up helps them learn that
gentle tools work better than noisy ones.

The world model tracks a few physical meters (wobble, dropped, cracked, mess)
and emotional memes (glee, caution, embarrassment, relief). State drives the
story and the Q&A.

Run it
------
    python storyworlds/worlds/gpt-5.4/mention_humor_lesson_learned_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/mention_humor_lesson_learned_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/mention_humor_lesson_learned_nursery_rhyme.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/mention_humor_lesson_learned_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4/mention_humor_lesson_learned_nursery_rhyme.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/mention_humor_lesson_learned_nursery_rhyme.py --verify
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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 5.0
CAREFUL_TRAITS = {"careful", "gentle", "sensible", "patient"}


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
    loud: bool = False
    fragile: bool = False
    balancing: bool = False
    gentle: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man", "gander"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    yard: str
    perch: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class NoisyThing:
    id: str
    label: str
    phrase: str
    sound: str
    mention_line: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    bird: str
    phrase: str
    cargo: str
    perch: str
    wobble_word: str
    plural_cargo: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class GentleThing:
    id: str
    label: str
    phrase: str
    action: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    label: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    if "tool" not in world.entities or "carrier" not in world.entities:
        return out
    tool = world.get("tool")
    carrier = world.get("carrier")
    if tool.meters["blown"] < THRESHOLD or not tool.loud or not carrier.balancing:
        return out
    sig = ("startle", tool.id, carrier.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.meters["wobble"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__wobble__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    carrier = world.get("carrier")
    cargo = world.get("cargo")
    if carrier.meters["wobble"] < THRESHOLD:
        return out
    if carrier.meters["caught"] >= THRESHOLD:
        return out
    sig = ("drop", carrier.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["dropped"] += 1
    cargo.meters["cracked"] += 1
    world.get("yard").meters["mess"] += 1
    for kid in world.kids():
        kid.memes["embarrassment"] += 1
        kid.memes["alarm"] += 1
    out.append("__drop__")
    return out


CAUSAL_RULES = [
    Rule(name="startle", tag="physical", apply=_r_startle),
    Rule(name="drop", tag="physical", apply=_r_drop),
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


def hazard_at_risk(noisy: NoisyThing, carrier: Carrier) -> bool:
    return noisy.sense >= 1 and bool(carrier.cargo)


def sensible_noisy_options() -> list[NoisyThing]:
    return [n for n in NOISY_THINGS.values() if n.sense >= SENSE_MIN]


def sensible_rescues() -> list[Rescue]:
    return [r for r in RESCUES.values() if r.sense >= SENSE_MIN]


def wobble_severity(carrier: Carrier, delay: int) -> int:
    base = 1 if carrier.plural_cargo else 0
    return 1 + base + delay


def is_saved(rescue: Rescue, carrier: Carrier, delay: int) -> bool:
    return rescue.power >= wobble_severity(carrier, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > BOLDNESS_INIT


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    tool = sim.get("tool")
    tool.meters["blown"] += 1
    propagate(sim, narrate=False)
    cargo = sim.get("cargo")
    carrier = sim.get("carrier")
    return {
        "wobble": carrier.meters["wobble"],
        "drop": cargo.meters["dropped"],
    }


def introduce(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["glee"] += 1
    world.say(
        f"In {setting.yard}, where {setting.image}, {a.id} and {b.id} skipped in a loop and a swoop."
    )
    world.say(
        f'"Trip and tip, sing and skip!" cried {a.id}. "{setting.perch.capitalize()} looks ripe for a peep."'
    )


def show_carrier(world: World, carrier_cfg: Carrier) -> None:
    world.say(
        f"Up by {carrier_cfg.perch}, {carrier_cfg.phrase} came stepping slow, balancing {carrier_cfg.cargo} with a careful show."
    )


def tempt(world: World, a: Entity, noisy: NoisyThing) -> None:
    a.memes["boldness"] += 1
    world.say(
        f"{a.id} spotted {noisy.phrase} and gave a grin. "
        f'"A toot or two will hurry things in!"'
    )
    world.say(noisy.mention_line)


def warn(world: World, b: Entity, a: Entity, noisy: NoisyThing, carrier_cfg: Carrier, parent: Entity) -> None:
    pred = predict_wobble(world)
    b.memes["caution"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_drop"] = pred["drop"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} tapped {a.id}'s sleeve, already sure the plan was silly."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "If you blow {noisy.label}, '
        f'{carrier_cfg.bird} may {carrier_cfg.wobble_word}, and the eggs may tumble."{extra}'
    )
    world.say(
        f'"{parent.label_word.capitalize()} says loud things are for fairs, not for a bird on a narrow stair."'
    )


def back_down(world: World, a: Entity, b: Entity, noisy: NoisyThing, parent: Entity, gentle: GentleThing) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} puffed one cheek, then the other, and let the brave idea go. '
        f'"No horn," {a.pronoun()} said. "I can see that now."'
    )
    world.say(
        f'Together they went to {parent.label_word} and asked for {gentle.phrase} instead.'
    )


def defy(world: World, a: Entity, b: Entity, noisy: NoisyThing) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"Pooh to the warning," sang {a.id}. "I am the big one, and I know." '
            f'With a wink and a wobbling toe, {a.pronoun()} lifted {noisy.phrase}.'
        )
    else:
        world.say(
            f'"Just one toot!" sang {a.id}, and before the rhyme was through, '
            f'{a.pronoun()} lifted {noisy.phrase}.'
        )


def blow_horn(world: World, noisy: NoisyThing, carrier_cfg: Carrier) -> None:
    tool = world.get("tool")
    tool.meters["blown"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{noisy.sound} went the {noisy.label}, bright and brassy in the sun."
    )
    if world.get("carrier").meters["wobble"] >= THRESHOLD:
        world.say(
            f"{carrier_cfg.bird.capitalize()} gave a flap, a hop, a stop, and {carrier_cfg.wobble_word} on {carrier_cfg.perch}."
        )


def alarm(world: World, b: Entity, carrier_cfg: Carrier) -> None:
    if world.get("cargo").meters["dropped"] >= THRESHOLD:
        world.say(
            f'"Oh crumbs and combs!" cried {b.id}. "{carrier_cfg.cargo.capitalize()} are coming down!"'
        )
    else:
        world.say(
            f'"Steady, steady!" cried {b.id}. "{carrier_cfg.bird.capitalize()}, keep your feet."'
        )


def rescue_success(world: World, parent: Entity, rescue: Rescue, carrier_cfg: Carrier) -> None:
    carrier = world.get("carrier")
    carrier.meters["caught"] += 1
    carrier.meters["wobble"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came swish and quick and {rescue.text.format(bird=carrier_cfg.bird, cargo=carrier_cfg.cargo)}."
    )
    world.say(
        f"The eggs stayed whole, though one rolled in a circle like a tiny moon with shoes."
    )


def lesson_happy(world: World, parent: Entity, a: Entity, b: Entity, noisy: NoisyThing, gentle: GentleThing) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt and smiled. "Now then, my chicks, '
        f'do not even mention {noisy.label} when a careful creature is carrying eggs."'
    )
    world.say(
        f'"A gentle sound can guide better than a loud one," {parent.pronoun()} said. '
        f'"That is the tune to keep."'
    )
    world.say(
        f'{a.id} nodded, and {b.id} nodded too, trying not to giggle at the egg that had rolled a silly little loop.'
    )
    world.say(
        f'Soon they used {gentle.phrase}; it made {gentle.sound}, and even the goose followed with a bobbing, comic sweep.'
    )


def rescue_fail(world: World, parent: Entity, rescue: Rescue, carrier_cfg: Carrier) -> None:
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {rescue.fail.format(bird=carrier_cfg.bird, cargo=carrier_cfg.cargo)}."
    )
    world.say(
        "But the eggs went plip and plop into the straw, and one yellow yolk kissed a shoe."
    )


def messy_lesson(world: World, parent: Entity, a: Entity, b: Entity, noisy: NoisyThing, gentle: GentleThing) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{a.id} stared at the drippy shoe, and then {a.pronoun()} laughed a tiny laugh because the mess looked too silly not to.'
    )
    world.say(
        f'{parent.label_word.capitalize()} fetched a rag and said, "We clean the yolk, and we keep the lesson too: noisy tricks can make a bigger fuss than you meant to do."'
    )
    world.say(
        f'After that, no one would mention {noisy.label} for guiding birds. They chose {gentle.phrase} instead, and the yard felt calmer.'
    )


def safe_ending(world: World, a: Entity, b: Entity, gentle: GentleThing, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["glee"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"By and by, {a.id} and {b.id} {gentle.action}, making {gentle.sound} under the blue."
    )
    world.say(
        f"In {setting.yard}, where the clucking slowed, even the breeze seemed to nod and say, \"Gentle will do.\""
    )


def tell(
    setting: Setting,
    noisy: NoisyThing,
    carrier_cfg: Carrier,
    gentle: GentleThing,
    rescue: Rescue,
    instigator: str = "Nell",
    instigator_gender: str = "girl",
    cautioner: str = "Pip",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    relation: str = "siblings",
    instigator_age: int = 5,
    cautioner_age: int = 7,
    delay: int = 0,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["merry"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = initial_caution(trait)
    world.add(Entity(id="yard", type="yard", label=setting.yard))
    world.add(Entity(id="tool", type="tool", label=noisy.label, phrase=noisy.phrase, loud=True))
    world.add(Entity(
        id="carrier",
        type="hen",
        label=carrier_cfg.bird,
        phrase=carrier_cfg.phrase,
        balancing=True,
        attrs={"perch": carrier_cfg.perch},
    ))
    world.add(Entity(
        id="cargo",
        type="eggs",
        label=carrier_cfg.cargo,
        phrase=carrier_cfg.cargo,
        fragile=True,
    ))

    introduce(world, a, b, setting)
    show_carrier(world, carrier_cfg)

    world.para()
    tempt(world, a, noisy)
    warn(world, b, a, noisy, carrier_cfg, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, noisy, parent, gentle)
        world.para()
        safe_ending(world, a, b, gentle, setting)
        outcome = "averted"
    else:
        defy(world, a, b, noisy)
        world.para()
        blow_horn(world, noisy, carrier_cfg)
        alarm(world, b, carrier_cfg)
        saved = is_saved(rescue, carrier_cfg, delay)
        world.para()
        if saved:
            rescue_success(world, parent, rescue, carrier_cfg)
            lesson_happy(world, parent, a, b, noisy, gentle)
            world.para()
            safe_ending(world, a, b, gentle, setting)
            outcome = "saved"
        else:
            rescue_fail(world, parent, rescue, carrier_cfg)
            messy_lesson(world, parent, a, b, noisy, gentle)
            world.para()
            safe_ending(world, a, b, gentle, setting)
            outcome = "messy"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        setting=setting,
        noisy=noisy,
        carrier_cfg=carrier_cfg,
        gentle=gentle,
        rescue=rescue,
        relation=relation,
        ignited=False,
        outcome=outcome,
        dropped=world.get("cargo").meters["dropped"] >= THRESHOLD,
        saved=world.get("carrier").meters["caught"] >= THRESHOLD,
        delay=delay,
    )
    return world


SETTINGS = {
    "farmyard": Setting(
        id="farmyard",
        yard="the clover yard",
        perch="the low gate",
        image="the buttercups blinked and the washing line bowed",
        tags={"yard"},
    ),
    "orchard": Setting(
        id="orchard",
        yard="the apple yard",
        perch="the crooked fence",
        image="the apples shone and the bees hummed low",
        tags={"yard"},
    ),
    "cottage": Setting(
        id="cottage",
        yard="the cobble yard",
        perch="the step by the coop",
        image="the geraniums bobbed and the teacups winked in the window",
        tags={"yard"},
    ),
}

NOISY_THINGS = {
    "tin_horn": NoisyThing(
        id="tin_horn",
        label="the tin horn",
        phrase="a shiny tin horn",
        sound="Toot-too-TOOT",
        mention_line='"Do not mention whispering," laughed {name}. "This horn is faster than feet!"',
        sense=3,
        tags={"horn", "loud"},
    ),
    "kazoo": NoisyThing(
        id="kazoo",
        label="the kazoo",
        phrase="a yellow kazoo",
        sound="Bzzz-waa",
        mention_line='"Do not mention quietness," laughed {name}. "This buzzy wonder will do!"',
        sense=2,
        tags={"kazoo", "loud"},
    ),
    "drum": NoisyThing(
        id="drum",
        label="the toy drum",
        phrase="a round toy drum",
        sound="Bom-bom-BOM",
        mention_line='"Do not mention tiptoes," laughed {name}. "A grand drumbeat will do!"',
        sense=2,
        tags={"drum", "loud"},
    ),
    "bell": NoisyThing(
        id="bell",
        label="the brass bell",
        phrase="a brass bell",
        sound="Clang-a-cling",
        mention_line='"Do not mention soft shoes," laughed {name}. "A bell can wake the whole row!"',
        sense=2,
        tags={"bell", "loud"},
    ),
}

CARRIERS = {
    "hen_eggs": Carrier(
        id="hen_eggs",
        bird="the hen",
        phrase="the speckled hen",
        cargo="three brown eggs",
        perch="the low gate",
        wobble_word="wobbled",
        plural_cargo=True,
        tags={"hen", "eggs"},
    ),
    "goose_eggs": Carrier(
        id="goose_eggs",
        bird="the goose",
        phrase="the big gray goose",
        cargo="two pale eggs",
        perch="the crooked fence",
        wobble_word="teetered",
        plural_cargo=True,
        tags={"goose", "eggs"},
    ),
    "duck_eggs": Carrier(
        id="duck_eggs",
        bird="the duck",
        phrase="the drowsy duck",
        cargo="two cream eggs",
        perch="the step by the coop",
        wobble_word="tottered",
        plural_cargo=True,
        tags={"duck", "eggs"},
    ),
}

GENTLE_THINGS = {
    "grain_bowl": GentleThing(
        id="grain_bowl",
        label="grain bowl",
        phrase="a little grain bowl",
        action="shook the grain bowl softly",
        sound="tik-tik-tik",
        tags={"gentle", "grain"},
    ),
    "wooden_spoon": GentleThing(
        id="wooden_spoon",
        label="wooden spoon",
        phrase="a wooden spoon on a pail",
        action="tapped the wooden spoon on the pail gently",
        sound="tup-tup-tup",
        tags={"gentle", "spoon"},
    ),
    "crumb_paper": GentleThing(
        id="crumb_paper",
        label="crumb paper",
        phrase="a twist of crumb paper",
        action="rustled the crumb paper softly",
        sound="hush-rush",
        tags={"gentle", "crumbs"},
    ),
}

RESCUES = {
    "catch_apron": Rescue(
        id="catch_apron",
        label="catch_apron",
        sense=3,
        power=3,
        text="flung out an apron under {bird} just in time, so the eggs bobbled but did not break",
        fail="flung out an apron, but {cargo} slipped past it and cracked in the straw",
        qa_text="held out an apron and caught the falling eggs before they broke",
        tags={"apron", "catch"},
    ),
    "steady_basket": Rescue(
        id="steady_basket",
        label="steady_basket",
        sense=3,
        power=4,
        text="slid a basket beneath {bird} and steadied the eggs with both hands",
        fail="reached with a basket, but {cargo} bounced out before it could help",
        qa_text="slid a basket underneath and steadied the eggs with both hands",
        tags={"basket", "catch"},
    ),
    "shoe_scoop": Rescue(
        id="shoe_scoop",
        label="shoe_scoop",
        sense=2,
        power=2,
        text="scooped one egg with a shoe and nudged the others back to safety",
        fail="tried to scoop the eggs with a shoe, but the wobble was already too wild",
        qa_text="used a shoe to scoop and nudge the eggs back to safety",
        tags={"shoe", "catch"},
    ),
    "hat_catch": Rescue(
        id="hat_catch",
        label="hat_catch",
        sense=1,
        power=1,
        text="held up a hat and somehow caught every egg",
        fail="held up a hat, but the eggs slipped past and went splat",
        qa_text="caught the eggs in a hat",
        tags={"hat", "catch"},
    ),
}

GIRL_NAMES = ["Nell", "Molly", "Daisy", "Poppy", "Tess", "May"]
BOY_NAMES = ["Pip", "Tom", "Ned", "Jem", "Kit", "Rob"]
TRAITS = ["careful", "gentle", "sensible", "patient", "curious", "merry"]


@dataclass
class StoryParams:
    setting: str
    noisy_thing: str
    carrier: str
    gentle_thing: str
    rescue: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 5
    cautioner_age: int = 7
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="farmyard",
        noisy_thing="tin_horn",
        carrier="hen_eggs",
        gentle_thing="grain_bowl",
        rescue="steady_basket",
        instigator="Nell",
        instigator_gender="girl",
        cautioner="Pip",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        delay=0,
    ),
    StoryParams(
        setting="orchard",
        noisy_thing="kazoo",
        carrier="goose_eggs",
        gentle_thing="crumb_paper",
        rescue="catch_apron",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="May",
        cautioner_gender="girl",
        parent="father",
        trait="gentle",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        delay=0,
    ),
    StoryParams(
        setting="cottage",
        noisy_thing="drum",
        carrier="duck_eggs",
        gentle_thing="wooden_spoon",
        rescue="shoe_scoop",
        instigator="Jem",
        instigator_gender="boy",
        cautioner="Daisy",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
        delay=1,
    ),
    StoryParams(
        setting="farmyard",
        noisy_thing="bell",
        carrier="hen_eggs",
        gentle_thing="grain_bowl",
        rescue="steady_basket",
        instigator="Poppy",
        instigator_gender="girl",
        cautioner="Molly",
        cautioner_gender="girl",
        parent="father",
        trait="careful",
        relation="siblings",
        instigator_age=4,
        cautioner_age=7,
        delay=0,
    ),
]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for noisy_id, noisy in NOISY_THINGS.items():
            for carrier_id, carrier in CARRIERS.items():
                if not hazard_at_risk(noisy, carrier):
                    continue
                for gentle_id in GENTLE_THINGS:
                    for rescue_id, rescue in RESCUES.items():
                        if rescue.sense >= SENSE_MIN:
                            combos.append((setting_id, noisy_id, carrier_id, gentle_id, rescue_id))
    return combos


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


KNOWLEDGE = {
    "horn": [(
        "Why can a loud horn be a bad idea near animals?",
        "A loud horn can startle animals and make them jump or wobble. When a creature is carrying something fragile, that surprise can cause a mess."
    )],
    "kazoo": [(
        "What is a kazoo?",
        "A kazoo is a little toy you hum into. It makes a buzzy sound that can be funny, but it is not always the right sound to use."
    )],
    "drum": [(
        "Why does a drum sound big?",
        "A drum sounds big because its skin and hollow body make the bumps of tapping spread into the air. That is why a little hit can sound much louder than a whisper."
    )],
    "bell": [(
        "What does a bell do?",
        "A bell rings loudly so people or animals can hear it. Loud sounds can be useful, but they should be used at the right time."
    )],
    "eggs": [(
        "Why do eggs break easily?",
        "Eggs have hard shells, but the shells are thin. A bump or a fall can crack them quickly."
    )],
    "gentle": [(
        "Why can a gentle sound work better than a loud one?",
        "A gentle sound does not frighten others as much. It can guide attention without causing a rush or a wobble."
    )],
    "catch": [(
        "What should you do if something fragile starts to fall?",
        "Call for a grown-up and try to keep everyone calm. Quick, careful help is better than wild grabbing."
    )],
}
KNOWLEDGE_ORDER = ["horn", "kazoo", "drum", "bell", "eggs", "gentle", "catch"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    noisy = f["noisy"]
    carrier = f["carrier_cfg"]
    gentle = f["gentle"]
    outcome = f["outcome"]
    base = (
        f'Write a short nursery-rhyme-style story for a 3-to-5-year-old that includes the word "mention" '
        f'and features humor plus a lesson learned.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a playful rhyme-story where {a.id} wants to use {noisy.label} to hurry {carrier.bird}, "
            f"but {b.id} stops the idea before anything falls.",
            f"Write a gentle cautionary nursery rhyme where a wiser older child suggests {gentle.phrase} "
            f"instead of a noisy toy, and the ending proves that gentle works better.",
        ]
    if outcome == "saved":
        return [
            base,
            f"Tell a funny nursery-rhyme tale where {a.id} ignores a warning and blows {noisy.label}, "
            f"making {carrier.bird} wobble with eggs, but a grown-up saves the day.",
            f"Write a child-facing story with a comic near-disaster, a calm rescue, and a clear lesson "
            f"about choosing gentle help over noisy tricks.",
        ]
    return [
        base,
        f"Tell a nursery-rhyme-style cautionary story where {a.id} blows {noisy.label}, "
        f"{carrier.bird} drops the eggs, and the family learns from the silly mess.",
        f"Write a humorous but instructive rhyme-story where a loud shortcut causes yolk on a shoe, "
        f"and the children choose {gentle.phrase} afterward.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    noisy = f["noisy"]
    carrier = f["carrier_cfg"]
    gentle = f["gentle"]
    rescue = f["rescue"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their {parent.label_word} in a sunny yard. "
            f"The trouble began when {a.id} wanted to use {noisy.label} near {carrier.bird}."
        ),
        (
            f"Why did {b.id} warn {a.id}?",
            f"{b.id} warned that the loud sound could startle {carrier.bird} while {carrier.pronoun()} was balancing {carrier.cargo}. "
            f"If the bird wobbled, the eggs could tumble and break."
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append((
            f"What happened after {b.id} gave the warning?",
            f"{a.id} listened and gave up the noisy plan, so nothing fell at all. "
            f"They asked for {gentle.phrase} instead because a gentler way fit the problem better."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely and happily. The children used {gentle.phrase}, and the yard grew calm instead of messy."
        ))
    elif outcome == "saved":
        qa.append((
            f"What happened when {a.id} used {noisy.label}?",
            f"{carrier.bird.capitalize()} wobbled with the eggs, and everyone felt a jolt of alarm. "
            f"The loud trick almost caused a bigger problem than {a.id} expected."
        ))
        qa.append((
            f"How did the grown-up help?",
            f"The grown-up {rescue.qa_text}. That quick, careful move stopped the wobble from turning into a broken-egg mess."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that gentle help can work better than noisy showing-off. "
            f"The ending proves it because the calm tool guided the bird without any fuss."
        ))
    else:
        qa.append((
            f"What happened when {a.id} used {noisy.label}?",
            f"The loud sound startled {carrier.bird}, and the eggs dropped and cracked. "
            f"One yolk even splashed onto a shoe, which made the mess feel funny and sad at the same time."
        ))
        qa.append((
            "What lesson did the children learn?",
            f"They learned that a noisy shortcut can make a small problem bigger. "
            f"After the mess, they chose {gentle.phrase} because it was kinder and wiser."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    noisy_id = f["noisy"].id
    if noisy_id == "tin_horn":
        tags.add("horn")
    else:
        tags.add(noisy_id)
    tags.add("eggs")
    tags.add("gentle")
    if f["outcome"] in {"saved", "messy"}:
        tags.add("catch")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (
            ("loud", e.loud),
            ("fragile", e.fragile),
            ("balancing", e.balancing),
            ("gentle", e.gentle),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(noisy: NoisyThing, rescue: Rescue) -> str:
    if noisy.sense < SENSE_MIN:
        good = ", ".join(sorted(nid for nid, n in NOISY_THINGS.items() if n.sense >= SENSE_MIN))
        return (
            f"(No story: {noisy.label} is treated as too weak or odd for this world's noisy-mistake setup. "
            f"Try one of these: {good}.)"
        )
    if rescue.sense < SENSE_MIN:
        good = ", ".join(sorted(rid for rid, r in RESCUES.items() if r.sense >= SENSE_MIN))
        return (
            f"(No story: rescue '{rescue.id}' scores too low on common sense for this world. "
            f"Try one of these: {good}.)"
        )
    return "(No story: that option set does not form a reasonable story.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    saved = is_saved(RESCUES[params.rescue], CARRIERS[params.carrier], params.delay)
    return "saved" if saved else "messy"


ASP_RULES = r"""
hazard(N, C) :- noisy(N), carrier(C).

sensible_noisy(N) :- noisy(N), noisy_sense(N, S), sense_min(M), S >= M.
sensible_rescue(R) :- rescue(R), rescue_sense(R, S), sense_min(M), S >= M.

valid(S, N, C, G, R) :-
    setting(S), noisy(N), carrier(C), gentle(G), rescue(R),
    hazard(N, C), sensible_noisy(N), sensible_rescue(R).

careful_now(T) :- trait(T), careful_trait(T).
init_caution(5) :- trait(T), careful_now(T).
init_caution(3) :- trait(T), not careful_now(T).
older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
authority(C + 1 + B) :- init_caution(C), B = 3, older_sibling.
authority(C + 1 + 0) :- init_caution(C), not older_sibling.
averted :- older_sibling, authority(A), boldness_init(B), A > B.

severity(1 + P + D) :- chosen_carrier(C), cargo_plural(C, P), delay(D).
rescue_power(P) :- chosen_rescue(R), rescue_power_val(R, P).
saved :- rescue_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(saved) :- not averted, saved.
outcome(messy) :- not averted, not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid, noisy in NOISY_THINGS.items():
        lines.append(asp.fact("noisy", nid))
        lines.append(asp.fact("noisy_sense", nid, noisy.sense))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("cargo_plural", cid, 1 if carrier.plural_cargo else 0))
    for gid in GENTLE_THINGS:
        lines.append(asp.fact("gentle", gid))
    for rid, rescue in RESCUES.items():
        lines.append(asp.fact("rescue", rid))
        lines.append(asp.fact("rescue_sense", rid, rescue.sense))
        lines.append(asp.fact("rescue_power_val", rid, rescue.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_carrier", params.carrier),
        asp.fact("chosen_rescue", params.rescue),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            args = parser.parse_args([])
            p = resolve_params(args, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            continue

    bad = 0
    for p in cases:
        po = outcome_of(p)
        ao = asp_outcome(p)
        if po != ao:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Empty story in smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a noisy joke, a wobbling bird, and a gentle lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--noisy-thing", dest="noisy_thing", choices=NOISY_THINGS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--gentle-thing", dest="gentle_thing", choices=GENTLE_THINGS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how late the grown-up help is")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.noisy_thing and args.rescue:
        noisy = NOISY_THINGS[args.noisy_thing]
        rescue = RESCUES[args.rescue]
        if noisy.sense < SENSE_MIN or rescue.sense < SENSE_MIN:
            raise StoryError(explain_rejection(noisy, rescue))
    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.noisy_thing is None or combo[1] == args.noisy_thing)
        and (args.carrier is None or combo[2] == args.carrier)
        and (args.gentle_thing is None or combo[3] == args.gentle_thing)
        and (args.rescue is None or combo[4] == args.rescue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, noisy_id, carrier_id, gentle_id, rescue_id = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        noisy_thing=noisy_id,
        carrier=carrier_id,
        gentle_thing=gentle_id,
        rescue=rescue_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        delay=delay,
    )


def _filled_noisy(noisy: NoisyThing, name: str) -> NoisyThing:
    return NoisyThing(
        id=noisy.id,
        label=noisy.label,
        phrase=noisy.phrase,
        sound=noisy.sound,
        mention_line=noisy.mention_line.format(name=name),
        sense=noisy.sense,
        tags=set(noisy.tags),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        noisy = NOISY_THINGS[params.noisy_thing]
        carrier = CARRIERS[params.carrier]
        gentle = GENTLE_THINGS[params.gentle_thing]
        rescue = RESCUES[params.rescue]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    if noisy.sense < SENSE_MIN:
        raise StoryError(explain_rejection(noisy, RESCUES["steady_basket"]))
    if rescue.sense < SENSE_MIN:
        raise StoryError(explain_rejection(noisy, rescue))

    world = tell(
        setting=setting,
        noisy=_filled_noisy(noisy, params.instigator),
        carrier_cfg=carrier,
        gentle=gentle,
        rescue=rescue,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        delay=params.delay,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, noisy, carrier, gentle, rescue) combos:\n")
        for setting_id, noisy_id, carrier_id, gentle_id, rescue_id in combos:
            print(f"  {setting_id:8} {noisy_id:9} {carrier_id:10} {gentle_id:12} {rescue_id}")
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.noisy_thing} with {p.carrier} "
                f"({p.setting}, {p.rescue}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
