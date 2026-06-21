#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bog_inflict_school_surprise_comedy.py
================================================================

A standalone story world for a school comedy about a boggy shortcut, a surprise,
and the trouble muddy shoes can inflict on a neat hallway.

Premise
-------
At school, a child helps carry a hidden surprise for a teacher or principal.
There is a tempting shortcut past a boggy patch by the school garden. The eager
child wants to dash across it. A friend warns that the bog will grab shoes,
splash mud, and maybe spoil the surprise. A sensible grown-up offers a better
way to carry the surprise, and the ending image proves whether the surprise
arrives neat or the class has to improvise a funny replacement.

Reasonableness rule
-------------------
Not every carrying method honestly protects every surprise item. A paper poster
needs a tube; cupcakes need a cake box; a flower pot needs a wagon or tray with
steady hands; a kazoo bundle needs a bag. The world refuses invalid explicit
choices.

Run it
------
    python storyworlds/worlds/gpt-5.4/bog_inflict_school_surprise_comedy.py
    python storyworlds/worlds/gpt-5.4/bog_inflict_school_surprise_comedy.py --surprise cupcakes
    python storyworlds/worlds/gpt-5.4/bog_inflict_school_surprise_comedy.py --carrier bag
    python storyworlds/worlds/gpt-5.4/bog_inflict_school_surprise_comedy.py --all
    python storyworlds/worlds/gpt-5.4/bog_inflict_school_surprise_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/bog_inflict_school_surprise_comedy.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_woman", "principal_woman"}
        male = {"boy", "father", "man", "teacher_man", "principal_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        if self.role == "teacher" or self.type.startswith("teacher_"):
            return "teacher"
        if self.role == "principal" or self.type.startswith("principal_"):
            return "principal"
        if self.type in {"mother", "father"}:
            return {"mother": "mom", "father": "dad"}[self.type]
        return self.type


@dataclass
class SurpriseKind:
    id: str
    label: str
    phrase: str
    hiding_spot: str
    reveal_line: str
    vulnerable_to: set[str]
    climax: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    guards: set[str]
    mode: str
    sense: int
    funny: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    label: str
    phrase: str
    depth: int
    mess: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Celebration:
    id: str
    honoree_role: str
    honoree_name: str
    honoree_type: str
    setup: str
    shout: str
    surprise_word: str
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


def _r_mud_tracks(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("hero")
    hall = world.get("hall")
    if child.meters["muddy"] >= THRESHOLD:
        sig = ("tracks", "hero")
        if sig not in world.fired:
            world.fired.add(sig)
            hall.meters["dirty"] += 1
            out.append("__tracks__")
    return out


def _r_dirty_hall_work(world: World) -> list[str]:
    out: list[str] = []
    hall = world.get("hall")
    helper = world.get("helper")
    if hall.meters["dirty"] >= THRESHOLD:
        sig = ("work", "hall")
        if sig not in world.fired:
            world.fired.add(sig)
            helper.meters["workload"] += 1
            out.append("The hallway would need mopping before the next class came through.")
    return out


def _r_spoil_surprise(world: World) -> list[str]:
    out: list[str] = []
    surprise = world.get("surprise")
    if surprise.meters["wobbled"] >= THRESHOLD and world.facts.get("unguarded"):
        sig = ("spoil", "surprise")
        if sig not in world.fired:
            world.fired.add(sig)
            surprise.meters["spoiled"] += 1
            out.append("__spoiled__")
    return out


CAUSAL_RULES = [
    Rule("mud_tracks", "physical", _r_mud_tracks),
    Rule("dirty_hall_work", "physical", _r_dirty_hall_work),
    Rule("spoil_surprise", "physical", _r_spoil_surprise),
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


def protects(carrier: Carrier, surprise: SurpriseKind) -> bool:
    return surprise.vulnerable_to.issubset(carrier.guards)


def sensible_carriers() -> list[Carrier]:
    return [c for c in CARRIERS.values() if c.sense >= SENSE_MIN]


def bog_severity(route: Route, hurry: int) -> int:
    return route.depth + hurry


def surprise_saved(carrier: Carrier, route: Route, hurry: int, surprise: SurpriseKind) -> bool:
    return protects(carrier, surprise) and carrier.sense >= route.depth and carrier.sense >= hurry + 1


def explain_rejection(surprise: SurpriseKind, carrier: Carrier) -> str:
    missing = sorted(surprise.vulnerable_to - carrier.guards)
    if carrier.sense < SENSE_MIN:
        return (
            f"(Refusing carrier '{carrier.id}': it scores too low on common sense "
            f"(sense={carrier.sense} < {SENSE_MIN}). Pick a steadier option.)"
        )
    if missing:
        return (
            f"(No story: {carrier.label} does not honestly protect {surprise.label}. "
            f"It still leaves it open to {', '.join(missing)}, so the surprise could be ruined.)"
        )
    return "(No story: this carrying plan is not reasonable.)"


def predict_shortcut(world: World, route: Route, hurry: int) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    surprise = sim.get("surprise")
    hero.meters["muddy"] += 1
    surprise.meters["wobbled"] += 1 if bog_severity(route, hurry) >= 2 else 0
    propagate(sim, narrate=False)
    return {
        "muddy": hero.meters["muddy"] >= THRESHOLD,
        "spoiled": surprise.meters["spoiled"] >= THRESHOLD,
        "hall_dirty": sim.get("hall").meters["dirty"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, celebration: Celebration) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"At school, {hero.id} and {friend.id} had the busiest whispers in the whole class. "
        f"{celebration.setup}"
    )


def hide_surprise(world: World, celebration: Celebration, surprise: SurpriseKind) -> None:
    world.say(
        f"They had tucked {surprise.phrase} in {surprise.hiding_spot}, and every time the classroom door clicked, "
        f"both children froze and then giggled."
    )


def assign_task(world: World, hero: Entity, surprise: SurpriseKind, celebration: Celebration) -> None:
    world.say(
        f'"{hero.id}," whispered a classmate, "can you bring {surprise.phrase} before {celebration.honoree_name} comes back?" '
        f"{hero.id} puffed up with importance at once."
    )


def tempt_shortcut(world: World, hero: Entity, route: Route) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f"Outside the side door lay {route.phrase}. It looked like a shortcut if you ignored the squelchy part."
    )
    world.say(
        f'"I can zip past the {route.label} in two seconds," {hero.id} said. "My shoes are faster than mud."'
    )


def warn(world: World, friend: Entity, hero: Entity, surprise: SurpriseKind, route: Route,
         helper: Entity, hurry: int) -> None:
    pred = predict_shortcut(world, route, hurry)
    friend.memes["worry"] += 1
    world.facts["predicted"] = pred
    spoil = ""
    if pred["spoiled"]:
        spoil = f" It might even spoil {surprise.label}."
    work = ""
    if pred["hall_dirty"]:
        work = f" And please don't inflict muddy footprints on the hall for the {helper.title_word} to mop."
    world.say(
        f'{friend.id} grabbed {hero.pronoun("possessive")} sleeve. "That is not a shortcut. It is a bog with opinions," '
        f'{friend.pronoun()} said. "It will grab your shoes, splash mud, and make everyone stare.{spoil}{work}"'
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'"I will tiptoe like a champion," said {hero.id}, which was exactly the kind of sentence that never ends in clean socks.'
    )


def bog_splat(world: World, hero: Entity, surprise: Entity, route: Route) -> None:
    hero.meters["muddy"] += 1
    surprise.meters["wobbled"] += 1
    hero.memes["embarrassment"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took one brave step beside the {route.label}. Then came {route.sound}. "
        f"One shoe stuck, the other slid, and {hero.id} windmilled both arms like a confused scarecrow."
    )


def helper_arrives(world: World, helper: Entity, carrier: Carrier) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"Just then, {helper.id} appeared at the side door with {carrier.phrase}. "
        f'"Good morning to this very muddy circus," {helper.pronoun()} said.'
    )


def save_plan(world: World, helper: Entity, hero: Entity, friend: Entity,
              celebration: Celebration, surprise: SurpriseKind, carrier: Carrier) -> None:
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f'{helper.id} looked at {surprise.phrase}, looked at {hero.id}\'s shoe, and shook {helper.pronoun("possessive")} head with a smile. '
        f'"If we want to keep the {celebration.surprise_word} a surprise, we carry it the steady way," {helper.pronoun()} said.'
    )
    world.say(
        f"{helper.pronoun().capitalize()} set out {carrier.phrase}, and suddenly the whole mission seemed possible again. "
        f"{carrier.funny}"
    )


def reveal_success(world: World, hero: Entity, friend: Entity, celebration: Celebration,
                   surprise: SurpriseKind, carrier: Carrier) -> None:
    hero.memes["pride"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"A minute later they rolled and tiptoed back into class with {surprise.phrase} safe inside {carrier.label}. "
        f"When {celebration.honoree_name} opened the door, everybody jumped up and shouted, {celebration.shout}"
    )
    world.say(
        f"{celebration.honoree_name} blinked, laughed, and saw the neat surprise first and the muddy shoe second. "
        f"{surprise.climax}"
    )


def reveal_improv(world: World, hero: Entity, friend: Entity, celebration: Celebration,
                  surprise: SurpriseKind) -> None:
    hero.memes["relief"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"The original {surprise.label} was too rumpled to present, so the class changed plans in a flash. "
        f"They hid the muddy part, lined up shoulder to shoulder, and made up a silly drumroll with pencils and desks."
    )
    world.say(
        f"When {celebration.honoree_name} stepped inside, everybody shouted, {celebration.shout} "
        f"{celebration.honoree_name} laughed so hard that the ruined surprise did not matter half as much as the effort."
    )
    world.say(
        f"Even {hero.id} laughed at the muddy shoe stuck halfway off, and the whole room felt brighter because the surprise had turned into a joke everybody could share."
    )


def clean_tag(world: World, helper: Entity, hero: Entity) -> None:
    world.say(
        f'Before the bell, {helper.id} handed {hero.id} a towel and said, "Next time, use the path before the bog writes its name on your socks."'
    )


def tell(celebration: Celebration, surprise_cfg: SurpriseKind, carrier_cfg: Carrier, route: Route,
         hero_name: str = "Nia", hero_type: str = "girl", friend_name: str = "Owen",
         friend_type: str = "boy", helper_role: str = "janitor", hurry: int = 1) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    helper_type = "man" if helper_role == "janitor" else "teacher_woman"
    helper_name = "Mr. Bell" if helper_role == "janitor" else "Ms. Park"
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    honoree = world.add(Entity(
        id=celebration.honoree_name,
        kind="character",
        type=celebration.honoree_type,
        role=celebration.honoree_role,
    ))
    surprise = world.add(Entity(id="surprise", type="surprise", label=surprise_cfg.label))
    world.add(Entity(id="hall", type="hall", label="the hallway"))

    world.facts["unguarded"] = not protects(carrier_cfg, surprise_cfg)

    introduce(world, hero, friend, celebration)
    hide_surprise(world, celebration, surprise_cfg)
    assign_task(world, hero, surprise_cfg, celebration)

    world.para()
    tempt_shortcut(world, hero, route)
    warn(world, friend, hero, surprise_cfg, route, helper, hurry)
    defy(world, hero)

    world.para()
    bog_splat(world, hero, surprise, route)
    helper_arrives(world, helper, carrier_cfg)

    saved = surprise_saved(carrier_cfg, route, hurry, surprise_cfg)
    outcome = "saved" if saved else "improv"

    if saved:
        save_plan(world, helper, hero, friend, celebration, surprise_cfg, carrier_cfg)
        world.para()
        reveal_success(world, hero, friend, celebration, surprise_cfg, carrier_cfg)
        clean_tag(world, helper, hero)
    else:
        propagate(world, narrate=False)
        world.para()
        reveal_improv(world, hero, friend, celebration, surprise_cfg)
        clean_tag(world, helper, hero)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        honoree=honoree,
        celebration=celebration,
        surprise_cfg=surprise_cfg,
        carrier=carrier_cfg,
        route=route,
        hurry=hurry,
        outcome=outcome,
        saved=saved,
        hall_dirty=world.get("hall").meters["dirty"] >= THRESHOLD,
        surprise_spoiled=world.get("surprise").meters["spoiled"] >= THRESHOLD or outcome == "improv",
    )
    return world


CELEBRATIONS = {
    "teacher_birthday": Celebration(
        "teacher_birthday",
        "teacher",
        "Ms. Honey",
        "teacher_woman",
        "Their class was getting ready for a secret birthday cheer for Ms. Honey.",
        '"Surprise! Happy birthday, Ms. Honey!"',
        "birthday surprise",
        tags={"teacher", "birthday", "surprise"},
    ),
    "principal_welcome": Celebration(
        "principal_welcome",
        "principal",
        "Principal Stone",
        "principal_man",
        "Their class was planning a secret welcome-back cheer for Principal Stone after his meeting.",
        '"Surprise! Welcome back, Principal Stone!"',
        "welcome-back surprise",
        tags={"principal", "surprise"},
    ),
    "teacher_thanks": Celebration(
        "teacher_thanks",
        "teacher",
        "Mr. Vale",
        "teacher_man",
        "Their class had made a secret thank-you moment for Mr. Vale after reading time.",
        '"Surprise! Thank you, Mr. Vale!"',
        "thank-you surprise",
        tags={"teacher", "surprise"},
    ),
}

SURPRISES = {
    "cupcakes": SurpriseKind(
        "cupcakes",
        "cupcakes",
        "a tray of frosted cupcakes",
        "the art closet behind a stack of paint paper",
        "The frosting survived, and each cupcake wore its little swirl like a party hat.",
        {"smear", "tilt"},
        "The class gasped because even the frosting roses were still standing.",
        tags={"cupcakes", "food", "surprise"},
    ),
    "poster": SurpriseKind(
        "poster",
        "poster",
        "a giant paper poster covered in stars and signatures",
        "the reading corner behind the beanbags",
        "The poster opened with a soft flap and showed all the children's names in bright crayon.",
        {"soak", "crease"},
        "Mr. Vale spread the poster wide and read every single scribbly message.",
        tags={"poster", "paper", "surprise"},
    ),
    "flower_pot": SurpriseKind(
        "flower_pot",
        "flower pot",
        "a flower pot painted with smiling worms",
        "the science shelf under the class terrarium",
        "The flower pot arrived without spilling its little heap of soil.",
        {"tilt", "drop"},
        "Even Principal Stone bent down to admire the painted worms marching around the pot.",
        tags={"plant", "surprise"},
    ),
    "kazoos": SurpriseKind(
        "kazoos",
        "kazoo bundle",
        "a bundle of shiny kazoos tied with curling ribbon",
        "the music cupboard beside the tambourines",
        "The kazoos did not tumble away, which meant the silly song could begin right on time.",
        {"drop"},
        "When the first buzzing note burst out, everyone laughed, including the grown-up being surprised.",
        tags={"music", "surprise"},
    ),
}

CARRIERS = {
    "cake_box": Carrier(
        "cake_box",
        "the cake box",
        "a white cake box with a wobbly little handle",
        {"smear", "tilt"},
        "carry",
        3,
        "The box made the cupcakes look so serious that the children began marching as if they were royal pudding guards.",
        tags={"box", "cupcakes"},
    ),
    "tube": Carrier(
        "tube",
        "the poster tube",
        "a blue poster tube with a shoulder strap",
        {"soak", "crease"},
        "carry",
        3,
        "Once the poster slid inside, it looked less like schoolwork and more like a spy mission.",
        tags={"tube", "poster"},
    ),
    "wagon": Carrier(
        "wagon",
        "the red wagon",
        "a little red wagon from the gym cupboard",
        {"tilt", "drop"},
        "roll",
        3,
        "The wagon squeaked like a tiny trumpet, which somehow made the whole rescue feel even more important.",
        tags={"wagon", "plant"},
    ),
    "bag": Carrier(
        "bag",
        "the music bag",
        "a zippered music bag with three silver stars on it",
        {"drop"},
        "carry",
        2,
        "The kazoos jingled once inside and then behaved, as if they knew they were part of a secret plan.",
        tags={"bag", "music"},
    ),
    "bare_hands": Carrier(
        "bare_hands",
        "bare hands",
        "nothing at all but two hopeful hands",
        set(),
        "carry",
        1,
        "It was a plan made almost entirely out of confidence.",
        tags={"risky"},
    ),
}

ROUTES = {
    "garden_bog": Route(
        "garden_bog",
        "bog",
        "the boggy corner by the school garden",
        2,
        "muddy",
        '"schloop-splap"',
        tags={"bog", "mud", "school"},
    ),
    "mulchy_bog": Route(
        "mulchy_bog",
        "bog",
        "the mulchy bog beside the compost bins",
        1,
        "muddy",
        '"slurp-plup"',
        tags={"bog", "mud", "school"},
    ),
    "drain_bog": Route(
        "drain_bog",
        "bog",
        "the soggy bog near the back drainpipe",
        2,
        "muddy",
        '"glorp"',
        tags={"bog", "mud", "school"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Ava", "Maya", "Zoe", "Ruby", "Tess", "Mina"]
BOY_NAMES = ["Owen", "Ben", "Max", "Theo", "Eli", "Noah", "Finn", "Milo"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, surprise in SURPRISES.items():
        for cid, carrier in CARRIERS.items():
            if carrier.sense >= SENSE_MIN and protects(carrier, surprise):
                combos.append((sid, cid))
    return combos


@dataclass
class StoryParams:
    celebration: str
    surprise: str
    carrier: str
    route: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    helper: str
    hurry: int
    seed: Optional[int] = None


KNOWLEDGE = {
    "bog": [(
        "What is a bog?",
        "A bog is a very wet, muddy patch of ground that can feel soft and squishy under your feet. It can grab shoes and make walking tricky."
    )],
    "mud": [(
        "Why is mud slippery?",
        "Mud is slippery because wet dirt makes a slick layer on top of the ground. Shoes can slide on it instead of gripping firmly."
    )],
    "surprise": [(
        "What makes a surprise fun?",
        "A surprise feels fun when someone does not know a kind thing is coming and then discovers it all at once. The happy feeling comes from being cared for unexpectedly."
    )],
    "cupcakes": [(
        "Why do cupcakes need a box?",
        "Cupcakes are soft and frosted, so they can smear if they wobble around. A box helps keep them level and protected."
    )],
    "poster": [(
        "Why does a paper poster need a tube?",
        "Paper can crease, tear, or get wet very easily. A tube keeps it rolled up safely while you carry it."
    )],
    "plant": [(
        "Why should you carry a flower pot carefully?",
        "A flower pot can tip, spill soil, or even crack if it drops. Carrying it steadily keeps both the plant and the floor safe."
    )],
    "music": [(
        "What is a kazoo?",
        "A kazoo is a small instrument that buzzes when you hum into it. It sounds funny, which is why it fits silly music so well."
    )],
    "cleaning": [(
        "Why is it not kind to track mud into school?",
        "Tracking mud into school makes the floor dirty and slippery for other people. Then someone has extra work cleaning it up."
    )],
}
KNOWLEDGE_ORDER = ["bog", "mud", "surprise", "cupcakes", "poster", "plant", "music", "cleaning"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    celebration, surprise = f["celebration"], f["surprise_cfg"]
    return [
        f'Write a funny school story for a 3-to-5-year-old that includes the words "bog" and "inflict" and features a surprise.',
        f"Tell a comedy where {hero.id} tries to hurry a hidden {surprise.label} past a bog at school, while {friend.id} warns what muddy shoes might inflict on the hallway.",
        f"Write a short school surprise story with a boggy shortcut, a near disaster, and a happy ending that makes everyone laugh.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    celebration = f["celebration"]
    surprise = f["surprise_cfg"]
    carrier = f["carrier"]
    route = f["route"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} at school, with {helper.id} helping at the important moment. They were trying to keep a secret surprise ready for {celebration.honoree_name}."
        ),
        (
            "What was the surprise for?",
            f"The class was preparing a surprise for {celebration.honoree_name}. They wanted the kind moment to stay secret until the grown-up walked back into the room."
        ),
        (
            f"Why did {friend.id} warn {hero.id} about the bog?",
            f"{friend.id} knew the bog would grab shoes, splash mud, and turn a quick errand into a mess. {friend.pronoun().capitalize()} also did not want muddy tracks to be inflicted on the school hallway for someone else to clean."
        ),
        (
            f"What happened when {hero.id} tried the shortcut?",
            f"{hero.id} stepped near the bog and immediately slipped into a funny, wobbly scramble. One shoe got muddy, and the secret delivery stopped being neat and quiet."
        ),
    ]
    if f["outcome"] == "saved":
        qa.append((
            f"How was the surprise saved?",
            f"{helper.id} arrived with {carrier.phrase}, which protected the {surprise.label} the steady way. That let the children bring it into class safely even after the bog tried to cause trouble."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with everyone shouting the surprise together and laughing at the muddy shoe. The ending proves the plan changed from a messy rush into a careful, funny success."
        ))
    else:
        qa.append((
            "Did the original surprise stay perfect?",
            f"No. The original {surprise.label} became too messy to present exactly as planned, so the class improvised a sillier surprise instead. They still made {celebration.honoree_name} feel loved, which mattered most."
        ))
        qa.append((
            "How did the story still end happily?",
            f"The children turned the mistake into a joke the whole class could share. Everyone laughed together, so the muddy accident became part of the celebration instead of ruining it."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bog", "mud", "surprise"}
    sid = f["surprise_cfg"].id
    if sid == "cupcakes":
        tags.add("cupcakes")
    elif sid == "poster":
        tags.add("poster")
    elif sid == "flower_pot":
        tags.add("plant")
    elif sid == "kazoos":
        tags.add("music")
    if f.get("hall_dirty"):
        tags.add("cleaning")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("teacher_birthday", "cupcakes", "cake_box", "garden_bog", "Nia", "girl", "Owen", "boy", "janitor", 1),
    StoryParams("principal_welcome", "flower_pot", "wagon", "mulchy_bog", "Ben", "boy", "Ruby", "girl", "janitor", 1),
    StoryParams("teacher_thanks", "poster", "tube", "drain_bog", "Maya", "girl", "Finn", "boy", "teacher", 1),
    StoryParams("teacher_birthday", "kazoos", "bag", "garden_bog", "Theo", "boy", "Lila", "girl", "janitor", 1),
    StoryParams("principal_welcome", "cupcakes", "bare_hands", "garden_bog", "Eli", "boy", "Mina", "girl", "janitor", 2),
]


ASP_RULES = r"""
compatible(S, C) :- surprise(S), carrier(C), sensible(C), vulnerable(S, V), guards(C, V),
                    not missing_guard(S, C).
missing_guard(S, C) :- surprise(S), carrier(C), vulnerable(S, V), not guards(C, V).

valid(S, C) :- compatible(S, C).

severity(D + H) :- chosen_route(R), depth(R, D), hurry(H).
saved :- chosen_surprise(S), chosen_carrier(C), compatible(S, C),
         chosen_route(R), depth(R, D), carrier_sense(C, CS), hurry(H),
         CS >= D, CS >= H + 1.

outcome(saved) :- saved.
outcome(improv) :- not saved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
        for v in sorted(SURPRISES[sid].vulnerable_to):
            lines.append(asp.fact("vulnerable", sid, v))
    for cid, c in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("carrier_sense", cid, c.sense))
        if c.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", cid))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", cid, g))
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("depth", rid, r.depth))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_surprise", params.surprise),
        asp.fact("chosen_carrier", params.carrier),
        asp.fact("chosen_route", params.route),
        asp.fact("hurry", params.hurry),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "saved" if surprise_saved(CARRIERS[params.carrier], ROUTES[params.route], params.hurry, SURPRISES[params.surprise]) else "improv"


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

    smoke_cases = list(CURATED[:3])
    for i in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(i))
            smoke_cases.append(p)
        except StoryError:
            continue

    bad = 0
    for p in smoke_cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
        try:
            sample = generate(p)
            if not sample.story.strip():
                raise StoryError("empty story")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED for {p}: {err}")
            continue

    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(smoke_cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(smoke_cases)} outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a school surprise, a boggy shortcut, and a comic rescue."
    )
    ap.add_argument("--celebration", choices=CELEBRATIONS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--helper", choices=["janitor", "teacher"])
    ap.add_argument("--hurry", type=int, choices=[0, 1, 2], help="how rushed the delivery is")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible surprise/carrier pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in pool if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surprise and args.carrier:
        surprise = SURPRISES[args.surprise]
        carrier = CARRIERS[args.carrier]
        if carrier.sense < SENSE_MIN or not protects(carrier, surprise):
            raise StoryError(explain_rejection(surprise, carrier))

    combos = [
        c for c in valid_combos()
        if (args.surprise is None or c[0] == args.surprise)
        and (args.carrier is None or c[1] == args.carrier)
    ]
    if not combos:
        if args.surprise and args.carrier:
            raise StoryError(explain_rejection(SURPRISES[args.surprise], CARRIERS[args.carrier]))
        raise StoryError("(No valid combination matches the given options.)")

    surprise_id, carrier_id = rng.choice(sorted(combos))
    celebration = args.celebration or rng.choice(sorted(CELEBRATIONS))
    route = args.route or rng.choice(sorted(ROUTES))
    helper = args.helper or rng.choice(["janitor", "teacher"])
    hurry = args.hurry if args.hurry is not None else rng.randint(0, 2)
    hero, hero_gender = _pick_child(rng)
    friend, friend_gender = _pick_child(rng, avoid=hero)
    return StoryParams(
        celebration, surprise_id, carrier_id, route,
        hero, hero_gender, friend, friend_gender, helper, hurry
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        CELEBRATIONS[params.celebration],
        SURPRISES[params.surprise],
        CARRIERS[params.carrier],
        ROUTES[params.route],
        params.hero,
        params.hero_gender,
        params.friend,
        params.friend_gender,
        params.helper,
        params.hurry,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (surprise, carrier) pairs:\n")
        for surprise, carrier in combos:
            print(f"  {surprise:12} {carrier}")
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
            header = f"### {p.hero} & {p.friend}: {p.surprise} with {p.carrier} ({p.celebration}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
