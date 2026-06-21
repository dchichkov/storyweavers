#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/planetarium_spoon_ful_conflict_pirate_tale.py
=========================================================================

A standalone storyworld about children visiting a planetarium and pretending to
be pirates on a star ship. One child wants to sneak a spoon-ful of comet dust
snack into the dark dome even though food is not allowed. The conflict turns on
a grounded problem: a sticky spill in the dark could make someone slip and could
smear the star projector. A calm grown-up redirects the children toward a safe,
bright ending.

Run it
------
    python storyworlds/worlds/gpt-5.4/planetarium_spoon_ful_conflict_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/planetarium_spoon_ful_conflict_pirate_tale.py --theme pirates --snack yogurt --risk floor
    python storyworlds/worlds/gpt-5.4/planetarium_spoon_ful_conflict_pirate_tale.py --risk seat
    python storyworlds/worlds/gpt-5.4/planetarium_spoon_ful_conflict_pirate_tale.py --response napkins
    python storyworlds/worlds/gpt-5.4/planetarium_spoon_ful_conflict_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/planetarium_spoon_ful_conflict_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/planetarium_spoon_ful_conflict_pirate_tale.py --qa --json
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
BOLDNESS_INIT = 5.0
CAREFUL_TRAITS = {"careful", "patient", "sensible", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    spillable: bool = False
    slippery_when_spilled: bool = False
    can_smear_lens: bool = False
    helps_clean: bool = False
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
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    goal: str
    dark_spot: str
    role_solo: str
    role_plural: str
    send_off: str


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    spoonful: str
    color: str
    texture: str
    plural: bool = False
    spillable: bool = True
    slippery: bool = True
    smear_power: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    the: str
    place: str
    slippery_when_spilled: bool = False
    can_smear_lens: bool = False
    severity: int = 1
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spill_danger(world: World) -> list[str]:
    out: list[str] = []
    snack = world.entities.get("snack")
    risk = world.entities.get("risk")
    room = world.entities.get("room")
    if not snack or not risk or not room:
        return out
    if snack.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill_danger", risk.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["danger"] += 1
    if risk.slippery_when_spilled:
        room.meters["slippery"] += 1
    if risk.can_smear_lens:
        room.meters["smear_risk"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule(name="spill_danger", tag="physical", apply=_r_spill_danger),
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


def spill_hazard(snack: Snack, risk: Risk) -> bool:
    return snack.spillable and (risk.slippery_when_spilled or risk.can_smear_lens)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(risk: Risk, delay: int) -> int:
    return risk.severity + delay


def is_contained(response: Response, risk: Risk, delay: int) -> bool:
    return response.power >= spill_severity(risk, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_care(trait) + 1.0) + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BOLDNESS_INIT


def _do_spill(world: World, risk_ent: Entity, narrate: bool = True) -> None:
    snack = world.get("snack")
    snack.meters["spilled"] += 1
    risk_ent.meters["messy"] += 1
    if risk_ent.slippery_when_spilled:
        risk_ent.meters["slippery"] += 1
    if risk_ent.can_smear_lens:
        risk_ent.meters["smear"] += 1
    propagate(world, narrate=narrate)


def predict_spill(world: World) -> dict:
    sim = world.copy()
    _do_spill(sim, sim.get("risk"), narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "slippery": sim.get("room").meters["slippery"],
        "smear": sim.get("room").meters["smear_risk"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a field-trip afternoon, {a.id} and {b.id} stepped into the planetarium and pretended it was {theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} whispered. "Let\'s find {theme.goal}!"'
    )


def need_dark(world: World, b: Entity, theme: Theme) -> None:
    world.say(
        f"But the dome was dark and quiet, and {theme.dark_spot} made the whole room feel secret and deep."
    )
    world.say(
        f'{b.id} looked up at the stars. "It is better when we sit very still in the dark," {b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, snack: Snack) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'{a.id} peeked into a little cup from the snack table. "I know," {a.pronoun()} said. "We can take {snack.spoonful} of {snack.label} on our voyage. Pirates need treasure snacks."'
    )


def warn(world: World, b: Entity, a: Entity, snack: Snack, risk: Risk, helper: Entity) -> None:
    pred = predict_spill(world)
    b.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["slippery"] >= THRESHOLD:
        extra = " It could make the floor slick in the dark."
    elif pred["smear"] >= THRESHOLD:
        extra = " It could smear the big star projector."
    world.say(
        f'{b.id} held {a.pronoun("possessive")} sleeve. "{a.id}, no food in the planetarium," {b.pronoun()} said. "If {snack.label} spills near {risk.the}, someone could get hurt or the show could be spoiled.{extra}"'
    )
    helper.memes["watchful"] += 1


def defy(world: World, a: Entity, b: Entity, snack: Snack) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"It is only {snack.spoonful}," {a.id} said, trying to sound brave. {a.pronoun().capitalize()} tucked the little cup close and hurried toward the seats.'
    )


def back_down(world: World, a: Entity, b: Entity, helper: Entity, theme: Theme) -> None:
    a.memes["boldness"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    sibling_word = "brother" if b.type == "boy" else "sister"
    world.say(
        f'"It is not pirate treasure if it ruins the stars," {b.id} said. Because {b.id} was {a.pronoun("possessive")} older {sibling_word}, {a.id} stopped, looked around the dark dome, and gave up the idea.'
    )
    world.say(
        f"They carried the cup back to the snack table and went to sit quietly for the show instead."
    )
    helper.memes["trust"] += 1


def spill(world: World, snack: Snack, risk: Risk) -> None:
    _do_spill(world, world.get("risk"))
    if risk.slippery_when_spilled:
        end = "and a shiny patch spread across the walkway."
    else:
        end = "and a sticky streak reached toward the projector stand."
    world.say(
        f"As {a_or_an(snack.color)} {snack.color} spoon-ful wobbled in the cup, it tipped. A blob of {snack.texture} {snack.label} splashed onto {risk.the}, {end}"
    )


def alarm(world: World, b: Entity, risk: Risk, helper: Entity) -> None:
    if risk.slippery_when_spilled:
        world.say(f'"Stop! The floor!" {b.id} cried.')
    else:
        world.say(f'"Stop! The projector!" {b.id} cried.')
    world.say(f'"{helper.label_word.upper()}!"')


def rescue(world: World, helper: Entity, response: Response, risk: Risk, theme: Theme) -> None:
    world.get("snack").meters["spilled"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.get("room").meters["slippery"] = 0.0
    world.get("room").meters["smear_risk"] = 0.0
    world.get("risk").meters["messy"] = 0.0
    world.get("risk").meters["slippery"] = 0.0
    world.get("risk").meters["smear"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} came quickly and {response.text.replace('{risk}', risk.label)}."
    )
    world.say(
        f"In a moment the dark room was safe again, and the two little {theme.role_plural} stood very still with warm cheeks."
    )


def lesson(world: World, helper: Entity, a: Entity, b: Entity, snack: Snack) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For one small moment, nobody said anything at all.")
    world.say(
        f'Then {helper.label_word} knelt beside them. "I am glad you called right away," {helper.pronoun()} said softly. "Food stays at the snack table. In the dark, even one {snack.spoonful} can make a big problem."'
    )
    world.say(f'"We understand," whispered {b.id} and {a.id} together.')


def safe_end(world: World, helper: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safe"] += 1
    world.say(
        f"After the show, {helper.label_word} had a better pirate idea. {helper.pronoun().capitalize()} handed them paper star maps and let them point with a small red flashlight in the bright hallway."
    )
    world.say(
        f'"Now," {helper.pronoun()} smiled, "what does {theme.role_solo} carry in a planetarium?"'
    )
    world.say(f'"Quiet feet and careful hands!" said {a.id} and {b.id}.')
    world.say(
        f"And the little {theme.role_plural} {theme.send_off} under the posters of moons and comets, brave enough to choose the safe way."
    )


def rescue_fail(world: World, helper: Entity, response: Response, risk: Risk) -> None:
    room = world.get("room")
    room.meters["danger"] += 1
    if risk.slippery_when_spilled:
        room.meters["slippery"] += 1
    if risk.can_smear_lens:
        room.meters["smear_risk"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {response.fail.replace('{risk}', risk.label)}."
    )
    if risk.slippery_when_spilled:
        world.say(
            "The sticky patch spread farther across the dark walkway, and the show had to stop while lights blinked on."
        )
    else:
        world.say(
            "A sticky smear reached the projector housing, and the stars on the ceiling went blurry and strange."
        )


def sad_end(world: World, helper: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] += 1
    world.say(
        f"The visitors had to leave their seats while the grown-ups cleaned the mess. {a.id} and {b.id} stood by the wall, feeling much smaller than before."
    )
    world.say(
        f'{helper.label_word.capitalize()} put a kind hand on their shoulders. "No one is hurt, and that matters most," {helper.pronoun()} said. "But the stars had to go dark because food was carried where it should not have been."'
    )
    world.say(
        f"After that, whenever the children entered a dark museum room, they checked their hands first and left snacks behind."
    )


def tell(
    theme: Theme,
    snack: Snack,
    risk: Risk,
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    helper_type: str = "teacher",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 7,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
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
    helper = world.add(Entity(
        id="Guide",
        kind="character",
        type=helper_type,
        role="helper",
        label="the guide",
    ))
    room = world.add(Entity(id="room", type="room", label="the dome"))
    snack_ent = world.add(Entity(
        id="snack",
        type="snack",
        label=snack.label,
        phrase=snack.phrase,
        spillable=snack.spillable,
    ))
    risk_ent = world.add(Entity(
        id="risk",
        type="risk",
        label=risk.label,
        slippery_when_spilled=risk.slippery_when_spilled,
        can_smear_lens=risk.can_smear_lens,
    ))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["trust"] = float(trust)
    b.memes["care"] = initial_care(trait)

    play_setup(world, a, b, theme)
    need_dark(world, b, theme)

    world.para()
    tempt(world, a, snack)
    warn(world, b, a, snack, risk, helper)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, helper, theme)
        world.para()
        safe_end(world, helper, a, b, theme)
        severity = 0
        contained = True
    else:
        defy(world, a, b, snack)
        world.para()
        spill(world, snack, risk)
        alarm(world, b, risk, helper)
        severity = spill_severity(risk, delay)
        world.get("risk").meters["severity"] = float(severity)
        contained = is_contained(response, risk, delay)
        world.para()
        if contained:
            rescue(world, helper, response, risk, theme)
            lesson(world, helper, a, b, snack)
            world.para()
            safe_end(world, helper, a, b, theme)
        else:
            rescue_fail(world, helper, response, risk)
            sad_end(world, helper, a, b, theme)

    outcome = "averted" if averted else ("contained" if contained else "spoiled")
    world.facts.update(
        instigator=a,
        cautioner=b,
        helper=helper,
        theme=theme,
        snack_cfg=snack,
        snack=snack_ent,
        risk_cfg=risk,
        risk=risk_ent,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        spilled=world.get("risk").meters["severity"] >= 0 and not averted,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a moonlit pirate harbor in the sky",
        rig="The round seats felt like ship rails, the glowing dots looked like treasure stars, and the dark dome curved overhead like a giant night sea.",
        captain="Captain",
        mate="Lookout",
        goal="the lost comet chest",
        dark_spot="the aisle between the seats and the projector island",
        role_solo="a sky pirate",
        role_plural="sky pirates",
        send_off="sailed down the hallway",
    ),
    "explorers": Theme(
        id="explorers",
        scene="a secret cave of stars",
        rig="The curved ceiling felt like stone above them, the seats were little ledges, and the tiny lights looked like gems hidden in the dark.",
        captain="Leader",
        mate="Scout",
        goal="the hidden star map",
        dark_spot="the quiet path around the middle machine",
        role_solo="an explorer",
        role_plural="explorers",
        send_off="set off down the hallway",
    ),
}

SNACKS = {
    "yogurt": Snack(
        id="yogurt",
        label="blueberry yogurt",
        phrase="a little cup of blueberry yogurt",
        spoonful="spoon-ful",
        color="purple-blue",
        texture="smooth",
        slippery=True,
        smear_power=1,
        tags={"snack", "spill", "yogurt"},
    ),
    "pudding": Snack(
        id="pudding",
        label="chocolate pudding",
        phrase="a little cup of chocolate pudding",
        spoonful="spoon-ful",
        color="brown",
        texture="silky",
        slippery=True,
        smear_power=1,
        tags={"snack", "spill", "pudding"},
    ),
    "applesauce": Snack(
        id="applesauce",
        label="applesauce",
        phrase="a little cup of applesauce",
        spoonful="spoon-ful",
        color="golden",
        texture="sticky",
        slippery=True,
        smear_power=1,
        tags={"snack", "spill", "applesauce"},
    ),
}

RISKS = {
    "floor": Risk(
        id="floor",
        label="floor",
        the="the floor by the aisle",
        place="by the aisle",
        slippery_when_spilled=True,
        can_smear_lens=False,
        severity=2,
        tags={"floor", "slip"},
    ),
    "projector": Risk(
        id="projector",
        label="projector",
        the="the projector stand",
        place="near the projector",
        slippery_when_spilled=False,
        can_smear_lens=True,
        severity=2,
        tags={"projector", "museum"},
    ),
    "seat": Risk(
        id="seat",
        label="seat",
        the="the velvet seat",
        place="on a seat",
        slippery_when_spilled=False,
        can_smear_lens=False,
        severity=1,
        tags={"seat"},
    ),
}

RESPONSES = {
    "close_clean": Response(
        id="close_clean",
        sense=3,
        power=3,
        text="closed the aisle, switched on a small work light, and wiped the spill before anyone stepped in it",
        fail="closed the aisle and dabbed at the {risk}, but the mess had already spread too far in the dark",
        qa_text="closed the aisle and cleaned the spill quickly",
        tags={"clean", "adult_help"},
    ),
    "cover_and_wipe": Response(
        id="cover_and_wipe",
        sense=3,
        power=2,
        text="set a bright cone over the spot and cleaned the mess with careful wipes",
        fail="set a cone by the {risk}, but the sticky mess had already reached too far to fix at once",
        qa_text="marked the spot and wiped the spill away",
        tags={"clean", "adult_help"},
    ),
    "napkins": Response(
        id="napkins",
        sense=1,
        power=1,
        text="handed over a few napkins and hoped the children could manage it alone",
        fail="handed over napkins, but the dark room needed a quicker grown-up fix than that",
        qa_text="gave them napkins",
        tags={"napkins"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "patient", "thoughtful", "sensible", "gentle"]


@dataclass
class StoryParams:
    theme: str
    snack: str
    risk: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    helper: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 7
    seed: Optional[int] = None


KNOWLEDGE = {
    "planetarium": [(
        "What is a planetarium?",
        "A planetarium is a dark room with a dome ceiling where people can watch stars and planets appear above them. It helps visitors learn about the sky."
    )],
    "spill": [(
        "Why can a spill be dangerous in a dark room?",
        "A spill can make the floor slippery, and in the dark people may not see it in time. That is why grown-ups clean spills quickly."
    )],
    "snack": [(
        "Why do some places ask people not to bring snacks inside?",
        "Snacks can spill, make a mess, and distract from what everyone came to see. In special places, clean hands and careful walking help protect the room."
    )],
    "projector": [(
        "What does a projector do in a planetarium?",
        "A projector shines pictures of stars and planets onto the dome. If it gets dirty or blocked, the sky show can look wrong."
    )],
    "slip": [(
        "What does it mean to slip?",
        "To slip means your feet slide when the ground is slick. You can fall if you are not careful."
    )],
    "clean": [(
        "Why is it good to ask a grown-up for help with a spill?",
        "A grown-up can block the area, bring the right cleaning things, and keep everyone safe. Asking for help fast can stop a small mess from becoming a bigger problem."
    )],
}
KNOWLEDGE_ORDER = ["planetarium", "snack", "spill", "projector", "slip", "clean"]


def a_or_an(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme_id in THEMES:
        for snack_id, snack in SNACKS.items():
            for risk_id, risk in RISKS.items():
                if spill_hazard(snack, risk):
                    combos.append((theme_id, snack_id, risk_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    snack = f["snack_cfg"]
    theme = f["theme"]
    risk = f["risk_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a pirate-flavored story for a 3-to-5-year-old set in a planetarium. Include the exact word "{snack.spoonful}" and a conflict about a snack in the dark.',
            f"Tell a gentle near-miss tale where {a.id} wants to carry a {snack.spoonful} of {snack.label}, but {b.id} stops the mistake before anything spills.",
            f"Write a story where children pretend to be {theme.role_plural}, face a conflict in a dark dome, and end by choosing careful hands instead of secret snacks.",
        ]
    if outcome == "spoiled":
        return [
            f'Write a cautionary pirate-style story in a planetarium that includes "{snack.spoonful}" and a spill that stops the star show.',
            f"Tell a story where {a.id} ignores {b.id}'s warning about carrying {snack.label} near {risk.the}, and the room has to stop for cleanup.",
            f"Write a child-facing museum safety story with conflict, a mistake in the dark, and a sadder ending that still keeps everyone safe.",
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old set in a planetarium. Include the exact word "{snack.spoonful}" and a conflict about bringing food into the dark.',
        f"Tell a gentle cautionary story where {a.id} carries {snack.label} toward {risk.the}, a grown-up helps quickly, and the children learn a safer way.",
        f"Write a complete story with a dark star room, a small spill problem, and an ending image that shows what changed.",
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    theme = f["theme"]
    snack = f["snack_cfg"]
    risk = f["risk_cfg"]
    response = f["response"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, visiting a planetarium with a guide nearby. They pretend to be {theme.role_plural} while they look at the stars."
        ),
        (
            "Why was there a conflict?",
            f"The conflict began because {a.id} wanted to carry {snack.spoonful} of {snack.label} into the dark dome, but {b.id} knew food was not allowed there. The warning mattered because a spill near {risk.the} could make the room unsafe or spoil the show."
        ),
        (
            f"What did {b.id} warn {a.id} about?",
            f"{b.id} warned that even one {snack.spoonful} could become a real problem in the dark. If {snack.label} spilled near {risk.the}, someone could slip or the planetarium equipment could be messed up."
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend([
            (
                f"What happened after {b.id} spoke up?",
                f"{a.id} listened and carried the snack back instead of sneaking it into the dome. Because the risky choice stopped early, nothing spilled and the show stayed calm."
            ),
            (
                "How did the story end?",
                f"It ended with the children using paper star maps and a little red flashlight in the bright hallway. That ending shows they still got a pirate adventure, but in a careful way."
            ),
        ])
    elif f["outcome"] == "contained":
        qa.extend([
            (
                "How did the grown-up fix the problem?",
                f"The guide {response.qa_text.replace('{risk}', risk.label)}. Acting quickly mattered because the dark room could have turned a tiny mess into a bigger danger."
            ),
            (
                "What did the children learn?",
                f"They learned that food belongs at the snack table, not in the dark dome. They also learned that calling a grown-up right away is the fastest way to keep people safe."
            ),
            (
                "How did the story end?",
                f"It ended with star maps in the bright hallway and the children saying, 'Quiet feet and careful hands!' The final image proves they changed how they explored."
            ),
        ])
    else:
        qa.extend([
            (
                "Did anyone get hurt?",
                "No one got hurt, and that is the most important part. But the spill was bad enough that the show had to stop while grown-ups cleaned up."
            ),
            (
                "How did the story end?",
                f"It ended with the children waiting by the wall while the room was cleaned. They left snacks behind after that because they understood how one careless choice spoiled the stars for everyone."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"planetarium", "spill", "snack"}
    risk = f["risk_cfg"]
    response = f["response"]
    if risk.can_smear_lens:
        tags.add("projector")
    if risk.slippery_when_spilled:
        tags.add("slip")
    if response.id in {"close_clean", "cover_and_wipe"}:
        tags.add("clean")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        snack="yogurt",
        risk="floor",
        response="close_clean",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        helper="teacher",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        theme="pirates",
        snack="pudding",
        risk="projector",
        response="cover_and_wipe",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        helper="teacher",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="explorers",
        snack="applesauce",
        risk="projector",
        response="cover_and_wipe",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        helper="teacher",
        trait="careful",
        delay=1,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="pirates",
        snack="yogurt",
        risk="floor",
        response="close_clean",
        instigator="Ben",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        helper="teacher",
        trait="sensible",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
]


def explain_rejection(snack: Snack, risk: Risk) -> str:
    if not (risk.slippery_when_spilled or risk.can_smear_lens):
        return (
            f"(No story: spilling {snack.label} on {risk.the} would make a mess, but not a strong enough danger for this conflict. Pick the floor or the projector instead.)"
        )
    return "(No story: this snack and risk do not make a clear enough planetarium hazard.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={response.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], RISKS[params.risk], params.delay) else "spoiled"


ASP_RULES = r"""
hazard(S, R) :- snack(S), risk(R), spillable(S), slippery_when_spilled(R).
hazard(S, R) :- snack(S), risk(R), spillable(S), can_smear_lens(R).
sensible(Resp) :- response(Resp), sense(Resp, S), sense_min(M), S >= M.
valid(T, S, R) :- theme(T), snack(S), risk(R), hazard(S, R).

care_now(Trait) :- trait(Trait), careful_trait(Trait).
init_care(5) :- trait(Trait), care_now(Trait).
init_care(3) :- trait(Trait), not care_now(Trait).
older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- older_sibling, authority(A), boldness_init(B), A > B.

severity(V) :- chosen_risk(R), risk_severity(R, RS), delay(D), V = RS + D.
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spoiled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.spillable:
            lines.append(asp.fact("spillable", sid))
    for rid, risk in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if risk.slippery_when_spilled:
            lines.append(asp.fact("slippery_when_spilled", rid))
        if risk.can_smear_lens:
            lines.append(asp.fact("can_smear_lens", rid))
        lines.append(asp.fact("risk_severity", rid, risk.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_risk", params.risk),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
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

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - defensive for batch generation
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a planetarium conflict about a spoon-ful of snack in the dark."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["teacher", "mother", "father"], help="grown-up who helps")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the spill gets before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.risk:
        risk = RISKS[args.risk]
        snack = SNACKS[args.snack] if args.snack else next(iter(SNACKS.values()))
        if not spill_hazard(snack, risk):
            raise StoryError(explain_rejection(snack, risk))
    if args.snack and args.risk:
        snack = SNACKS[args.snack]
        risk = RISKS[args.risk]
        if not spill_hazard(snack, risk):
            raise StoryError(explain_rejection(snack, risk))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.snack is None or combo[1] == args.snack)
        and (args.risk is None or combo[2] == args.risk)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, snack, risk = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    helper = args.helper or "teacher"
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme,
        snack=snack,
        risk=risk,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        helper=helper,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        snack = SNACKS[params.snack]
        risk = RISKS[params.risk]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if not spill_hazard(snack, risk):
        raise StoryError(explain_rejection(snack, risk))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        theme=theme,
        snack=snack,
        risk=risk,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        helper_type=params.helper,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(f"{len(combos)} compatible (theme, snack, risk) combos:\n")
        for theme, snack, risk in combos:
            print(f"  {theme:10} {snack:10} {risk}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.snack} near {p.risk} ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
