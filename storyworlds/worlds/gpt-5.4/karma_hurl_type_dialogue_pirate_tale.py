#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/karma_hurl_type_dialogue_pirate_tale.py
==================================================================

A standalone story world for a small pirate-tale domain: two young pirates hear
a frightened creature flapping high in the rigging, and one child wants to
* hurl * something upward to knock it free. The other child warns that this is
the wrong * type * of rescue. A calm grown-up pirate then uses a gentler method,
and the ending shows what kind of pirate the children choose to become.

The seed words "karma", "hurl", and "type" are woven into the dialogue and the
story's lesson. The world model tracks simple physical meters and emotional
memes, and the prose is rendered from state rather than from a single frozen
template.

Run it
------
    python storyworlds/worlds/gpt-5.4/karma_hurl_type_dialogue_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/karma_hurl_type_dialogue_pirate_tale.py --victim gull --throw boot
    python storyworlds/worlds/gpt-5.4/karma_hurl_type_dialogue_pirate_tale.py --response shout
    python storyworlds/worlds/gpt-5.4/karma_hurl_type_dialogue_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/karma_hurl_type_dialogue_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/karma_hurl_type_dialogue_pirate_tale.py --trace
    python storyworlds/worlds/gpt-5.4/karma_hurl_type_dialogue_pirate_tale.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "gentle", "sensible", "steady"}


def sentence_case(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    throwable: bool = False
    vulnerable: bool = False
    rescue_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "captain_female", "woman"}
        male = {"boy", "father", "captain_male", "man"}
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
            "captain_female": "captain",
            "captain_male": "captain",
        }.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    setup: str
    mast: str
    water: str
    role_plural: str
    sendoff: str


@dataclass
class Victim:
    id: str
    label: str
    phrase: str
    snag: str
    cry: str
    home: str
    fragility: int
    vulnerable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def The(self) -> str:
        return self.the.capitalize()

    @property
    def Phrase(self) -> str:
        return sentence_case(self.phrase)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class ThrowThing:
    id: str
    label: str
    phrase: str
    hurl_line: str
    impact: int
    plural: bool = False
    throwable: bool = True
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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


def _r_distress(world: World) -> list[str]:
    out: list[str] = []
    victim = world.get("victim")
    if victim.meters["snagged"] >= THRESHOLD:
        sig = ("distress", "victim")
        if sig not in world.fired:
            world.fired.add(sig)
            victim.memes["fear"] += 1
            for kid in world.kids():
                kid.memes["worry"] += 1
            out.append("__distress__")
    return out


def _r_hurt_guilt(world: World) -> list[str]:
    out: list[str] = []
    victim = world.get("victim")
    if victim.meters["hurt"] >= THRESHOLD:
        sig = ("guilt", "victim")
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["guilt"] += 1
            out.append("__hurt__")
    return out


CAUSAL_RULES = [
    Rule("distress", "emotional", _r_distress),
    Rule("hurt_guilt", "emotional", _r_hurt_guilt),
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


def hazard_at_risk(throw: ThrowThing, victim: Victim) -> bool:
    return throw.throwable and victim.vulnerable and throw.impact > 0 and victim.fragility > 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def rescue_severity(throw: ThrowThing, victim: Victim, delay: int) -> int:
    return throw.impact + victim.fragility + delay


def is_rescued(response: Response, throw: ThrowThing, victim: Victim, delay: int) -> bool:
    return response.power >= rescue_severity(throw, victim, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def predict_hurl(world: World, throw_id: str) -> dict:
    sim = world.copy()
    _do_hurl(sim, sim.get(throw_id), narrate=False)
    victim = sim.get("victim")
    return {
        "hurt": victim.meters["hurt"] >= THRESHOLD,
        "fear": victim.memes["fear"],
    }


def _do_hurl(world: World, throw_ent: Entity, narrate: bool = True) -> None:
    victim = world.get("victim")
    victim.meters["hurt"] += 1
    victim.meters["snagged"] += 1
    victim.meters["panic"] += throw_ent.meters["impact"]
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, scene: Scene) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright tide morning, {a.id} and {b.id} turned {scene.place} into a grand pirate deck. "
        f"{scene.setup}"
    )
    world.say(
        f'"Captain {a.id} and Mate {b.id}!" {a.id} cried. "Let\'s make this the bravest ship in the harbor!"'
    )


def trouble_appears(world: World, b: Entity, victim: Victim, scene: Scene) -> None:
    world.get("victim").meters["snagged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a sharp little sound floated down from {scene.mast}. {victim.Phrase} was {victim.snag}, "
        f"and every frightened flap shook the rope."
    )
    world.say(f'"Listen," {b.id} whispered. "{victim.cry}"')


def temptation(world: World, a: Entity, throw: ThrowThing) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"{a.id} pointed up at the rigging. {throw.hurl_line}"
    )
    world.say("For one bold second, the idea felt quick and clever.")


def warning(world: World, b: Entity, a: Entity, throw: ThrowThing, victim: Victim) -> None:
    pred = predict_hurl(world, "throw")
    b.memes["caution"] += 1
    world.facts["predicted_hurt"] = pred["hurt"]
    extra = ""
    if pred["hurt"]:
        extra = f" {b.pronoun().capitalize()} could almost picture {victim.the} jerking harder in the rope."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "No, {a.id}. That is the wrong type of rescue. '
        f'If you hurl {throw.phrase}, you might hurt {victim.the} instead of helping."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, throw: ThrowThing) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"I can do it," {a.id} said. Because {a.pronoun()} was the older one, '
            f'{b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"I can do it," {a.id} said, and before anyone could stop {a.pronoun("object")}, {a.pronoun()} wound up to throw.')


def back_down(world: World, a: Entity, b: Entity, throw: ThrowThing) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} held still with {throw.the if hasattr(throw, "the") else throw.phrase} in hand, then let out a breath. '
        f'"You\'re right," {a.pronoun()} said. "That would be bad pirate karma."'
    )
    world.say(
        f"{a.id} lowered {throw.phrase} and stepped back from the rail."
    )


def hurl(world: World, a: Entity, throw_ent: Entity, throw: ThrowThing, victim: Victim) -> None:
    _do_hurl(world, throw_ent)
    world.say(
        f"{a.id} gave one mighty swing and let it fly. The {throw.label} did not free {victim.the} at all. "
        f"It smacked the rope beside {victim.pronoun('object')}, and {victim.the} flapped in fresh panic."
    )


def alarm(world: World, b: Entity, captain: Entity, victim: Victim) -> None:
    world.say(f'"Captain! {victim.The} is scared!" {b.id} shouted.')


def rescue(world: World, captain: Entity, response: Response, victim: Victim) -> None:
    v = world.get("victim")
    v.meters["snagged"] = 0.0
    v.meters["panic"] = 0.0
    v.meters["hurt"] = 0.0
    v.memes["fear"] = 0.0
    world.say(
        f"{sentence_case(captain.label)} came at once and {response.text.replace('{victim}', victim.the)}."
    )
    world.say(
        f"Soon {victim.the} was free again, trembling but safe, with both wings tucked close."
    )


def rescue_fail(world: World, captain: Entity, response: Response, victim: Victim) -> None:
    v = world.get("victim")
    v.meters["snagged"] = 0.0
    v.meters["panic"] += 1
    v.meters["hurt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{sentence_case(captain.label)} came at once and {response.fail.replace('{victim}', victim.the)}."
    )
    world.say(
        f"{victim.The} got loose at last, but flew away crooked and frightened over the water."
    )


def lesson(world: World, captain: Entity, a: Entity, b: Entity, throw: ThrowThing, outcome: str) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["worry"] = 0.0
    if outcome == "safe":
        world.say(
            f'{sentence_case(captain.label)} knelt beside them. "A real pirate does not hurl first and think later," '
            f'{captain.pronoun()} said softly. "Good pirate karma comes from helping with gentle hands and the right type of tool."'
        )
    else:
        world.say(
            f'{sentence_case(captain.label)} knelt beside them. "You meant to help, but a quick throw can turn fear into pain," '
            f'{captain.pronoun()} said softly. "If we want good karma on this ship, we must choose the right type of help."'
        )
    world.say(f'"We understand," whispered {b.id} and {a.id} together.')


def ending_safe(world: World, a: Entity, b: Entity, scene: Scene, victim: Victim) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["kindness"] += 1
    world.say(
        f"Before sunset, {victim.the} circled once above {scene.water} and gave a bright cry, as if the whole harbor had been thanked."
    )
    world.say(
        f'{a.id} smiled at {b.id}. "From now on," {a.pronoun()} said, "we will be the type of pirates who rescue gently."'
    )
    world.say(
        f"And the two young {scene.role_plural} {scene.sendoff}, carrying a coil of soft rescue line instead of anything meant to fly."
    )


def ending_hurt(world: World, a: Entity, b: Entity, scene: Scene, victim: Victim) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["kindness"] += 1
    world.say(
        f"For a long moment, the water below {scene.place} looked very wide, and both children wished they could call {victim.the} back."
    )
    world.say(
        f'{b.id} took {a.id}\'s hand. "Next time," {b.pronoun()} said, "we will be the type of pirates who help before we boast."'
    )
    world.say(
        "They stood quietly together until the lanterns came on, and neither of them ever forgot that lesson."
    )


def tell(
    scene: Scene,
    victim: Victim,
    throw: ThrowThing,
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "gentle",
    captain_type: str = "captain_female",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type=captain_type,
        role="captain",
        label="the captain",
    ))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    v = world.add(Entity(id="victim", type="creature", label=victim.label, vulnerable=True))
    t = world.add(Entity(id="throw", type="thing", label=throw.label, throwable=True))
    t.meters["impact"] = float(throw.impact)

    opening(world, a, b, scene)
    trouble_appears(world, b, victim, scene)

    world.para()
    temptation(world, a, throw)
    warning(world, b, a, throw, victim)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, throw)
        world.para()
        rescue(world, captain, response, victim)
        lesson(world, captain, a, b, throw, "safe")
        world.para()
        ending_safe(world, a, b, scene, victim)
        outcome = "averted"
    else:
        defy(world, a, b, throw)
        world.para()
        hurl(world, a, t, throw, victim)
        alarm(world, b, captain, victim)
        contained = is_rescued(response, throw, victim, delay)
        world.para()
        if contained:
            rescue(world, captain, response, victim)
            lesson(world, captain, a, b, throw, "safe")
            world.para()
            ending_safe(world, a, b, scene, victim)
            outcome = "safe"
        else:
            rescue_fail(world, captain, response, victim)
            lesson(world, captain, a, b, throw, "hurt")
            world.para()
            ending_hurt(world, a, b, scene, victim)
            outcome = "hurt"

    world.facts.update(
        scene=scene,
        victim_cfg=victim,
        throw_cfg=throw,
        response=response,
        instigator=a,
        cautioner=b,
        captain=captain,
        relation=relation,
        delay=delay,
        outcome=outcome,
        rescued=(outcome in {"averted", "safe"}),
        predicted_hurt=world.facts.get("predicted_hurt", False),
        severity=rescue_severity(throw, victim, delay),
    )
    return world


SCENES = {
    "harbor": Scene(
        "harbor",
        "the old harbor boat",
        "The mop was their mast, a painted crate was their treasure chest, and a striped cloth snapped like a proud black flag.",
        "the highest yard of the little mast",
        "the blue harbor water",
        "pirates",
        "marched the deck more softly than before",
    ),
    "cove": Scene(
        "cove",
        "the cove skiff",
        "A barrel was their cannon, a driftwood board was their gangplank, and a basket of shells gleamed like treasure.",
        "the crooked spar above the bow",
        "the green cove water",
        "pirates",
        "sailed their pretend ship into a gentler game",
    ),
    "dock": Scene(
        "dock",
        "the docked sloop",
        "A coil of rope was their sea-serpent, a crate of oranges became treasure, and the bell rope rang like a captain's call.",
        "the rope ladder near the mast",
        "the shining water",
        "pirates",
        "set off to guard the deck with kinder eyes",
    ),
}

VICTIMS = {
    "gull": Victim(
        "gull",
        "gull",
        "a little gull with silver wings",
        "snagged in a loose bit of fishing net",
        "It sounds scared.",
        "the harbor wall",
        2,
        tags={"gull", "animal", "rescue"},
    ),
    "tern": Victim(
        "tern",
        "tern",
        "a white tern with a forked tail",
        "caught by one leg in a string near the sail",
        "That bird is crying.",
        "the open cove",
        2,
        tags={"bird", "animal", "rescue"},
    ),
    "parrot": Victim(
        "parrot",
        "parrot",
        "a bright green parrot",
        "tangled in the bunting above the deck",
        "Its wings are stuck.",
        "the warm mast-top",
        3,
        tags={"parrot", "animal", "rescue"},
    ),
}

THROWS = {
    "boot": ThrowThing(
        "boot",
        "boot",
        "a heavy deck boot",
        '"I know! I can hurl this boot and knock the rope loose!"',
        2,
        tags={"boot", "throw"},
    ),
    "orange": ThrowThing(
        "orange",
        "orange",
        "an orange from the treasure crate",
        '"I know! I can hurl this orange and pop the knot apart!"',
        1,
        tags={"orange", "throw"},
    ),
    "mug": ThrowThing(
        "mug",
        "mug",
        "a wooden mug",
        '"I know! I can hurl this mug and make the string jump free!"',
        2,
        tags={"mug", "throw"},
    ),
}

RESPONSES = {
    "ladder": Response(
        "ladder",
        3,
        5,
        "climbed the ladder with a soft blanket over one arm, eased the knot loose, and wrapped {victim} gently before bringing it down",
        "climbed the ladder, but the frightened flapping made {victim} twist away before the knot could be freed",
        "climbed up carefully and brought the creature down in a soft blanket",
        tags={"ladder", "animal_rescue"},
    ),
    "lower_sail": Response(
        "lower_sail",
        3,
        4,
        "loosened the line and lowered the snagged cloth until {victim} could be untangled at deck level",
        "pulled on the line, but the snag only tightened and {victim} struggled harder",
        "lowered the cloth and untangled the creature safely on deck",
        tags={"rope", "animal_rescue"},
    ),
    "boat_hook": Response(
        "boat_hook",
        2,
        3,
        "used the smooth end of the boat hook to lift the string away until {victim} slipped free",
        "reached up with the boat hook, but {victim} was too panicked and flew off hurt the moment the string gave way",
        "used the smooth end of a boat hook to lift the string away and free the creature",
        tags={"boat_hook", "animal_rescue"},
    ),
    "shout": Response(
        "shout",
        1,
        1,
        "stood below and called for {victim} to calm down",
        "called up from the deck, but words alone could not undo the tangle",
        "called to the creature from below",
        tags={"voice"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Zoe", "Ella", "Maya", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli"]
TRAITS = ["careful", "gentle", "sensible", "steady", "kind", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for scene in SCENES:
        for tid, throw in THROWS.items():
            for vid, victim in VICTIMS.items():
                if hazard_at_risk(throw, victim):
                    combos.append((scene, tid, vid))
    return combos


@dataclass
class StoryParams:
    scene: str
    throw: str
    victim: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    captain: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    seed: Optional[int] = None


KNOWLEDGE = {
    "animal": [(
        "Why should you be gentle with a trapped animal?",
        "A trapped animal is already frightened, so rough actions can hurt it more. Gentle help gives it a better chance to calm down and stay safe."
    )],
    "rescue": [(
        "What is a rescue?",
        "A rescue is when you help someone or something get out of danger. A good rescue uses the safest tool and the calmest plan."
    )],
    "throw": [(
        "Why is throwing things at a trapped bird a bad idea?",
        "Throwing something can hit the bird or scare it into struggling harder. That can make the problem worse instead of better."
    )],
    "ladder": [(
        "Why can a ladder help in a rescue?",
        "A ladder lets a grown-up reach something high without throwing anything. That makes it easier to use careful hands."
    )],
    "rope": [(
        "What does lowering a rope or sail do?",
        "Lowering a rope or sail can bring a problem down to where hands can reach it safely. It is often better than trying to knock something loose."
    )],
    "boat_hook": [(
        "What is a boat hook?",
        "A boat hook is a long pole used on boats to reach things without climbing too far. Grown-ups can use the smooth end carefully to move rope or lines."
    )],
    "karma": [(
        "What does karma mean in this story?",
        "Here karma means that your choices bring good or bad results back to you. Kind choices tend to lead to kinder endings."
    )],
}
KNOWLEDGE_ORDER = ["animal", "rescue", "throw", "ladder", "rope", "boat_hook", "karma"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["instigator"], f["cautioner"]
    victim, throw, scene = f["victim_cfg"], f["throw_cfg"], f["scene"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate tale for a 3-to-5-year-old with lively dialogue where two children find {victim.phrase} trapped high above {scene.place}. '
        f'Include the words "karma", "hurl", and "type".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle pirate story where {a.id} wants to hurl {throw.phrase}, but {b.id}, an older sibling, stops the mistake before it happens.",
            'Write a story in which a child says "wrong type of rescue," a captain helps kindly, and the ending shows what good pirate karma looks like.',
        ]
    if outcome == "hurt":
        return [
            base,
            f"Tell a cautionary pirate story where {a.id} throws first, the rescue goes badly, and the children learn that boasting is the wrong type of help.",
            "Write a sadder pirate tale where the lesson about karma comes after a frightened creature is hurt and flies away.",
        ]
    return [
        base,
        f"Tell a pirate rescue story where {a.id} wants to hurl {throw.phrase}, {b.id} warns against it, and a captain uses a gentler method.",
        'Write a child-facing pirate tale with dialogue, a clear mistake, and an ending where the children decide what type of pirates they want to be.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, captain = f["instigator"], f["cautioner"], f["captain"]
    scene, victim, throw, response = f["scene"], f["victim_cfg"], f["throw_cfg"], f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, f['relation'])}, {a.id} and {b.id}, and the captain who helped them. They were playing pirates at {scene.place} when they found {victim.phrase} in trouble."
        ),
        (
            "What problem did the children discover?",
            f"They found {victim.phrase} {victim.snag}. That made the rescue feel urgent, which is why {a.id} reached for a quick but risky idea."
        ),
        (
            f"What did {a.id} want to do?",
            f"{a.id} wanted to hurl {throw.phrase} upward to knock the tangle free. {b.id} warned that this was the wrong type of rescue because it could frighten or hurt {victim.the}."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"Did {a.id} throw anything?",
            f"No. {a.id} listened and backed down before throwing, so the captain could help without the rescue getting worse. That changed the whole story from a mistake into a near-miss."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely. {victim.the} was freed, and the children promised to be the type of pirates who rescue gently."
        ))
    elif f["outcome"] == "safe":
        qa.append((
            f"What happened when {a.id} threw {throw.phrase}?",
            f"The throw did not help at all. It made {victim.the} flap in fresh panic, which is why {b.id} called for the captain right away."
        ))
        qa.append((
            "How did the captain fix the problem?",
            f"The captain {response.qa_text.replace('{victim}', victim.the)}. The careful method worked because it was stronger and gentler than throwing."
        ))
        qa.append((
            "What did the children learn?",
            "They learned that good pirate karma comes from helping gently, not from showing off. By the end, they chose to be the type of pirates who think first."
        ))
    else:
        qa.append((
            "Did the rescue go well?",
            f"No. The captain tried to help, but {victim.the} flew away hurt and frightened. The sad ending came because the quick throw and weak rescue made the danger harder to fix."
        ))
        qa.append((
            "What did the children learn?",
            "They learned that boasting and throwing can turn a hard problem into a worse one. The captain used the word karma to remind them that careless choices bring painful results."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"animal", "rescue", "throw", "karma"}
    tags |= set(f["response"].tags)
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
        flags = [n for n, on in (("throwable", e.throwable), ("vulnerable", e.vulnerable), ("rescue_tool", e.rescue_tool)) if on]
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
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "boot", "gull", "ladder", "Tom", "boy", "Lily", "girl", "captain_female", "gentle", 0, 6, 4, "siblings"),
    StoryParams("cove", "orange", "tern", "lower_sail", "Max", "boy", "Mia", "girl", "captain_male", "steady", 0, 5, 5, "friends"),
    StoryParams("dock", "mug", "parrot", "boat_hook", "Sam", "boy", "Nora", "girl", "captain_female", "careful", 1, 7, 5, "siblings"),
    StoryParams("harbor", "orange", "gull", "ladder", "Ben", "boy", "Tom", "boy", "captain_male", "gentle", 0, 5, 7, "siblings"),
]


def explain_rejection(throw: ThrowThing, victim: Victim) -> str:
    if throw.impact <= 0:
        return f"(No story: {throw.label} would not create a risky hurl at all.)"
    if not victim.vulnerable:
        return f"(No story: {victim.the} is not vulnerable, so there is no rescue danger.)"
    return f"(No story: hurling {throw.phrase} at {victim.the} does not make a sensible pirate rescue premise.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer rescue method such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "safe" if is_rescued(RESPONSES[params.response], THROWS[params.throw], VICTIMS[params.victim], params.delay) else "hurt"


ASP_RULES = r"""
hazard(T, V) :- throwable(T), vulnerable(V), impact(T, I), fragility(V, F), I > 0, F > 0.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Sn, T, V) :- scene(Sn), throw(T), victim(V), hazard(T, V).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

severity(I + F + D) :- chosen_throw(T), chosen_victim(V), impact(T, I), fragility(V, F), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
rescued :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(safe) :- not averted, rescued.
outcome(hurt) :- not averted, not rescued.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for tid, throw in THROWS.items():
        lines.append(asp.fact("throw", tid))
        if throw.throwable:
            lines.append(asp.fact("throwable", tid))
        lines.append(asp.fact("impact", tid, throw.impact))
    for vid, victim in VICTIMS.items():
        lines.append(asp.fact("victim", vid))
        if victim.vulnerable:
            lines.append(asp.fact("vulnerable", vid))
        lines.append(asp.fact("fragility", vid, victim.fragility))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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

    scenario = "\n".join([
        asp.fact("chosen_throw", params.throw),
        asp.fact("chosen_victim", params.victim),
        asp.fact("chosen_response", params.response),
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

    clingo_sens, python_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if clingo_sens == python_sens:
        print(f"OK: sensible responses match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a pirate rescue where a child wants to hurl first and think later."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--throw", choices=THROWS)
    ap.add_argument("--victim", choices=VICTIMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--captain", choices=["captain_female", "captain_male"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the problem gets before the captain reaches it")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.throw and args.victim:
        throw, victim = THROWS[args.throw], VICTIMS[args.victim]
        if not hazard_at_risk(throw, victim):
            raise StoryError(explain_rejection(throw, victim))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.scene is None or c[0] == args.scene)
        and (args.throw is None or c[1] == args.throw)
        and (args.victim is None or c[2] == args.victim)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene, throw, victim = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    captain = args.captain or rng.choice(["captain_female", "captain_male"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        scene=scene,
        throw=throw,
        victim=victim,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        captain=captain,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SCENES[params.scene],
        VICTIMS[params.victim],
        THROWS[params.throw],
        RESPONSES[params.response],
        params.instigator,
        params.instigator_gender,
        params.cautioner,
        params.cautioner_gender,
        params.trait,
        params.captain,
        params.delay,
        params.instigator_age,
        params.cautioner_age,
        params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, throw, victim) combos:\n")
        for scene, throw, victim in combos:
            print(f"  {scene:8} {throw:8} {victim}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.throw} -> {p.victim} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
