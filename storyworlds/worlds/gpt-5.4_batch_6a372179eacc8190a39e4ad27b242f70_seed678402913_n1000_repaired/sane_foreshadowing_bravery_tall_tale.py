#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sane_foreshadowing_bravery_tall_tale.py
==================================================================

A standalone story world for a child-sized tall tale: in a windy frontier town,
small signs whisper that a giant storm is coming, and one brave child must reach
a warning signal in time so the grown-ups can hurry back and tie everything down.

The style leans tall-tale in its exaggeration, but the world keeps one foot on
the ground: the hero succeeds by noticing sane warning signs, picking a signal
loud enough to carry, and acting bravely before the storm grows teeth.

Run it
------
python storyworlds/worlds/gpt-5.4/sane_foreshadowing_bravery_tall_tale.py
python storyworlds/worlds/gpt-5.4/sane_foreshadowing_bravery_tall_tale.py --setting mesa --signal bell
python storyworlds/worlds/gpt-5.4/sane_foreshadowing_bravery_tall_tale.py --signal whistle
python storyworlds/worlds/gpt-5.4/sane_foreshadowing_bravery_tall_tale.py --all
python storyworlds/worlds/gpt-5.4/sane_foreshadowing_bravery_tall_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/sane_foreshadowing_bravery_tall_tale.py --verify
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

# Make storyworlds/results.py importable when run directly from this nested dir.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SANE_MIN = 2


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    signal_spot: str
    field_place: str
    distance: int
    route_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Omen:
    id: str
    sign: str
    warning: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Route:
    id: str
    path: str
    risk: int
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    loudness: int
    sane: int
    sound: str
    action: str
    answer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    courage_bonus: int
    support_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    omen: str
    route: str
    signal: str
    helper: str
    hero_name: str
    hero_gender: str
    adult_type: str
    trait: str
    storm_delay: int = 0
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


def _r_alarm(world: World) -> list[str]:
    if "signal" not in world.entities or "workers" not in world.entities:
        return []
    sig = world.get("signal")
    if sig.meters["rung"] < THRESHOLD:
        return []
    mark = ("alarm",)
    if mark in world.fired:
        return []
    world.fired.add(mark)
    workers = world.get("workers")
    workers.memes["alert"] += 1
    workers.meters["returning"] += 1
    return ["__alarm__"]


def _r_secured(world: World) -> list[str]:
    if "workers" not in world.entities or "storm" not in world.entities or "town" not in world.entities:
        return []
    workers = world.get("workers")
    storm = world.get("storm")
    town = world.get("town")
    if workers.meters["returning"] < THRESHOLD:
        return []
    mark = ("secured",)
    if mark in world.fired:
        return []
    world.fired.add(mark)
    if storm.meters["arrived"] < THRESHOLD:
        town.meters["secured"] += 1
        town.meters["damage"] = 0.0
    return ["__secured__"]


CAUSAL_RULES = [
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="secured", tag="physical", apply=_r_secured),
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
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "mesa": Setting(
        id="mesa",
        place="Dusty Mesa Junction",
        signal_spot="the tall water tower",
        field_place="the far hay meadow",
        distance=3,
        route_line="a ladder nailed up the side of the old water tower",
        ending_image="the whole town shone calm under a sky that had used up its temper",
        tags={"tower", "wind"},
    ),
    "prairie": Setting(
        id="prairie",
        place="Long-Grass Prairie Bend",
        signal_spot="the bell frame on the hill",
        field_place="the corn patch past the creek",
        distance=2,
        route_line="a plank footbridge and the hill path beyond it",
        ending_image="the fields lay flat and silver while the houses still stood snug as turtle shells",
        tags={"hill", "storm"},
    ),
    "canyon": Setting(
        id="canyon",
        place="Red Canyon Crossing",
        signal_spot="the old lookout platform",
        field_place="the bean rows by the wash",
        distance=4,
        route_line="a narrow catwalk built between two red rocks",
        ending_image="the canyon echoed softly again, and every roof stayed where roofs belong",
        tags={"canyon", "echo"},
    ),
}

OMENS = {
    "swallows": Omen(
        id="swallows",
        sign="the swallows skimmed so low they nearly stitched the air",
        warning="Grandpa always said low swallows meant rough wind was riding in behind them",
        severity=1,
        tags={"birds", "foreshadowing"},
    ),
    "vanesqueal": Omen(
        id="vanesqueal",
        sign="the weather vane squealed and spun like a pig on skates",
        warning="That shriek meant the sky was winding itself up for trouble",
        severity=2,
        tags={"weather", "foreshadowing"},
    ),
    "stillness": Omen(
        id="stillness",
        sign="the whole town went so still that even the wash line forgot how to flap",
        warning="In that country, a too-quiet minute was the storm's way of clearing its throat",
        severity=2,
        tags={"weather", "foreshadowing"},
    ),
    "ants": Omen(
        id="ants",
        sign="the ants marched uphill carrying crumbs twice their size",
        warning="Folks said ants did that only when rain and wind had signed a mean little agreement",
        severity=1,
        tags={"ants", "foreshadowing"},
    ),
}

ROUTES = {
    "ladder": Route(
        id="ladder",
        path="the ladder",
        risk=3,
        detail="Each rung wobbled just enough to make a small stomach feel large.",
        tags={"height"},
    ),
    "bridge": Route(
        id="bridge",
        path="the footbridge",
        risk=2,
        detail="The boards knocked their wooden knees together above the creek.",
        tags={"bridge"},
    ),
    "catwalk": Route(
        id="catwalk",
        path="the catwalk",
        risk=4,
        detail="The catwalk was narrow enough to make a brave shadow walk single file.",
        tags={"height", "canyon"},
    ),
}

SIGNALS = {
    "bell": Signal(
        id="bell",
        label="bell",
        phrase="the brass warning bell",
        loudness=4,
        sane=3,
        sound="BONG! BONG! BONG!",
        action="rang the bell with both hands",
        answer="The bell was loud enough to carry clear to the fields.",
        tags={"bell", "warning"},
    ),
    "horn": Signal(
        id="horn",
        label="cow horn",
        phrase="the long cow horn",
        loudness=3,
        sane=2,
        sound="BWAAAH!",
        action="blew the horn until the note bounced off every board and barrel",
        answer="The horn carried far because it was made for calling workers home.",
        tags={"horn", "warning"},
    ),
    "pan": Signal(
        id="pan",
        label="frying pan",
        phrase="a giant iron frying pan",
        loudness=2,
        sane=2,
        sound="CLANG-CLANG!",
        action="banged the pan with a spoon hard enough to wake the chickens and the clouds",
        answer="The pan made a sharp racket, but it did not carry as far as a bell or horn.",
        tags={"pan", "warning"},
    ),
    "whistle": Signal(
        id="whistle",
        label="tin whistle",
        phrase="a tiny tin whistle",
        loudness=1,
        sane=1,
        sound="Phee! Phee!",
        action="blew the whistle until the little note fluttered away",
        answer="The whistle was too small for warning people working far away.",
        tags={"whistle"},
    ),
}

HELPERS = {
    "dog": Helper(
        id="dog",
        label="the sheepdog",
        type="dog",
        courage_bonus=1,
        support_line="The sheepdog planted his paws beside the child as if four sturdy paws could lend two more to the job.",
        ending_line="Afterward, the sheepdog trotted around as proud as if he had held the sky up himself.",
        tags={"dog"},
    ),
    "aunt": Helper(
        id="aunt",
        label="Aunt May",
        type="aunt",
        courage_bonus=2,
        support_line="Aunt May shouted from below to keep climbing and kept one hand on the rope line.",
        ending_line="Aunt May laughed later and said the child had more grit than a wagonload of sand.",
        tags={"adult_helper"},
    ),
    "none": Helper(
        id="none",
        label="no helper",
        type="none",
        courage_bonus=0,
        support_line="No one was close enough to do the climbing for the child.",
        ending_line="Later, the child stood a little taller all by themselves.",
        tags=set(),
    ),
}

GIRL_NAMES = ["Molly", "Nell", "Sadie", "Ruth", "Pearl", "June"]
BOY_NAMES = ["Eli", "Hank", "Beau", "Jesse", "Cal", "Otis"]
TRAITS = ["steady", "careful", "bright", "stubborn", "quick-eyed"]

KNOWLEDGE = {
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story shows a small sign early that hints at something important coming later. It helps the big moment feel prepared instead of sudden."
        )
    ],
    "bell": [
        (
            "Why is a bell good for a warning?",
            "A big bell makes a loud sound that can travel far. That helps many people hear the warning quickly."
        )
    ],
    "horn": [
        (
            "Why can a horn be used to call people from far away?",
            "A horn makes one long strong note. That kind of sound can carry across open fields better than a quiet voice."
        )
    ],
    "bridge": [
        (
            "Why can crossing a bridge feel scary in high wind?",
            "A bridge can sway or rattle when the wind pushes it. That makes people feel unsteady even when the bridge still holds."
        )
    ],
    "height": [
        (
            "Why do brave people still feel scared sometimes?",
            "Brave people can feel fear and act anyway. Bravery means doing the right thing even while your heart is thumping."
        )
    ],
    "warning": [
        (
            "Why is it important to warn people before a storm arrives?",
            "A warning gives people time to come back, tie things down, and get safe. A little time can prevent a lot of trouble."
        )
    ],
    "dog": [
        (
            "How can a dog help when someone feels nervous?",
            "A calm dog can stay close and make a person feel less alone. Even without talking, a helper beside you can make a hard job feel possible."
        )
    ],
}
KNOWLEDGE_ORDER = ["foreshadowing", "warning", "bell", "horn", "bridge", "height", "dog"]


def required_loudness(setting: Setting, omen: Omen, delay: int) -> int:
    return setting.distance + omen.severity + delay


def route_window(route: Route, helper: Helper) -> int:
    return 3 + helper.courage_bonus - route.risk


def signal_can_warn(setting: Setting, omen: Omen, signal: Signal, delay: int) -> bool:
    return signal.sane >= SANE_MIN and signal.loudness >= required_loudness(setting, omen, delay)


def brave_enough(route: Route, helper: Helper) -> bool:
    return route_window(route, helper) >= 0


def valid_combos() -> list[tuple[str, str, str, str, int]]:
    combos: list[tuple[str, str, str, str, int]] = []
    for setting_id, setting in SETTINGS.items():
        for omen_id, omen in OMENS.items():
            for signal_id, signal in SIGNALS.items():
                for helper_id, helper in HELPERS.items():
                    for delay in (0, 1):
                        if signal_can_warn(setting, omen, signal, delay) and brave_enough(ROUTES["bridge"], helper):
                            combos.append((setting_id, omen_id, signal_id, helper_id, delay))
    return combos


def predict_outcome(setting: Setting, omen: Omen, route: Route, signal: Signal, helper: Helper, delay: int) -> str:
    if signal.sane < SANE_MIN:
        return "lost"
    if route_window(route, helper) < 0:
        return "lost"
    if signal.loudness >= required_loudness(setting, omen, delay):
        return "saved"
    return "lost"


def intro(world: World, hero: Entity, setting: Setting, trait: str, adult: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {setting.place}, where fence posts were said to grow taller at night and wagon wheels boasted louder than roosters, "
        f"lived {hero.id}, a {trait} little {hero.type} with eyes sharp enough to notice what the wind was thinking."
    )
    world.say(
        f"That afternoon, most of the grown-ups were working in {setting.field_place}, and {hero.id}'s {adult.label_word} had gone with them."
    )


def foreshadow(world: World, hero: Entity, omen: Omen) -> None:
    hero.memes["caution"] += 1
    world.say(f"Before the trouble came, {omen.sign}.")
    world.say(f"{omen.warning}.")
    world.facts["foreshadowing_line"] = omen.sign


def spot_risk(world: World, hero: Entity, setting: Setting) -> None:
    hero.memes["worry"] += 1
    town = world.get("town")
    town.meters["at_risk"] += 1
    world.say(
        f"{hero.id} looked over the sheds and porches and knew that if the storm hit first, loose roofs and feed sacks would go skipping across town like iron pancakes."
    )
    world.say(
        f"The only way to call everyone back in time was to reach {setting.signal_spot} and sound the warning."
    )


def helper_beat(world: World, helper: Helper) -> None:
    if helper.id != "none":
        world.say(helper.support_line)
    else:
        world.say(helper.support_line)


def climb_route(world: World, hero: Entity, route: Route) -> None:
    hero.meters["climbing"] += 1
    hero.memes["fear"] += 1
    world.say(f"The way there ran by {route.path}. {route.detail}")
    if route.risk >= 4:
        world.say(
            f"{hero.id}'s knees felt as loose as jelly in a wash bucket, but {hero.pronoun()} kept going one careful step at a time."
        )
    elif route.risk >= 3:
        world.say(
            f"{hero.id}'s heart thumped like a hammer in a biscuit tin, yet {hero.pronoun()} climbed without turning back."
        )
    else:
        world.say(
            f"The path was shaky enough to make a sensible person pause, so {hero.id} paused once, took a breath, and went on."
        )


def fail_route(world: World, hero: Entity, route: Route) -> None:
    hero.memes["fear"] += 1
    hero.memes["sadness"] += 1
    world.say(
        f"{hero.id} started across {route.path}, but the rising wind shoved so hard that even bravery could not turn the path steady."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had to scramble back before a fall, and by then the storm was already pounding on the town's door."
    )
    storm = world.get("storm")
    storm.meters["arrived"] += 1
    town = world.get("town")
    town.meters["damage"] += 1


def sound_signal(world: World, hero: Entity, signal: Signal) -> None:
    sig = world.get("signal")
    sig.meters["rung"] += 1
    hero.memes["bravery"] += 1
    propagate(world, narrate=False)
    world.say(f"At the top, {hero.id} grabbed {signal.phrase} and {signal.action}.")
    world.say(signal.sound)


def rescue_success(world: World, setting: Setting, hero: Entity, adult: Entity, helper: Helper) -> None:
    world.get("storm").meters["arrived"] += 1
    propagate(world, narrate=False)
    town = world.get("town")
    town.meters["secured"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"Out in {setting.field_place}, heads turned all at once. The workers came running with ropes, tarps, and fast hands."
    )
    world.say(
        f"They tied doors, stacked barrels, and hauled the loose feed under cover before the first hard gust slapped the street."
    )
    world.say(
        f"When {adult.label_word.capitalize()} reached {hero.id}, {adult.pronoun()} hugged {hero.pronoun('object')} tight and said that was the bravest and sanest thing anyone could have done."
    )
    world.say(helper.ending_line)
    world.say(
        f"Then the storm stamped around town for a while, found everything fastened down, and had to go grumble someplace else. By evening, {setting.ending_image}."
    )


def rescue_fail_signal(world: World, setting: Setting, hero: Entity, signal: Signal) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f"{hero.id} did everything right with brave hands, but {signal.label} was too small for work so far away."
    )
    world.say(
        f"The sound fluttered over the nearest roofs and died before it reached {setting.field_place}."
    )
    storm = world.get("storm")
    storm.meters["arrived"] += 1
    town = world.get("town")
    town.meters["damage"] += 1
    world.say(
        "By the time the grown-ups saw the sky and hurried back on their own, one shed door had torn free and seed sacks were rolling down the road."
    )
    world.say(
        f"Nobody was hurt, but {hero.id} learned that bravery works best when it travels with a good plan and the right tool."
    )


def tell(
    setting: Setting,
    omen: Omen,
    route: Route,
    signal: Signal,
    helper: Helper,
    hero_name: str,
    hero_gender: str,
    adult_type: str,
    trait: str,
    storm_delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the adult"))
    world.add(Entity(id="town", type="town", label="the town"))
    world.add(Entity(id="storm", type="storm", label="the storm"))
    world.add(Entity(id="signal", type="signal", label=signal.label))
    world.add(Entity(id="workers", type="workers", label="the workers"))
    if helper.id != "none":
        world.add(Entity(id="helper", kind="character", type=helper.type, label=helper.label, role="helper"))

    intro(world, hero, setting, trait, adult)
    foreshadow(world, hero, omen)

    world.para()
    spot_risk(world, hero, setting)
    helper_beat(world, helper)
    climb_route(world, hero, route)

    outcome = predict_outcome(setting, omen, route, signal, helper, storm_delay)
    world.para()
    if route_window(route, helper) < 0:
        fail_route(world, hero, route)
    else:
        sound_signal(world, hero, signal)
        if signal.loudness >= required_loudness(setting, omen, storm_delay) and signal.sane >= SANE_MIN:
            rescue_success(world, setting, hero, adult, helper)
        else:
            rescue_fail_signal(world, setting, hero, signal)

    world.facts.update(
        setting=setting,
        omen=omen,
        route=route,
        signal_cfg=signal,
        helper_cfg=helper,
        hero=hero,
        adult=adult,
        outcome=outcome,
        storm_delay=storm_delay,
        needed_loudness=required_loudness(setting, omen, storm_delay),
        route_margin=route_window(route, helper),
        heard=signal.loudness >= required_loudness(setting, omen, storm_delay),
        sane=(signal.sane >= SANE_MIN),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    setting = f["setting"]
    omen = f["omen"]
    signal = f["signal_cfg"]
    route = f["route"]
    outcome = f["outcome"]
    prompts = [
        'Write a tall-tale style story for a 3-to-5-year-old that includes the word "sane".',
        f"Tell a frontier tall tale where {hero.id} notices that {omen.sign} and realizes a storm is coming.",
        f"Write a story about bravery where a child must cross {route.path} to use {signal.phrase} and warn a whole town.",
    ]
    if outcome == "saved":
        prompts.append(
            "Make the ending prove that courage and a sensible plan together can save the day."
        )
    else:
        prompts.append(
            "Let the story teach that bravery needs the right tool and enough time, even in a tall tale."
        )
    prompts[0] = prompts[0].replace("story", f"story set in {setting.place}")
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    adult = f["adult"]
    omen = f["omen"]
    setting = f["setting"]
    route = f["route"]
    signal = f["signal_cfg"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type} in {setting.place}. The story also includes {hero.pronoun('possessive')} {adult.label_word} and the people working far away."
        ),
        (
            "What warning sign came before the storm?",
            f"The story foreshadowed the trouble with this sign: {omen.sign}. That early clue told {hero.id} the sky was getting ready for rough weather."
        ),
        (
            f"Why did {hero.id} have to go to {setting.signal_spot}?",
            f"{hero.id} needed to warn the workers in {setting.field_place} before the storm arrived. If they heard in time, they could run back and tie everything down."
        ),
        (
            f"Was {hero.id} brave on the way?",
            f"Yes. {hero.id} felt scared on {route.path}, but kept moving anyway, which is what bravery looks like in this story."
        ),
    ]
    if helper.id != "none":
        qa.append(
            (
                f"Who helped {hero.id}?",
                f"{helper.label} helped. {helper.support_line} That support made the hard climb feel more possible."
            )
        )
    if outcome == "saved":
        qa.append(
            (
                f"How did {hero.id} save the town?",
                f"{hero.id} used {signal.phrase} to send a warning loud enough to reach the fields. Because the workers heard in time, they came back and secured the town before the worst gusts hit."
            )
        )
        qa.append(
            (
                "Why does the story call the choice sane?",
                f"It calls the choice sane because {hero.id} did not panic or guess wildly. {hero.pronoun().capitalize()} picked a real warning signal and used it for the exact job it was meant to do."
            )
        )
    else:
        if f["route_margin"] < 0:
            qa.append(
                (
                    f"Why could {hero.id} not finish the climb?",
                    f"The route became too dangerous before {hero.id} could reach the signal. The storm and the shaky path together were stronger than one small climber."
                )
            )
        else:
            qa.append(
                (
                    f"Why did the warning fail?",
                    f"The signal was not loud enough for the distance. {hero.id} was brave, but the little sound faded before it reached the workers."
                )
            )
        qa.append(
            (
                "What did the story teach?",
                f"It taught that courage matters, but courage works best with the right plan and the right tool. Being brave is good, and being brave plus sensible is even better."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"foreshadowing", "warning"}
    tags |= set(f["route"].tags)
    tags |= set(f["signal_cfg"].tags)
    tags |= set(f["helper_cfg"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="mesa",
        omen="vanesqueal",
        route="ladder",
        signal="bell",
        helper="aunt",
        hero_name="Molly",
        hero_gender="girl",
        adult_type="father",
        trait="steady",
        storm_delay=0,
    ),
    StoryParams(
        setting="prairie",
        omen="swallows",
        route="bridge",
        signal="horn",
        helper="dog",
        hero_name="Eli",
        hero_gender="boy",
        adult_type="mother",
        trait="bright",
        storm_delay=0,
    ),
    StoryParams(
        setting="canyon",
        omen="stillness",
        route="catwalk",
        signal="horn",
        helper="aunt",
        hero_name="Pearl",
        hero_gender="girl",
        adult_type="uncle",
        trait="careful",
        storm_delay=1,
    ),
    StoryParams(
        setting="prairie",
        omen="vanesqueal",
        route="bridge",
        signal="pan",
        helper="none",
        hero_name="Cal",
        hero_gender="boy",
        adult_type="father",
        trait="quick-eyed",
        storm_delay=1,
    ),
]


def explain_signal(signal: Signal, setting: Setting, omen: Omen, delay: int) -> str:
    need = required_loudness(setting, omen, delay)
    if signal.sane < SANE_MIN:
        return (
            f"(No story: {signal.label} is not a sane warning tool here "
            f"(sane={signal.sane} < {SANE_MIN}). Pick a real warning signal like bell or horn.)"
        )
    return (
        f"(No story: {signal.label} is too quiet for this setup. "
        f"It carries {signal.loudness}, but this storm needs at least {need} to reach the fields.)"
    )


def explain_route(route: Route, helper: Helper) -> str:
    return (
        f"(No story: {route.path} is too dangerous with helper={helper.id}. "
        f"The route needs more support for a believable climb.)"
    )


ASP_RULES = r"""
sane_signal(S) :- signal(S), sane(S, V), sane_min(M), V >= M.
needed_loudness(Req) :- chosen_setting(St), distance(St, D),
                        chosen_omen(O), severity(O, Sev),
                        delay(Delay), Req = D + Sev + Delay.
heard :- chosen_signal(S), loudness(S, L), needed_loudness(R), L >= R.
route_margin(M) :- chosen_route(R), risk(R, RR),
                   chosen_helper(H), courage_bonus(H, B),
                   M = 3 + B - RR.
brave_enough :- route_margin(M), M >= 0.

valid(St, O, S, H, D) :- setting(St), omen(O), signal(S), helper(H), delay_value(D),
                         sane(S, SV), sane_min(M), SV >= M,
                         distance(St, Dist), severity(O, Sev), loudness(S, L),
                         L >= Dist + Sev + D,
                         courage_bonus(H, B),
                         3 + B - 2 >= 0.

outcome(saved) :- chosen_signal(S), sane_signal(S), heard, brave_enough.
outcome(lost) :- not outcome(saved).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("distance", sid, setting.distance))
    for oid, omen in OMENS.items():
        lines.append(asp.fact("omen", oid))
        lines.append(asp.fact("severity", oid, omen.severity))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("risk", rid, route.risk))
    for sid, signal in SIGNALS.items():
        lines.append(asp.fact("signal", sid))
        lines.append(asp.fact("loudness", sid, signal.loudness))
        lines.append(asp.fact("sane", sid, signal.sane))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("courage_bonus", hid, helper.courage_bonus))
    for delay in (0, 1):
        lines.append(asp.fact("delay_value", delay))
    lines.append(asp.fact("sane_min", SANE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_omen", params.omen),
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_signal", params.signal),
            asp.fact("chosen_helper", params.helper),
            asp.fact("delay", params.storm_delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _check_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.omen not in OMENS:
        raise StoryError(f"(No story: unknown omen '{params.omen}'.)")
    if params.route not in ROUTES:
        raise StoryError(f"(No story: unknown route '{params.route}'.)")
    if params.signal not in SIGNALS:
        raise StoryError(f"(No story: unknown signal '{params.signal}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.storm_delay not in (0, 1):
        raise StoryError("(No story: storm_delay must be 0 or 1.)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a child notices storm signs and bravely sounds a warning."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--storm-delay", type=int, choices=[0, 1], dest="storm_delay")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP and Python parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    omen_id = args.omen or rng.choice(sorted(OMENS))
    route_id = args.route or rng.choice(sorted(ROUTES))
    signal_id = args.signal or rng.choice(sorted(SIGNALS))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    delay = args.storm_delay if args.storm_delay is not None else rng.choice([0, 1])

    setting = SETTINGS[setting_id]
    omen = OMENS[omen_id]
    route = ROUTES[route_id]
    signal = SIGNALS[signal_id]
    helper = HELPERS[helper_id]

    if args.signal is not None and not signal_can_warn(setting, omen, signal, delay):
        raise StoryError(explain_signal(signal, setting, omen, delay))
    if args.route is not None and args.helper is not None and not brave_enough(route, helper):
        raise StoryError(explain_route(route, helper))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult_type = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        omen=omen_id,
        route=route_id,
        signal=signal_id,
        helper=helper_id,
        hero_name=name,
        hero_gender=gender,
        adult_type=adult_type,
        trait=trait,
        storm_delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        omen=OMENS[params.omen],
        route=ROUTES[params.route],
        signal=SIGNALS[params.signal],
        helper=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        adult_type=params.adult_type,
        trait=params.trait,
        storm_delay=params.storm_delay,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP valid combos match Python ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(20):
        p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        p.seed = seed
        cases.append(p)

    bad = 0
    for params in cases:
        py = predict_outcome(
            SETTINGS[params.setting],
            OMENS[params.omen],
            ROUTES[params.route],
            SIGNALS[params.signal],
            HELPERS[params.helper],
            params.storm_delay,
        )
        asp_out = asp_outcome(params)
        if py != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, omen, signal, helper, delay) combos:\n")
        for row in combos:
            print("  " + " ".join(str(x).ljust(10) for x in row))
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
            header = f"### {p.hero_name}: {p.setting}, {p.signal}, {predict_outcome(SETTINGS[p.setting], OMENS[p.omen], ROUTES[p.route], SIGNALS[p.signal], HELPERS[p.helper], p.storm_delay)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
