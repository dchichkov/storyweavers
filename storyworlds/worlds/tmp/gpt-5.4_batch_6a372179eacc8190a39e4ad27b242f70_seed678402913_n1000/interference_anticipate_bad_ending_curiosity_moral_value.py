#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/interference_anticipate_bad_ending_curiosity_moral_value.py
========================================================================================

A small myth-like storyworld about a curious child, a sacred sealed vessel, and
the warning that some mysteries should be met with patience. The world model
tracks a child's curiosity, a guardian's warning, the release of a harmful force,
and whether the community can contain the damage in time.

The seed words "interference" and "anticipate" appear naturally in generated
stories. The domain supports happy containment endings and bad endings where the
harm spreads too far, while keeping a clear moral shape.

Run it
------
    python storyworlds/worlds/gpt-5.4/interference_anticipate_bad_ending_curiosity_moral_value.py
    python storyworlds/worlds/gpt-5.4/interference_anticipate_bad_ending_curiosity_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/interference_anticipate_bad_ending_curiosity_moral_value.py --trace
    python storyworlds/worlds/gpt-5.4/interference_anticipate_bad_ending_curiosity_moral_value.py --qa --json
    python storyworlds/worlds/gpt-5.4/interference_anticipate_bad_ending_curiosity_moral_value.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    sealed: bool = False
    sacred: bool = False
    dangerous: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "goddess", "priestess"}
        male = {"boy", "man", "father", "god", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    wonder: str
    people: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    seal_text: str
    warning_place: str
    release_text: str
    residue_text: str
    spread: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Harm:
    id: str
    name: str
    sign: str
    touch: str
    loss: str
    ending_image: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    method: str
    fail_text: str
    qa_text: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    vessel: str
    harm: str
    aid: str
    child_name: str
    child_gender: str
    guardian_name: str
    guardian_type: str
    relation: str
    trait: str
    delay: int = 0
    child_age: int = 7
    guardian_age: int = 300
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
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_release_spreads(world: World) -> list[str]:
    out: list[str] = []
    vessel = world.entities.get("vessel")
    plague = world.entities.get("harm")
    village = world.entities.get("village")
    child = world.entities.get("child")
    guardian = world.entities.get("guardian")
    if not vessel or not plague or not village or not child or not guardian:
        return out
    if plague.meters["loose"] < THRESHOLD:
        return out
    sig = ("spread", plague.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    village.meters["danger"] += 1
    village.meters["shadow"] += 1
    child.memes["fear"] += 1
    guardian.memes["grief"] += 1
    return out


CAUSAL_RULES = [
    Rule(name="release_spreads", tag="physical", apply=_r_release_spreads),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "valley": Setting(
        id="valley",
        place="a green valley under a ring of blue mountains",
        sky="the dawn poured gold across the ridges",
        wonder="At the center of the valley stood an ancient shrine of white stone.",
        people="the valley folk",
        tags={"myth", "mountain"},
    ),
    "island": Setting(
        id="island",
        place="a bright island where cliffs looked over the sea",
        sky="morning light turned the waves to silver",
        wonder="Above the harbor stood an old temple with doors of cedar wood.",
        people="the island folk",
        tags={"myth", "sea"},
    ),
    "desert": Setting(
        id="desert",
        place="a quiet desert oasis ringed with date palms",
        sky="the evening sky blushed rose above the sand",
        wonder="Beside the spring stood a shrine carved with stars and lions.",
        people="the oasis folk",
        tags={"myth", "desert"},
    ),
}

VESSELS = {
    "jar": Vessel(
        id="jar",
        label="jar",
        phrase="a painted clay jar with a lid sealed by blue wax",
        seal_text="Do not break this seal before the festival moon.",
        warning_place="on the shrine step",
        release_text="a cold wind rushed from the jar mouth and twisted into the air",
        residue_text="Only one small silver spark stayed behind at the bottom",
        spread=2,
        tags={"jar", "seal"},
    ),
    "box": Vessel(
        id="box",
        label="box",
        phrase="a cedar box bound with a bronze clasp",
        seal_text="Open this only when the temple bell rings three times.",
        warning_place="beneath the temple lamp",
        release_text="a hiss of dark smoke uncoiled from the box and streamed away",
        residue_text="One pale bead of light still trembled inside",
        spread=3,
        tags={"box", "seal"},
    ),
    "urn": Vessel(
        id="urn",
        label="urn",
        phrase="a tall black urn tied with a braided red cord",
        seal_text="Let no impatient hand untie this cord before dawn.",
        warning_place="by the oldest pillar",
        release_text="a bitter shadow slipped from the urn and flew over the roofs",
        residue_text="A warm ember of hope still glimmered within",
        spread=2,
        tags={"urn", "seal"},
    ),
}

HARMS = {
    "night_swarm": Harm(
        id="night_swarm",
        name="the Night Swarm",
        sign="The sunshine thinned as if a giant wing had crossed the sky.",
        touch="The creatures stung the air and made children hide their faces.",
        loss="fruit fell unripe and songs died in their throats",
        ending_image="the orchard stood dim and silent under torn leaves",
        lesson="Curiosity needs wisdom, or it can trouble many hearts at once.",
        tags={"darkness", "swarm"},
    ),
    "sorrow_fog": Harm(
        id="sorrow_fog",
        name="the Sorrow Fog",
        sign="Gray mist poured along the ground and swallowed bright colors.",
        touch="It made every breath feel heavy and every footstep slow.",
        loss="market lamps went out and laughter faded from the square",
        ending_image="the empty square sat under a blanket of gray",
        lesson="Some doors stay closed for a reason, and patience guards the whole village.",
        tags={"fog", "darkness"},
    ),
    "thorn_wind": Harm(
        id="thorn_wind",
        name="the Thorn Wind",
        sign="A sharp wind whirled up and rattled every shutter in the town.",
        touch="It scratched cheeks with dust and snapped blossoms from the vines.",
        loss="the gardens bent low and the river boats knocked against the pier",
        ending_image="broken petals lay in drifts along the stones",
        lesson="A warning is a gift, and careless interference can turn wonder into harm.",
        tags={"wind", "storm"},
    ),
}

AIDS = {
    "bell_prayer": Aid(
        id="bell_prayer",
        label="bell and prayer",
        phrase="the shrine bell and the old prayer",
        method="rang the bronze bell, spoke the oldest prayer, and drew a circle of bright salt around the shrine",
        fail_text="rang the bronze bell and spoke the prayer, but the harm had already raced beyond the shrine",
        qa_text="used the shrine bell, the old prayer, and a circle of bright salt",
        sense=3,
        power=3,
        tags={"prayer", "bell", "salt"},
    ),
    "sun_mirror": Aid(
        id="sun_mirror",
        label="sun mirror",
        phrase="the temple's sun mirror",
        method="lifted the temple's sun mirror and threw a golden beam across the square until the dark force shrank back",
        fail_text="raised the sun mirror, but the dark force had already spread wider than the beam could reach",
        qa_text="used the temple's sun mirror to drive the harm back",
        sense=3,
        power=4,
        tags={"mirror", "sun"},
    ),
    "reed_flute": Aid(
        id="reed_flute",
        label="reed flute",
        phrase="a sacred reed flute",
        method="played the sacred reed flute and called the village lamps to wake one by one",
        fail_text="played the sacred reed flute, but the sound was too thin once the harm had filled the whole town",
        qa_text="played the sacred reed flute to call the lamps awake",
        sense=2,
        power=2,
        tags={"music", "lamp"},
    ),
    "bucket_water": Aid(
        id="bucket_water",
        label="bucket of water",
        phrase="a bucket of water from the spring",
        method="splashed water at the shadow, which only hissed and slid around the drops",
        fail_text="threw spring water at the harm, but it did nothing at all",
        qa_text="threw water at the harm",
        sense=1,
        power=0,
        tags={"water"},
    ),
}

CHILD_NAMES = ["Lio", "Mira", "Tarin", "Nela", "Ivo", "Suri", "Pavo", "Ena"]
GUARDIAN_NAMES = ["Thalos", "Iria", "Doran", "Selka", "Orin", "Mara"]
TRAITS = ["curious", "restless", "eager", "thoughtful", "wondering"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting in SETTINGS:
        for vessel in VESSELS:
            for harm in HARMS:
                if VESSELS[vessel].spread >= 1 and HARMS[harm].name:
                    combos.append((setting, vessel, harm))
    return combos


def sensible_aids() -> list[Aid]:
    return [a for a in AIDS.values() if a.sense >= SENSE_MIN]


def harm_severity(vessel: Vessel, delay: int) -> int:
    return vessel.spread + delay


def can_contain(aid: Aid, vessel: Vessel, delay: int) -> bool:
    return aid.power >= harm_severity(vessel, delay)


def outcome_of(params: StoryParams) -> str:
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid '{params.aid}'.)")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel '{params.vessel}'.)")
    return "contained" if can_contain(AIDS[params.aid], VESSELS[params.vessel], params.delay) else "bad_ending"


def explain_response(aid_id: str) -> str:
    aid = AIDS[aid_id]
    better = ", ".join(sorted(a.id for a in sensible_aids()))
    return (
        f"(Refusing aid '{aid_id}': it scores too low on common sense "
        f"(sense={aid.sense} < {SENSE_MIN}). Try a wiser answer such as {better}.)"
    )


def predict_release(world: World) -> dict:
    sim = world.copy()
    vessel = sim.get("vessel")
    harm = sim.get("harm")
    village = sim.get("village")
    vessel.sealed = False
    harm.meters["loose"] += 1
    propagate(sim, narrate=False)
    return {
        "loose": harm.meters["loose"] >= THRESHOLD,
        "danger": village.meters["danger"],
    }


def opening(world: World, child: Entity, guardian: Entity, setting: Setting, vessel: Vessel) -> None:
    world.say(
        f"In the age when rivers still listened and hills remembered names, "
        f"there lived a child named {child.id} in {setting.place}."
    )
    world.say(setting.sky)
    world.say(setting.wonder)
    world.say(
        f"There, {guardian.id}, the {guardian.label_word}, kept watch over {vessel.phrase} "
        f"set {vessel.warning_place}."
    )


def curiosity(world: World, child: Entity, guardian: Entity, vessel: Vessel) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} was {child.attrs.get('trait', 'curious')}, and {child.pronoun()} often "
        f"stood near the vessel, wondering what song or storm might sleep inside."
    )
    world.say(
        f'On the lid were written the words, "{vessel.seal_text}"'
    )
    world.say(
        f'One day {child.id} asked, "Why must it stay shut?"'
    )
    world.say(
        f'{guardian.id} answered, "Because a wise heart learns to anticipate harm before touching what it does not understand."'
    )


def warning(world: World, child: Entity, guardian: Entity, vessel: Vessel, harm: Harm) -> None:
    pred = predict_release(world)
    world.facts["predicted_danger"] = pred["danger"]
    guardian.memes["care"] += 1
    world.say(
        f'{guardian.id} laid a hand over the seal. "Inside waits {harm.name}," {guardian.pronoun()} said. '
        f'"If curiosity turns into interference, the whole town may weep."'
    )


def temptation(world: World, child: Entity, guardian: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But when {guardian.id} walked to the spring to greet a traveler, "
        f"{child.id}'s wonder grew louder than patience."
    )
    world.say(
        f"{child.pronoun().capitalize()} looked left and right, then reached toward the vessel with trembling fingers."
    )


def release_harm(world: World, vessel_ent: Entity, harm_ent: Entity, vessel: Vessel, harm: Harm, child: Entity) -> None:
    vessel_ent.sealed = False
    vessel_ent.meters["opened"] += 1
    harm_ent.meters["loose"] += 1
    child.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The seal broke. At once {vessel.release_text}."
    )
    world.say(harm.sign)
    world.say(harm.touch)


def alarm(world: World, child: Entity, guardian: Entity, harm: Harm) -> None:
    world.say(
        f'"{guardian.id}!" cried {child.id}. "{harm.name} is free!"'
    )
    world.say(
        f"{guardian.id} came running, and sorrow filled {guardian.pronoun('possessive')} face when {guardian.pronoun()} saw the broken seal."
    )


def contain(world: World, guardian: Entity, aid: Aid, harm: Harm, village: Entity, vessel: Vessel) -> None:
    village.meters["danger"] = 0.0
    village.meters["shadow"] = 0.0
    world.get("harm").meters["loose"] = 0.0
    guardian.memes["resolve"] += 1
    world.say(
        f"Without wasting even one breath, {guardian.id} {aid.method}."
    )
    world.say(
        f"Slowly the air cleared, and {harm.name} folded back toward the {vessel.label} like smoke drawn into a chimney."
    )
    world.say(
        f"{VESSELS[vessel.id].residue_text}. The guardian sealed the vessel again with new wax and a steadier hand."
    )


def contained_lesson(world: World, child: Entity, guardian: Entity, aid: Aid, harm: Harm) -> None:
    child.memes["remorse"] += 1
    child.memes["lesson"] += 1
    guardian.memes["forgiveness"] += 1
    world.say(
        f"{child.id} sank to {child.pronoun('possessive')} knees. "
        f'"I wanted to know," {child.pronoun()} whispered.'
    )
    world.say(
        f'"Curiosity is not evil," said {guardian.id}, lifting {child.pronoun("object")} gently. '
        f'"But curiosity must walk beside wisdom. When you cannot anticipate the end, you must not break what others are guarding."'
    )
    world.say(
        f"After that day, {child.id} asked questions with an open mouth and kept {child.pronoun('possessive')} hands still until the right time."
    )


def fail_to_contain(world: World, guardian: Entity, aid: Aid, harm: Harm, village: Entity) -> None:
    guardian.memes["grief"] += 1
    village.meters["danger"] += 1
    village.meters["shadow"] += 1
    world.say(
        f"{guardian.id} {aid.fail_text}."
    )
    world.say(
        f"But {harm.name} rolled through the streets, and soon {harm.loss}."
    )


def bad_ending(world: World, child: Entity, guardian: Entity, setting: Setting, harm: Harm) -> None:
    child.memes["remorse"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"By nightfall, {setting.people} barred their doors and lit dim lamps behind shutter cracks."
    )
    world.say(
        f"{harm.ending_image}."
    )
    world.say(
        f"{child.id} wept beside {guardian.id}. No one scolded loudly, which made the sorrow feel heavier."
    )
    world.say(
        f'At last {guardian.id} said, "{harm.lesson}"'
    )
    world.say(
        f"From then on, whenever {child.id} felt wonder burning too hot, {child.pronoun()} remembered the broken seal before touching what was not {child.pronoun('possessive')} to open."
    )


def tell(
    setting: Setting,
    vessel: Vessel,
    harm: Harm,
    aid: Aid,
    child_name: str,
    child_gender: str,
    guardian_name: str,
    guardian_type: str,
    relation: str,
    trait: str,
    delay: int,
    child_age: int,
    guardian_age: int,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"relation": relation, "trait": trait},
    ))
    guardian = world.add(Entity(
        id=guardian_name,
        kind="character",
        type=guardian_type,
        label=guardian_type,
        role="guardian",
        attrs={"relation": relation},
    ))
    vessel_ent = world.add(Entity(
        id="vessel",
        kind="thing",
        type="vessel",
        label=vessel.label,
        phrase=vessel.phrase,
        sealed=True,
        sacred=True,
        dangerous=True,
        tags=set(vessel.tags),
    ))
    harm_ent = world.add(Entity(
        id="harm",
        kind="thing",
        type="harm",
        label=harm.name,
        dangerous=True,
        tags=set(harm.tags),
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="village",
    ))
    child.attrs["age"] = child_age
    guardian.attrs["age"] = guardian_age

    opening(world, child, guardian, setting, vessel)
    world.para()
    curiosity(world, child, guardian, vessel)
    warning(world, child, guardian, vessel, harm)
    temptation(world, child, guardian)

    world.para()
    release_harm(world, vessel_ent, harm_ent, vessel, harm, child)
    alarm(world, child, guardian, harm)

    outcome = "contained" if can_contain(aid, vessel, delay) else "bad_ending"
    world.facts["severity"] = harm_severity(vessel, delay)
    world.facts["delay"] = delay

    world.para()
    if outcome == "contained":
        contain(world, guardian, aid, harm, village, vessel)
        contained_lesson(world, child, guardian, aid, harm)
    else:
        fail_to_contain(world, guardian, aid, harm, village)
        bad_ending(world, child, guardian, setting, harm)

    world.facts.update(
        setting=setting,
        vessel_cfg=vessel,
        harm_cfg=harm,
        aid_cfg=aid,
        child=child,
        guardian=guardian,
        vessel=vessel_ent,
        harm=harm_ent,
        village=village,
        relation=relation,
        outcome=outcome,
        opened=vessel_ent.meters["opened"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "seal": [(
        "Why do people seal something shut?",
        "A seal shows that something should stay closed until the right time. It is a sign of warning, care, and trust."
    )],
    "curiosity": [(
        "Is curiosity good or bad?",
        "Curiosity is good when it helps you learn in a safe and respectful way. It becomes dangerous when it pushes you to ignore warnings."
    )],
    "warning": [(
        "Why should you listen to a warning from a wise grown-up?",
        "A wise warning often comes from knowing what could go wrong. Listening can protect not just you, but other people too."
    )],
    "prayer": [(
        "Why do myths use bells, prayers, or sacred songs?",
        "In myths, bells, prayers, and songs often stand for order, memory, and courage. They show people trying to push back harm with wisdom instead of panic."
    )],
    "mirror": [(
        "Why is light often important in myths?",
        "Light in myths often stands for truth, hope, or protection. When darkness spreads, light shows that goodness can still fight back."
    )],
    "music": [(
        "Why can music matter in a story?",
        "Music can call people together, give them courage, or remind them what is good. In a myth, a song or flute may help restore balance."
    )],
    "moral": [(
        "What is a moral in a story?",
        "A moral is the lesson a story teaches. It helps readers remember what kind of choices lead to help or harm."
    )],
}
KNOWLEDGE_ORDER = ["seal", "curiosity", "warning", "prayer", "mirror", "music", "moral"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    vessel = f["vessel_cfg"]
    harm = f["harm_cfg"]
    outcome = f["outcome"]
    if outcome == "bad_ending":
        return [
            f'Write a short myth for a young child that includes the words "interference" and "anticipate".',
            f"Tell a myth in which {child.id}'s curiosity leads {child.pronoun('object')} to open {vessel.phrase}, releasing {harm.name} and bringing a sad ending.",
            f"Write a moral tale where {guardian.id} warns a child to anticipate harm before interfering with a sacred object, but the warning is ignored.",
        ]
    return [
        f'Write a short myth for a young child that includes the words "interference" and "anticipate".',
        f"Tell a myth in which {child.id}'s curiosity breaks the seal on {vessel.phrase}, but {guardian.id} barely saves the village.",
        f"Write a moral tale where a wise guardian warns a child not to interfere with a sacred object, and the child learns that curiosity must be guided by patience.",
    ]


def pair_phrase(relation: str, guardian: Entity) -> str:
    if relation == "grandchild":
        return f"a child and {guardian.pronoun('possessive')} elder guardian"
    return "a child and a village guardian"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    vessel = f["vessel_cfg"]
    harm = f["harm_cfg"]
    aid = f["aid_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_phrase(f['relation'], guardian)}, {child.id} and {guardian.id}. "
            f"They live in a place where sacred things are watched carefully."
        ),
        (
            f"Why was {child.id} interested in the {vessel.label}?",
            f"{child.id} was full of curiosity and wondered what was sleeping inside it. "
            f"The mystery of the seal made the vessel feel even more tempting."
        ),
        (
            f"What warning did {guardian.id} give?",
            f"{guardian.id} said a wise heart should anticipate harm before touching what it does not understand. "
            f"{guardian.pronoun().capitalize()} also warned that careless interference could hurt the whole town."
        ),
    ]
    if f["opened"]:
        qa.append((
            f"What happened when {child.id} opened the {vessel.label}?",
            f"{harm.name} burst free, and the place around them changed at once. "
            f"The broken seal turned one curious moment into danger for everyone nearby."
        ))
    if outcome == "contained":
        qa.append((
            f"How did {guardian.id} stop the danger?",
            f"{guardian.id} {aid.qa_text}. "
            f"That quick, wise action contained the harm before it could settle over the whole town."
        ))
        qa.append((
            f"What did {child.id} learn?",
            f"{child.id} learned that curiosity is not wrong by itself, but it needs wisdom and patience. "
            f"When {child.pronoun()} could not anticipate the ending, {child.pronoun()} should not have broken the seal."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the village safe and the vessel sealed again. "
            f"The ending image shows that danger can be repaired, but only after a hard lesson."
        ))
    else:
        qa.append((
            "Why is this a bad ending?",
            f"It is a bad ending because the harm spread through the town and people lost peace and brightness. "
            f"The trouble reached many innocent people, not just the child who opened the vessel."
        ))
        qa.append((
            f"What did {child.id} learn after the disaster?",
            f"{child.id} learned that warnings are a kind of love and that impatient interference can wound a whole community. "
            f"The lesson came too late to stop the loss, which is what makes the ending sad."
        ))
        qa.append((
            "What is the moral of the story?",
            f"{harm.lesson} "
            f"It teaches that wonder should lead to questions first, not reckless hands."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"seal", "curiosity", "warning", "moral"}
    aid = f["aid_cfg"]
    if "prayer" in aid.tags or "bell" in aid.tags or "salt" in aid.tags:
        tags.add("prayer")
    if "mirror" in aid.tags or "sun" in aid.tags:
        tags.add("mirror")
    if "music" in aid.tags or "lamp" in aid.tags:
        tags.add("music")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        flags = [name for name, on in (
            ("sealed", ent.sealed),
            ("sacred", ent.sacred),
            ("dangerous", ent.dangerous),
            ("protective", ent.protective),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, V, H) :- setting(S), vessel(V), harm(H).

sensible_aid(A) :- aid(A), sense(A, S), sense_min(M), S >= M.

severity(V, D, Sv) :- spread(V, Sp), delay(D), Sv = Sp + D.
contained(V, A, D) :- vessel(V), sensible_aid(A), severity(V, D, Sv), power(A, P), P >= Sv.
bad_ending(V, A, D) :- vessel(V), aid(A), delay(D), not contained(V, A, D).
outcome(contained) :- chosen_vessel(V), chosen_aid(A), delay(D), contained(V, A, D).
outcome(bad_ending) :- chosen_vessel(V), chosen_aid(A), delay(D), bad_ending(V, A, D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("spread", vid, vessel.spread))
    for hid in HARMS:
        lines.append(asp.fact("harm", hid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        lines.append(asp.fact("power", aid_id, aid.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_aids() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_aid/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible_aid"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_aid", params.aid),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="valley",
        vessel="jar",
        harm="night_swarm",
        aid="bell_prayer",
        child_name="Mira",
        child_gender="girl",
        guardian_name="Iria",
        guardian_type="priestess",
        relation="grandchild",
        trait="curious",
        delay=0,
        child_age=7,
        guardian_age=320,
    ),
    StoryParams(
        setting="island",
        vessel="box",
        harm="sorrow_fog",
        aid="reed_flute",
        child_name="Lio",
        child_gender="boy",
        guardian_name="Orin",
        guardian_type="priest",
        relation="apprentice",
        trait="eager",
        delay=2,
        child_age=8,
        guardian_age=280,
    ),
    StoryParams(
        setting="desert",
        vessel="urn",
        harm="thorn_wind",
        aid="sun_mirror",
        child_name="Suri",
        child_gender="girl",
        guardian_name="Mara",
        guardian_type="priestess",
        relation="ward",
        trait="wondering",
        delay=0,
        child_age=6,
        guardian_age=260,
    ),
    StoryParams(
        setting="valley",
        vessel="box",
        harm="night_swarm",
        aid="sun_mirror",
        child_name="Ivo",
        child_gender="boy",
        guardian_name="Thalos",
        guardian_type="priest",
        relation="grandchild",
        trait="restless",
        delay=1,
        child_age=7,
        guardian_age=400,
    ),
    StoryParams(
        setting="island",
        vessel="jar",
        harm="thorn_wind",
        aid="bell_prayer",
        child_name="Nela",
        child_gender="girl",
        guardian_name="Selka",
        guardian_type="priestess",
        relation="apprentice",
        trait="thoughtful",
        delay=2,
        child_age=8,
        guardian_age=290,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a myth of curiosity, warning, and a sealed danger."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--harm", choices=HARMS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--guardian-type", choices=["priest", "priestess"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.aid and AIDS[args.aid].sense < SENSE_MIN:
        raise StoryError(explain_response(args.aid))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.harm is None or combo[2] == args.harm)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, vessel_id, harm_id = rng.choice(sorted(combos))
    aid_id = args.aid or rng.choice(sorted(a.id for a in sensible_aids()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    guardian_type = args.guardian_type or rng.choice(["priest", "priestess"])
    child_name = rng.choice(CHILD_NAMES)
    guardian_name = rng.choice([n for n in GUARDIAN_NAMES if n != child_name])
    relation = rng.choice(["grandchild", "apprentice", "ward"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        vessel=vessel_id,
        harm=harm_id,
        aid=aid_id,
        child_name=child_name,
        child_gender=child_gender,
        guardian_name=guardian_name,
        guardian_type=guardian_type,
        relation=relation,
        trait=trait,
        delay=delay,
        child_age=rng.randint(6, 8),
        guardian_age=rng.randint(200, 400),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting '{params.setting}'.)")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel '{params.vessel}'.)")
    if params.harm not in HARMS:
        raise StoryError(f"(Unknown harm '{params.harm}'.)")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid '{params.aid}'.)")
    if AIDS[params.aid].sense < SENSE_MIN:
        raise StoryError(explain_response(params.aid))

    world = tell(
        setting=SETTINGS[params.setting],
        vessel=VESSELS[params.vessel],
        harm=HARMS[params.harm],
        aid=AIDS[params.aid],
        child_name=params.child_name,
        child_gender=params.child_gender,
        guardian_name=params.guardian_name,
        guardian_type=params.guardian_type,
        relation=params.relation,
        trait=params.trait,
        delay=params.delay,
        child_age=params.child_age,
        guardian_age=params.guardian_age,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {aid.id for aid in sensible_aids()}
    asp_sensible = set(asp_sensible_aids())
    if py_sensible == asp_sensible:
        print(f"OK: sensible aids match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible aids:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sensible))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving random case at seed {seed}.")
            break

    bad = 0
    for case in cases:
        py_outcome = outcome_of(case)
        asp_out = asp_outcome(case)
        if py_outcome != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_aid/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible aids: {', '.join(asp_sensible_aids())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, vessel, harm) combos:\n")
        for setting_id, vessel_id, harm_id in combos:
            print(f"  {setting_id:8} {vessel_id:6} {harm_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = (
                f"### {p.child_name}: {p.vessel} / {p.harm} at {p.setting} "
                f"({p.aid}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
