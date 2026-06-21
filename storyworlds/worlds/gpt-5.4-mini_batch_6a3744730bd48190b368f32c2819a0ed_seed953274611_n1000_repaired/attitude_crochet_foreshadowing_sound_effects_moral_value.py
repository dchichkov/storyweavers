#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/attitude_crochet_foreshadowing_sound_effects_moral_value.py
===========================================================================================

A small standalone storyworld in a space-adventure style.

Seed idea:
- A child aboard a little spaceship has an attitude.
- They are working with crochet yarn/hook on a tiny space mission.
- Foreshadowing appears as strange sounds from the ship.
- Sound effects punctuate the turn.
- The moral value is about listening, staying calm, and fixing problems kindly.

The world supports several reasonable variations, all built from a simulation
with typed entities, physical meters, emotional memes, a forward-chained rule
system, and an inline ASP twin for parity checks.
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

# Make shared results importable when run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Mission:
    id: str
    scene: str
    ship: str
    goal: str
    hatch: str
    sound_hint: str
    sendoff: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class CrochetKit:
    id: str
    label: str
    phrase: str
    hook: str
    loop_sound: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Trouble:
    id: str
    label: str
    phrase: str
    noise: str
    warning: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    if ship.meters["warning"] < THRESHOLD:
        return out
    if ("alert",) in world.fired:
        return out
    world.fired.add(("alert",))
    for kid in world.characters():
        kid.memes["unease"] += 1
    out.append("__alert__")
    return out


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    if ship.meters["warning"] < THRESHOLD:
        return out
    if ("break",) in world.fired:
        return out
    world.fired.add(("break",))
    ship.meters["stress"] += 1
    out.append("__break__")
    return out


RULES = [Rule("alert", _r_alert), Rule("break", _r_break)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    texts: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                texts.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for t in texts:
            world.say(t)
    return texts


def hazard(trouble: Trouble) -> bool:
    return trouble.risky


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fire_of_sound(trouble: Trouble, delay: int) -> int:
    return 1 + delay if trouble.risky else 0


def contained(fix: Fix, trouble: Trouble, delay: int) -> bool:
    return fix.power >= fire_of_sound(trouble, delay)


def predict(world: World, trouble_id: str) -> dict:
    sim = world.copy()
    _trigger_trouble(sim, sim.get(trouble_id), narrate=False)
    return {
        "warning": sim.get("ship").meters["warning"],
        "stress": sim.get("ship").meters["stress"],
    }


def _trigger_trouble(world: World, trouble_ent: Entity, narrate: bool = True) -> None:
    trouble_ent.meters["warning"] += 1
    world.get("ship").meters["warning"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, mate: Entity, mission: Mission) -> None:
    hero.memes["pride"] += 1
    mate.memes["hope"] += 1
    world.say(
        f"On the little starship {hero.id} and {mate.id} turned the cabin into {mission.scene}. "
        f"{mission.ship}"
    )
    world.say(
        f'"Captain {hero.id} and Navigator {mate.id}!" {hero.id} said with a bright grin. '
        f'"Let\'s reach {mission.goal}!"'
    )


def foreshadow(world: World, mate: Entity, mission: Mission) -> None:
    world.say(
        f"But near {mission.hatch}, {mission.sound_hint} slipped through the metal wall."
    )
    world.say(
        f'{mate.id} paused. "{mission.warning_line if "warning_line" in mission.__dict__ else "Do you hear that?"}"'
    )


def sound_fx(world: World, trouble: Trouble) -> None:
    world.say(f"{trouble.noise}")


def tempt(world: World, hero: Entity, trouble: Trouble) -> None:
    hero.memes["attitude"] += 1
    world.say(
        f'"{trouble.label}?" {hero.id} said with attitude. '
        f'"That sounds dramatic, not dangerous."'
    )


def warn(world: World, mate: Entity, hero: Entity, trouble: Trouble, parent: Entity) -> None:
    pred = predict(world, trouble.id)
    mate.memes["caution"] += 1
    world.facts["predicted_warning"] = pred["warning"]
    world.say(
        f'"Hold on," {mate.id} said softly. "{trouble.warning} {parent.label_word.capitalize()} said to be careful."'
    )


def defy(world: World, hero: Entity, mate: Entity, trouble: Trouble) -> None:
    hero.memes["defiance"] += 1
    world.say(f'"Hmph," {hero.id} muttered, and reached for {trouble.phrase} anyway.')


def ignore_and_use(world: World, trouble_ent: Entity, trouble: Trouble) -> None:
    _trigger_trouble(world, trouble_ent)
    world.say(
        f"{trouble.noise} {trouble.label.capitalize()} clicked and crackled in the dark."
    )


def call_for_help(world: World, mate: Entity, parent: Entity) -> None:
    world.say(f'"{parent.id}!" {mate.id} called. "{parent.label_word.capitalize()}, come quick!"')


def rescue(world: World, parent: Entity, fix: Fix, trouble_ent: Entity, trouble: Trouble, mission: Mission) -> None:
    trouble_ent.meters["warning"] = 0.0
    world.get("ship").meters["warning"] = 0.0
    body = fix.text.replace("{trouble}", trouble.label)
    world.say(
        f"{parent.label_word.capitalize()} came fast and {body}."
    )
    world.say(
        f"The cabin went still again, except for the soft hum of the engines and the little crochet hook resting safely in {world.facts['hero'].id}'s hand."
    )


def lesson(world: World, parent: Entity, hero: Entity, mate: Entity, trouble: Trouble) -> None:
    for kid in (hero, mate):
        kid.memes["relief"] += 1
        kid.memes["moral"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} hugged them both and said, "
        f'"A calm attitude matters more than a loud one. And crochet is for making, not for teasing danger. The brave thing is to ask for help."'
    )
    world.say(f'"We promise," whispered {mate.id} and {hero.id} together.')


def happy_finish(world: World, parent: Entity, hero: Entity, mate: Entity, mission: Mission, kit: CrochetKit) -> None:
    for kid in (hero, mate):
        kid.memes["joy"] += 1
    world.say(
        f"The next orbit, {parent.label_word.capitalize()} brought out a tiny repair pouch and a soft new skein of yarn."
    )
    world.say(
        f'"Now," {parent.id} smiled, "what does a space scout need for {mission.goal}?"'
    )
    world.say(
        f"{hero.id} lifted {kit.label}. {mate.id} snapped the pouch shut with a little {kit.loop_sound}."
    )
    world.say(
        f'"Crochet!" they cheered, and the starship sailed on {mission.sendoff}.'
    )


def rescue_fail(world: World, parent: Entity, fix: Fix, trouble_ent: Entity, trouble: Trouble) -> None:
    world.get("ship").meters["stress"] += 1
    trouble_ent.meters["warning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} rushed in, but {fix.fail.replace('{trouble}', trouble.label)}."
    )
    world.say("The ship shuddered, and the little mission had to slow to a careful crawl.")


def grim_end(world: World, parent: Entity, hero: Entity, mate: Entity, mission: Mission) -> None:
    for kid in (hero, mate):
        kid.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} got everyone strapped in and fixed the problem the safe way."
    )
    world.say(
        f"After that, the pair stopped clowning around and listened whenever the cabin gave them a warning."
    )
    world.say(
        f"The stars still looked the same, but now {hero.id} and {mate.id} knew a good attitude meant listening first."
    )


def tell(mission: Mission, kit: CrochetKit, trouble: Trouble, fix: Fix,
         hero_name: str = "Nova", hero_type: str = "girl",
         mate_name: str = "Pip", mate_type: str = "boy",
         parent_type: str = "mother", delay: int = 0,
         hero_traits: Optional[list[str]] = None) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=hero_traits or ["bold"]))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_type, role="mate", traits=["careful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the pilot"))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label="the ship"))
    tool = world.add(Entity(id="kit", kind="thing", type="tool", label=kit.label, tags=set(kit.tags)))
    trouble_ent = world.add(Entity(id="trouble", kind="thing", type="thing", label=trouble.label, tags=set(trouble.tags)))

    world.facts["hero"] = hero
    world.facts["mate"] = mate
    world.facts["parent"] = parent
    world.facts["mission"] = mission
    world.facts["kit"] = kit
    world.facts["trouble"] = trouble
    world.facts["fix"] = fix
    world.facts["delay"] = delay
    world.facts["tool"] = tool

    setup(world, hero, mate, mission)
    world.para()
    foreshadow(world, mate, mission)
    tempt(world, hero, trouble)
    warn(world, mate, hero, trouble, parent)

    averted = False
    if mission.id == "older_sibling_calm" and hero.memes["attitude"] < 1:
        averted = True

    if averted:
        world.say(f'{hero.id} looked at {mate.id}, blinked, and put the idea away.')
        happy_finish(world, parent, hero, mate, mission, kit)
        outcome = "averted"
    else:
        defy(world, hero, mate, trouble)
        world.para()
        ignore_and_use(world, trouble_ent, trouble)
        call_for_help(world, mate, parent)
        contained_ok = contained(fix, trouble, delay)
        world.facts["contained"] = contained_ok
        if contained_ok:
            world.para()
            rescue(world, parent, fix, trouble_ent, trouble, mission)
            lesson(world, parent, hero, mate, trouble)
            world.para()
            happy_finish(world, parent, hero, mate, mission, kit)
            outcome = "contained"
        else:
            world.para()
            rescue_fail(world, parent, fix, trouble_ent, trouble)
            grim_end(world, parent, hero, mate, mission)
            outcome = "burned"

    world.facts["outcome"] = outcome
    world.facts["ignited"] = True
    world.facts["resolved"] = outcome != "burned"
    return world


MISSIONS = {
    "starlane": Mission(
        id="starlane",
        scene="a tiny moon-base map made of blankets and paper stars",
        ship="The cabin lights blinked like tiny comets, and the little engine hummed in the floor.",
        goal="the silver moon gate",
        hatch="the storage hatch",
        sound_hint="a faint tap-tap from behind the panel",
        sendoff="toward the moon gate",
        tags={"space", "foreshadowing"},
    ),
    "asteroid": Mission(
        id="asteroid",
        scene="a pretend asteroid camp with pillow rocks and tape trails",
        ship="The control screen glowed blue, and the windows showed a river of stars.",
        goal="the bright asteroid ridge",
        hatch="the side hatch",
        sound_hint="a soft tick-tick in the wall",
        sendoff="past the asteroid ridge",
        tags={"space", "foreshadowing"},
    ),
    "comet": Mission(
        id="comet",
        scene="a comet chase with scarf tails and cardboard control panels",
        ship="The thrusters whispered now and then, as if the ship had secrets of its own.",
        goal="the comet trail",
        hatch="the cargo hatch",
        sound_hint="a teeny clink-clink under the floor",
        sendoff="after the comet trail",
        tags={"space", "foreshadowing"},
    ),
}

KIT = {
    "star_crochet": CrochetKit(
        id="star_crochet", label="the crochet kit", phrase="a little crochet kit", hook="hook", loop_sound="click-clack", tags={"crochet"}
    ),
    "luna_yarn": CrochetKit(
        id="luna_yarn", label="the yarn pouch", phrase="a soft yarn pouch", hook="hook", loop_sound="whip-whip", tags={"crochet"}
    ),
    "repair_hook": CrochetKit(
        id="repair_hook", label="the repair hook", phrase="a tiny repair hook", hook="hook", loop_sound="tap-tap", tags={"crochet"}
    ),
}

TROUBLES = {
    "loose_cable": Trouble(
        id="loose_cable", label="the loose cable", phrase="the loose cable", noise="BZZZT!", warning="A loose cable can spark if it wiggles too much.", risky=True, tags={"warning", "sound"}
    ),
    "panel_rattle": Trouble(
        id="panel_rattle", label="the rattling panel", phrase="the rattling panel", noise="Clank-clink!", warning="That panel might pop open and bump the wires.", risky=True, tags={"warning", "sound"}
    ),
    "coolant_ping": Trouble(
        id="coolant_ping", label="the coolant valve", phrase="the coolant valve", noise="Ping-ping!", warning="That valve should not be jarred while the ship is moving.", risky=True, tags={"warning", "sound"}
    ),
}

FIXES = {
    "tape": Fix(id="tape", sense=3, power=3, text="sealed the panel with space tape and tucked the cable away", fail="tried to tape the panel, but the trouble was bigger than the patch", qa_text="sealed the panel with space tape", tags={"tape"}),
    "toolbox": Fix(id="toolbox", sense=3, power=2, text="used the toolbox to brace the panel shut", fail="put a toolbox against it, but the panel still shook", qa_text="used the toolbox to brace the panel shut", tags={"toolbox"}),
    "call_pilot": Fix(id="call_pilot", sense=4, power=4, text="checked the wires with a flashlight and fixed the panel before it could spark", fail="looked, but the problem needed more time and help", qa_text="checked the wires with a flashlight and fixed the panel", tags={"help"}),
    "restart": Fix(id="restart", sense=1, power=1, text="shook the wall and hoped it would settle down", fail="shook the wall, but that only made the noise worse", qa_text="shook the wall", tags={"bad"}),
}

MORAL = {
    "warning": [("Why should you listen to a warning sound?", "A warning sound can be the first clue that something is wrong. If you listen early, you can fix a small problem before it turns into a big one.")],
    "attitude": [("What is a good attitude in a problem?", "A good attitude is calm and respectful. It helps you stop bragging, listen to others, and solve the problem safely.")],
    "crochet": [("What is crochet?", "Crochet is a way of making cloth with a hook and yarn. People loop the yarn again and again to make useful or pretty things.")],
    "space": [("Why do people stay careful on a spaceship?", "Spaceships have lots of moving parts, so small mistakes can become big trouble. Careful choices help everyone stay safe among the stars.")],
}

MORAL_ORDER = ["warning", "attitude", "crochet", "space"]


@dataclass
class StoryParams:
    mission: str
    kit: str
    trouble: str
    fix: str
    hero: str
    hero_type: str
    mate: str
    mate_type: str
    parent_type: str
    delay: int = 0
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(mission="starlane", kit="star_crochet", trouble="loose_cable", fix="call_pilot", hero="Nova", hero_type="girl", mate="Pip", mate_type="boy", parent_type="mother", delay=0),
    StoryParams(mission="asteroid", kit="luna_yarn", trouble="panel_rattle", fix="tape", hero="Iris", hero_type="girl", mate="Milo", mate_type="boy", parent_type="father", delay=0),
    StoryParams(mission="comet", kit="repair_hook", trouble="coolant_ping", fix="toolbox", hero="Zane", hero_type="boy", mate="Tess", mate_type="girl", parent_type="mother", delay=1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for m in MISSIONS:
        for k in KIT:
            for t in TROUBLES:
                if hazard(TROUBLES[t]):
                    combos.append((m, k, t))
    return combos


def explain_rejection(trouble: Trouble) -> str:
    return f"(No story: {trouble.label} is not risky enough to make a foreshadowing turn.)"


def explain_fix(fid: str) -> str:
    f = FIXES[fid]
    better = ", ".join(sorted(x.id for x in sensible_fixes()))
    return f"(Refusing fix '{fid}': sense={f.sense} < {SENSE_MIN}. Try: {better}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    trouble = f["trouble"]
    return [
        f'Write a space-adventure story for a 3-to-5-year-old that includes the words "attitude" and "crochet".',
        f"Tell a story where {hero.id} has a bad attitude on a tiny starship, hears a warning sound near {mission.hatch}, and learns a moral value by fixing the problem calmly.",
        f"Write a gentle spaceship story with foreshadowing, sound effects, and a crochet tool, ending with a moral about listening first.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, parent = f["hero"], f["mate"], f["parent"]
    mission, trouble, fix, kit = f["mission"], f["trouble"], f["fix"], f["kit"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {mate.id} on a little spaceship with {parent.label_word} watching over them. The story follows their mission from a playful beginning to a careful ending.",
        ),
        QAItem(
            question="What warning did they hear?",
            answer=f"They heard {trouble.noise} near {mission.hatch}, and that was the foreshadowing clue. It mattered because {trouble.warning.lower()}",
        ),
        QAItem(
            question="What did {0} do with crochet?".format(hero.id),
            answer=f"{hero.id} carried {kit.phrase} and wanted to keep using it during the mission. The crochet tool was part of the adventure, but the bigger lesson was to use it safely and not brush aside danger.",
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(
            QAItem(
                question=f"How did {parent.label_word} fix the problem?",
                answer=f"{parent.label_word.capitalize()} came in and {fix.qa_text}. That stopped the trouble before it could grow, so the ship stayed safe.",
            )
        )
        qa.append(
            QAItem(
                question="What moral did the children learn?",
                answer="They learned that a calm attitude is better than a show-off one. Listening early and asking for help keeps everyone safe.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="What happened at the end?",
                answer=f"The problem got too big for the first fix, so {parent.label_word} had to work harder to make the ship safe again. The children still learned to listen sooner next time.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["kit"].tags) | set(world.facts["trouble"].tags) | {"crochet", "space", "attitude"}
    out: list[QAItem] = []
    for key in MORAL_ORDER:
        if key in tags and key in MORAL:
            q, a = MORAL[key][0]
            out.append(QAItem(q, a))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risky(T) :- trouble(T).
needs_help(T) :- risky(T).
contained(F, T) :- fix(F), trouble(T), power(F, P), severity(T, S), P >= S.
severity(T, S) :- trouble(T), delay(D), S = 1 + D.
outcome(averted) :- calm_ending.
outcome(contained) :- not calm_ending, contained(_, _).
outcome(burned) :- not calm_ending, not contained(_, _).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for m in MISSIONS:
        lines.append(asp.fact("mission", m))
    for k in KIT:
        lines.append(asp.fact("kit", k))
    for t in TROUBLES:
        lines.append(asp.fact("trouble", t))
        if TROUBLES[t].risky:
            lines.append(asp.fact("risky", t))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
        lines.append(asp.fact("power", f, FIXES[f].power))
        lines.append(asp.fact("sense", f, FIXES[f].sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show risky/1."))
    return sorted(set(asp.atoms(model, "risky")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    if set(asp_valid_combos()) != {(t,) for t in valid_combos()}:
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"Story generation failed: {exc}")
    print("OK" if rc == 0 else "FAIL")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure crochet storyworld.")
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--kit", choices=KIT)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))
    if args.trouble and not TROUBLES[args.trouble].risky:
        raise StoryError(explain_rejection(TROUBLES[args.trouble]))
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combos.")
    m, k, t = rng.choice(combos)
    return StoryParams(
        mission=args.mission or m,
        kit=args.kit or k,
        trouble=args.trouble or t,
        fix=args.fix or rng.choice(sorted([f.id for f in sensible_fixes()])),
        hero=args.hero or rng.choice(["Nova", "Iris", "Zane", "Luna", "Milo"]),
        hero_type=args.hero_type or rng.choice(["girl", "boy"]),
        mate=args.mate or rng.choice(["Pip", "Tess", "Orin", "Cleo"]),
        mate_type=args.mate_type or rng.choice(["girl", "boy"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
        delay=args.delay if args.delay is not None else rng.randint(0, 2),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS or params.kit not in KIT or params.trouble not in TROUBLES or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = tell(MISSIONS[params.mission], KIT[params.kit], TROUBLES[params.trouble], FIXES[params.fix],
                 hero_name=params.hero, hero_type=params.hero_type,
                 mate_name=params.mate, mate_type=params.mate_type,
                 parent_type=params.parent_type, delay=params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program(show="#show risky/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} risky combos:")
        for combo in combos:
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
