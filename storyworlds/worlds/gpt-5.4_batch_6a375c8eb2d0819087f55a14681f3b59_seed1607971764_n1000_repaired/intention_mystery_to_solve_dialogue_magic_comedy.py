#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/intention_mystery_to_solve_dialogue_magic_comedy.py
==============================================================================

A standalone storyworld about a child magician trying to solve a silly mystery:
who made all the town bells honk like geese before the bakery parade?

This world models a small comic domain with:
- intention: a helper's good intention can accidentally cause the problem
- mystery to solve: clues narrow down who cast the wrong spell
- dialogue: the story is driven by spoken guesses, worries, and explanations
- magic: simple spells change the physical state of the bells and the square

The engine is classical and state-driven. A child magician plans a parade trick,
a bell problem appears, clues are found, a suspect is identified, and the spell
is undone. Some combinations are refused when the clues would not honestly point
to the culprit or the chosen fix would not work.

Run it
------
    python storyworlds/worlds/gpt-5.4/intention_mystery_to_solve_dialogue_magic_comedy.py
    python storyworlds/worlds/gpt-5.4/intention_mystery_to_solve_dialogue_magic_comedy.py --suspect broom
    python storyworlds/worlds/gpt-5.4/intention_mystery_to_solve_dialogue_magic_comedy.py --effect hiccup_suds
    python storyworlds/worlds/gpt-5.4/intention_mystery_to_solve_dialogue_magic_comedy.py --all
    python storyworlds/worlds/gpt-5.4/intention_mystery_to_solve_dialogue_magic_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/intention_mystery_to_solve_dialogue_magic_comedy.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "witch"}
        male = {"boy", "father", "dad", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    centerpiece: str
    crowd: str
    snack: str
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
class BellEffect:
    id: str
    noise: str
    line: str
    clue_mark: str
    messy_trace: str
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
class Suspect:
    id: str
    label: str
    phrase: str
    kind: str
    motive: str
    intention_text: str
    clue: str
    clue_kind: str
    funny_move: str
    magical: bool = True
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
class DetectiveTool:
    id: str
    label: str
    phrase: str
    reveals: str
    text: str
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
class FixSpell:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    action_text: str
    qa_text: str
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


def _r_bells_disturb(world: World) -> list[str]:
    out: list[str] = []
    bells = world.get("bells")
    if bells.meters["bewitched"] < THRESHOLD:
        return out
    sig = ("disturb", "bells")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    square = world.get("square")
    square.meters["confusion"] += 1
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["surprise"] += 1
    out.append("__disturb__")
    return out


def _r_detective_progress(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters["clues_found"] < 2:
        return out
    sig = ("ready_guess", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["confidence"] += 1
    out.append("__ready__")
    return out


def _r_fix_clears_trouble(world: World) -> list[str]:
    out: list[str] = []
    bells = world.get("bells")
    if bells.meters["fixed"] < THRESHOLD:
        return out
    sig = ("clear", bells.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bells.meters["bewitched"] = 0.0
    world.get("square").meters["confusion"] = 0.0
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["relief"] += 1
    out.append("__clear__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bells_disturb", tag="physical", apply=_r_bells_disturb),
    Rule(name="detective_progress", tag="social", apply=_r_detective_progress),
    Rule(name="fix_clears_trouble", tag="physical", apply=_r_fix_clears_trouble),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_matches(effect: BellEffect, suspect: Suspect, tool: DetectiveTool) -> bool:
    return suspect.clue_kind == tool.reveals and bool(effect.clue_mark)


def sensible_fixes() -> list[FixSpell]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def disturbance_severity(effect: BellEffect, suspect: Suspect) -> int:
    extra = 1 if suspect.kind == "creature" else 0
    if effect.id == "goose_honk":
        base = 2
    elif effect.id == "opera_echo":
        base = 2
    else:
        base = 3
    return base + extra


def fix_works(fix: FixSpell, effect: BellEffect, suspect: Suspect) -> bool:
    return fix.power >= disturbance_severity(effect, suspect)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for effect_id, effect in EFFECTS.items():
            for suspect_id, suspect in SUSPECTS.items():
                for tool_id, tool in TOOLS.items():
                    if clue_matches(effect, suspect, tool) and sensible_fixes():
                        combos.append((setting_id, effect_id, suspect_id, tool_id))
    return combos


def predict_guess(effect: BellEffect, suspect: Suspect, tool: DetectiveTool) -> dict:
    honest = clue_matches(effect, suspect, tool)
    return {
        "honest_clue": honest,
        "clue_text": suspect.clue if honest else "",
    }


def introduce(world: World, child: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.place}, {child.id} skipped into the square with a satchel of harmless practice magic. "
        f"The bakery parade was almost ready, and {setting.crowd} waited around {setting.centerpiece}."
    )
    world.say(
        f'{child.id} grinned. "My intention is simple," {child.pronoun()} said. '
        f'"I only want one neat sparkle over the buns, not a disaster with legs."'
    )


def plan_parade(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    helper.memes["helpfulness"] += 1
    world.say(
        f'{helper.id} held a list and whispered, "Sparkle, wave, bow, and then eat {setting.snack}."'
    )
    world.say(
        f'"Perfect," said {child.id}. "A tiny spell, a tidy parade, and no surprises bigger than a loaf."'
    )


def trouble_starts(world: World, effect: BellEffect, suspect: Suspect) -> None:
    bells = world.get("bells")
    bells.meters["bewitched"] += 1
    bells.meters["volume"] += 1
    bells.attrs["effect_id"] = effect.id
    world.facts["effect_line"] = effect.line
    world.facts["clue_mark"] = effect.clue_mark
    world.facts["suspect_intention"] = suspect.intention_text
    propagate(world, narrate=False)
    world.say(
        f"Then every bell in the square blurted out {effect.noise}. {effect.line}"
    )
    world.say(
        f'The baker dropped a tray. "My buns are marching away from the noise!" he cried.'
    )


def react(world: World, child: Entity, helper: Entity) -> None:
    child.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f'"This was not my plan," said {child.id}. "{helper.id}, did you add anything to my kit?"'
    )
    world.say(
        f'"Only neatness and hope," said {helper.id}. "Well... and maybe one tiny extra polish spell."'
    )


def search_for_clues(world: World, child: Entity, helper: Entity,
                     effect: BellEffect, suspect: Suspect, tool: DetectiveTool) -> None:
    detective = world.get("detective")
    pred = predict_guess(effect, suspect, tool)
    world.facts["predicted_honest"] = pred["honest_clue"]
    world.facts["predicted_clue"] = pred["clue_text"]
    detective.meters["clues_found"] += 1
    world.say(
        f'{child.id} pulled out {tool.phrase}. "{tool.text}"'
    )
    detective.meters["clues_found"] += 1
    world.say(
        f"The spell-light wiggled over the cobbles and showed {effect.clue_mark}. "
        f'Helper or not, something had definitely touched the bells.'
    )
    propagate(world, narrate=False)
    if pred["honest_clue"]:
        world.say(
            f'"Look!" said {helper.id}. "{suspect.clue}"'
        )


def accuse(world: World, child: Entity, suspect: Suspect) -> None:
    detective = world.get("detective")
    detective.memes["confidence"] += 1
    world.say(
        f'{child.id} planted both feet. "I know it now," {child.pronoun()} said. '
        f'"It was {suspect.phrase}."'
    )
    world.say(
        f'"Why would {suspect.label} do that?" asked the baker.'
    )


def reveal(world: World, suspect: Suspect) -> None:
    culprit = world.get("culprit")
    culprit.memes["shame"] += 1
    culprit.memes["kindness"] += 1
    world.say(
        f"Out popped {suspect.phrase}, looking embarrassed and slightly glittery. "
        f'"I had a good intention," {culprit.pronoun()} said. "{suspect.intention_text}"'
    )
    world.say(
        f"{suspect.funny_move} The square stared for one blink, and then even the baker had to laugh."
    )


def fix_scene(world: World, child: Entity, fix: FixSpell, effect: BellEffect, suspect: Suspect) -> None:
    bells = world.get("bells")
    if fix_works(fix, effect, suspect):
        bells.meters["fixed"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{child.id} lifted {fix.phrase}. "{fix.label}, please be polite this time," {child.pronoun()} said.'
        )
        world.say(fix.action_text.format(noise=effect.noise))
    else:
        bells.meters["bewitched"] += 1
        world.get("square").meters["confusion"] += 1
        world.say(
            f'{child.id} tried {fix.phrase}, but the bells only answered with even louder {effect.noise}.'
        )


def ending(world: World, child: Entity, helper: Entity, setting: Setting,
           suspect: Suspect, fix: FixSpell, effect: BellEffect) -> None:
    if world.get("bells").meters["bewitched"] < THRESHOLD:
        child.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(
            f'Soon the bells rang like bells again. "{setting.snack} can return to being food," the baker said with a bow.'
        )
        world.say(
            f'{suspect.phrase.capitalize()} helped stack chairs and promised to ask before improving anybody else\'s magic. '
            f'{child.id} laughed and said, "Next time, keep the intention and lose the surprise."'
        )
        world.say(
            f"By parade time, the square was bright, calm, and full of giggles instead of {effect.noise}."
        )
    else:
        world.say(
            f"The parade had to march in a wide, silly loop around the noisy bells. "
            f"Nobody was hurt, but everyone agreed that mystery first and magic second was a better order."
        )


def tell(setting: Setting, effect: BellEffect, suspect_cfg: Suspect,
         tool: DetectiveTool, fix: FixSpell, child_name: str = "Nora",
         child_gender: str = "girl", helper_name: str = "Pip",
         helper_gender: str = "boy", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="hero",
        attrs={"intention": "make one neat sparkle", "age": "little"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        attrs={"intention": "be useful"},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type="thing" if suspect_cfg.kind != "person" else "wizard",
        role="culprit",
        label=suspect_cfg.label,
        attrs={"good_intention": suspect_cfg.intention_text},
    ))
    world.add(Entity(id="bells", type="bells", label="the town bells"))
    world.add(Entity(id="square", type="square", label="the square"))
    world.add(Entity(id="detective", type="detective", label="the detective work"))
    world.facts.update(
        setting=setting,
        effect=effect,
        suspect=suspect_cfg,
        tool=tool,
        fix=fix,
        child=child,
        helper=helper,
        parent_type=parent_type,
        solved=False,
        successful_fix=False,
    )

    introduce(world, child, setting)
    plan_parade(world, child, helper, setting)

    world.para()
    trouble_starts(world, effect, suspect_cfg)
    react(world, child, helper)

    world.para()
    search_for_clues(world, child, helper, effect, suspect_cfg, tool)
    accuse(world, child, suspect_cfg)
    reveal(world, suspect_cfg)

    world.para()
    fix_scene(world, child, fix, effect, suspect_cfg)
    solved = clue_matches(effect, suspect_cfg, tool)
    successful_fix = fix_works(fix, effect, suspect_cfg)
    world.facts["solved"] = solved
    world.facts["successful_fix"] = successful_fix
    world.facts["outcome"] = "solved" if solved and successful_fix else "messy"
    ending(world, child, helper, setting, suspect_cfg, fix, effect)
    return world


SETTINGS = {
    "square": Setting(
        id="square",
        place="the little town square",
        centerpiece="the fountain with a duck on top",
        crowd="neighbors in aprons and hats",
        snack="cinnamon buns",
        tags={"square", "parade"},
    ),
    "market": Setting(
        id="market",
        place="the covered market lane",
        centerpiece="the striped jam stall",
        crowd="shopkeepers peeking over baskets",
        snack="berry tarts",
        tags={"market", "parade"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the harbor clock yard",
        centerpiece="the old rope winch",
        crowd="sailors and aunties carrying ribbons",
        snack="butter rolls",
        tags={"harbor", "parade"},
    ),
}

EFFECTS = {
    "goose_honk": BellEffect(
        id="goose_honk",
        noise="a chorus of grand goose honks",
        line="The sound bounced off every window until even the pigeons looked offended.",
        clue_mark="a trail of shiny yellow feathers and silver dust",
        messy_trace="feathers",
        tags={"bells", "magic", "goose"},
    ),
    "opera_echo": BellEffect(
        id="opera_echo",
        noise="tiny opera notes singing their own names",
        line='Each ding added a new "laaa!" until the fountain seemed to be taking singing lessons.',
        clue_mark="a ribbon-shaped shimmer floating near the bell ropes",
        messy_trace="ribbon shimmer",
        tags={"bells", "magic", "opera"},
    ),
    "hiccup_suds": BellEffect(
        id="hiccup_suds",
        noise="wet hiccups that puffed out soap bubbles",
        line="The bubbles drifted into hats, bread baskets, and one very surprised moustache.",
        clue_mark="round bubble prints and pearly foam around the clapper",
        messy_trace="soap foam",
        tags={"bells", "magic", "bubbles"},
    ),
}

SUSPECTS = {
    "broom": Suspect(
        id="broom",
        label="the broom",
        phrase="the broom from the bakery wall",
        kind="helper_object",
        motive="help clean",
        intention_text="I meant to sweep the square so well that even the bells would shine.",
        clue="It left neat brush lines in the silver dust.",
        clue_kind="sweep",
        funny_move="Then it bowed so low that its bristles sneezed",
        magical=True,
        tags={"broom", "magic", "help"},
    ),
    "goose": Suspect(
        id="goose",
        label="the goose",
        phrase="the mayor's goose in a blue ribbon",
        kind="creature",
        motive="join parade",
        intention_text="I wanted the bells to sound more festive, like a proper goose parade.",
        clue="There are webbed prints mixed in with the glitter.",
        clue_kind="tracks",
        funny_move="The goose gave one proud honk, as if this explained everything",
        magical=True,
        tags={"goose", "magic", "help"},
    ),
    "apprentice": Suspect(
        id="apprentice",
        label="the apprentice",
        phrase="the sleepy apprentice from the clock shop",
        kind="person",
        motive="improve spell",
        intention_text="I only wanted to help your sparkle carry farther, so everyone could see it.",
        clue="That blue chalk is the same kind the clock shop uses for repair notes.",
        clue_kind="chalk",
        funny_move="He pushed his hat back and discovered a bubble sitting on his nose",
        magical=True,
        tags={"apprentice", "magic", "help"},
    ),
}

TOOLS = {
    "magnifying_moon": DetectiveTool(
        id="magnifying_moon",
        label="magnifying moon",
        phrase="a tiny silver moon lens",
        reveals="tracks",
        text='"Magnifying Moon, show me the steps that tiptoed before the trouble."',
        tags={"tool", "mystery"},
    ),
    "dust_compass": DetectiveTool(
        id="dust_compass",
        label="dust compass",
        phrase="a brass dust compass",
        reveals="sweep",
        text='"Dust Compass, point toward the fussiest cleaning in town."',
        tags={"tool", "mystery"},
    ),
    "chalk_sniffer": DetectiveTool(
        id="chalk_sniffer",
        label="chalk sniffer",
        phrase="a sneezy little chalk sniffer",
        reveals="chalk",
        text='"Chalk Sniffer, sniff out the freshest scribble magic."',
        tags={"tool", "mystery"},
    ),
}

FIXES = {
    "untangle_tune": FixSpell(
        id="untangle_tune",
        label="Untangle Tune",
        phrase="the Untangle Tune",
        power=3,
        sense=3,
        action_text='A soft ribbon of sound wrapped around the bells, tugged the mixed-up magic loose, and let the {noise} melt away.',
        qa_text="used the Untangle Tune to loosen the mixed-up spell until the bells sounded normal again",
        tags={"fix", "magic"},
    ),
    "reverse_polish": FixSpell(
        id="reverse_polish",
        label="Reverse Polish",
        phrase="Reverse Polish",
        power=2,
        sense=2,
        action_text='The shine on the bells folded back into a neat spark and zipped into the wand, and the {noise} stopped at once.',
        qa_text="used Reverse Polish to pull the extra magic off the bells",
        tags={"fix", "magic"},
    ),
    "tickle_joke": FixSpell(
        id="tickle_joke",
        label="Tickle Joke",
        phrase="Tickle Joke",
        power=1,
        sense=1,
        action_text='The bells laughed, but laughing only made the sound sillier.',
        qa_text="told a tickle spell to the bells",
        tags={"fix", "magic"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Pip", "Ben", "Max", "Leo", "Sam", "Finn", "Theo", "Eli"]


@dataclass
class StoryParams:
    setting: str
    effect: str
    suspect: str
    tool: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
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


KNOWLEDGE = {
    "bells": [(
        "What does a bell do?",
        "A bell makes a ringing sound when it is struck or swung. People use bells to call attention or mark an event."
    )],
    "magic": [(
        "What is magic in a story?",
        "In a story, magic is a pretend power that can change things in surprising ways. Good story magic still needs care, because mistakes can cause problems."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is a problem where you do not know the answer yet. You solve it by noticing clues and thinking about what they mean."
    )],
    "broom": [(
        "What is a broom for?",
        "A broom is for sweeping dust and crumbs off the floor. It helps clean, but in a magic story it might also cause trouble by accident."
    )],
    "goose": [(
        "Why are geese noisy?",
        "Geese honk to call to each other and show where they are. Their voices can sound very loud and funny."
    )],
    "apprentice": [(
        "What is an apprentice?",
        "An apprentice is someone who is still learning from a skilled grown-up. They practice, make mistakes, and get better over time."
    )],
    "tool": [(
        "What does a detective use to solve a mystery?",
        "A detective uses clues, careful looking, and good questions. In a magic story, a tool may help reveal what ordinary eyes missed."
    )],
    "fix": [(
        "Why is it important to fix a mistake after you find it?",
        "Finding the cause is only part of the job. Fixing the mistake helps make things safe and calm again."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "magic", "bells", "tool", "fix", "broom", "goose", "apprentice"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    effect = f["effect"]
    suspect = f["suspect"]
    setting = f["setting"]
    return [
        f'Write a funny magic mystery for a young child that includes the word "intention" and takes place in {setting.place}.',
        f"Tell a dialogue-rich story where {child.id} must discover why the bells are making {effect.noise} and learns that {suspect.label} had a good intention but caused a silly problem.",
        f'Write a gentle comedy about clues, mistaken magic, and a cheerful solution, ending with the town calm again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    effect = f["effect"]
    suspect = f["suspect"]
    tool = f["tool"]
    fix = f["fix"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little magician trying to help with a parade, and {helper.id}, who searches for clues alongside {child.pronoun('object')}. Together they try to discover who bewitched the bells."
        ),
        (
            "What problem started the mystery?",
            f"The town bells suddenly began making {effect.noise}. That strange sound interrupted the parade plans and told everyone that some magic had gone wrong."
        ),
        (
            f"How did {child.id} look for clues?",
            f"{child.id} used {tool.phrase} to inspect the bell area. The tool helped reveal a clue that pointed toward {suspect.label} instead of leaving the mystery as a wild guess."
        ),
        (
            f"Why did {suspect.label} cause the trouble?",
            f"{suspect.phrase.capitalize()} did not mean to ruin the day. {suspect.intention_text}"
        ),
    ]
    if outcome == "solved":
        qa.append((
            f"How did {child.id} fix the bells?",
            f"{child.id} {fix.qa_text}. That worked because the spell was strong enough to undo the mixed-up magic on the bells."
        ))
        qa.append((
            "How did the story end?",
            f"The bells sounded normal again, the parade could continue, and everyone laughed about the silly mistake. The ending shows that a good intention still needs care, but mistakes can be mended kindly."
        ))
    else:
        qa.append((
            f"Did {child.id} solve the problem completely?",
            f"{child.pronoun().capitalize()} figured out the cause, but the fix was too weak to stop the bells. So the mystery was understood, yet the ending stayed a little messy and comic."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "magic", "bells", "tool", "fix"}
    suspect = world.facts["suspect"]
    if suspect.id in KNOWLEDGE:
        tags.add(suspect.id)
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="square",
        effect="goose_honk",
        suspect="goose",
        tool="magnifying_moon",
        fix="untangle_tune",
        child_name="Nora",
        child_gender="girl",
        helper_name="Pip",
        helper_gender="boy",
        parent="mother",
        seed=1,
    ),
    StoryParams(
        setting="market",
        effect="opera_echo",
        suspect="apprentice",
        tool="chalk_sniffer",
        fix="reverse_polish",
        child_name="Mia",
        child_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="father",
        seed=2,
    ),
    StoryParams(
        setting="harbor",
        effect="hiccup_suds",
        suspect="broom",
        tool="dust_compass",
        fix="untangle_tune",
        child_name="Ava",
        child_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        parent="mother",
        seed=3,
    ),
    StoryParams(
        setting="square",
        effect="hiccup_suds",
        suspect="goose",
        tool="magnifying_moon",
        fix="reverse_polish",
        child_name="Lily",
        child_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        parent="father",
        seed=4,
    ),
]


def explain_rejection(effect: BellEffect, suspect: Suspect, tool: DetectiveTool) -> str:
    return (
        f"(No story: {tool.label} reveals {tool.reveals}, but the clue for {suspect.label} "
        f"would not honestly point there in the {effect.id} case. Pick a matching detective tool.)"
    )


def explain_fix_rejection(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
valid(S, E, U, T) :- setting(S), effect(E), suspect(U), tool(T), clue_kind(U, K), reveals(T, K), sensible_fix_exists.

sensible_fix(F) :- fix(F), sense(F, N), sense_min(M), N >= M.
sensible_fix_exists :- sensible_fix(_).

severity(E, U, 3) :- effect(E), suspect(U), E = hiccup_suds, kind(U, creature).
severity(E, U, 2) :- effect(E), suspect(U), E = goose_honk, not kind(U, creature).
severity(E, U, 3) :- effect(E), suspect(U), E = goose_honk, kind(U, creature).
severity(E, U, 2) :- effect(E), suspect(U), E = opera_echo, not kind(U, creature).
severity(E, U, 3) :- effect(E), suspect(U), E = opera_echo, kind(U, creature).
severity(E, U, 3) :- effect(E), suspect(U), E = hiccup_suds, not kind(U, creature).
works :- chosen_fix(F), power(F, P), chosen_effect(E), chosen_suspect(U), severity(E, U, V), P >= V.
outcome(solved) :- works.
outcome(messy) :- not works.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for eid in EFFECTS:
        lines.append(asp.fact("effect", eid))
    for uid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", uid))
        lines.append(asp.fact("clue_kind", uid, suspect.clue_kind))
        lines.append(asp.fact("kind", uid, suspect.kind))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("reveals", tid, tool.reveals))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("power", fid, fix.power))
        lines.append(asp.fact("sense", fid, fix.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_effect", params.effect),
        asp.fact("chosen_suspect", params.suspect),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if fix_works(FIXES[params.fix], EFFECTS[params.effect], SUSPECTS[params.suspect]) else "messy"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    py_fixes = {f.id for f in sensible_fixes()}
    asp_fixes = set(asp_sensible_fixes())
    if py_fixes == asp_fixes:
        print(f"OK: sensible fixes match ({sorted(py_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_fixes)} python={sorted(py_fixes)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comic magic mystery storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--effect", choices=EFFECTS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(args.fix))
    if args.effect and args.suspect and args.tool:
        if not clue_matches(EFFECTS[args.effect], SUSPECTS[args.suspect], TOOLS[args.tool]):
            raise StoryError(explain_rejection(EFFECTS[args.effect], SUSPECTS[args.suspect], TOOLS[args.tool]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.effect is None or c[1] == args.effect)
        and (args.suspect is None or c[2] == args.suspect)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, effect, suspect, tool = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        setting=setting,
        effect=effect,
        suspect=suspect,
        tool=tool,
        fix=fix,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.effect not in EFFECTS:
        raise StoryError(f"(Unknown effect: {params.effect})")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect: {params.suspect})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if not clue_matches(EFFECTS[params.effect], SUSPECTS[params.suspect], TOOLS[params.tool]):
        raise StoryError(explain_rejection(EFFECTS[params.effect], SUSPECTS[params.suspect], TOOLS[params.tool]))
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix_rejection(params.fix))

    world = tell(
        SETTINGS[params.setting],
        EFFECTS[params.effect],
        SUSPECTS[params.suspect],
        TOOLS[params.tool],
        FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/4.\n#show sensible_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        fixes = asp_sensible_fixes()
        print(f"sensible fixes: {', '.join(fixes)}\n")
        print(f"{len(combos)} compatible (setting, effect, suspect, tool) combos:\n")
        for setting, effect, suspect, tool in combos:
            print(f"  {setting:8} {effect:12} {suspect:10} {tool}")
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
            header = (
                f"### {p.child_name}: {p.effect} / {p.suspect} at {p.setting}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
