#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/swarm_executive_humor_conflict_mystery_to_solve.py
===================================================================================

A small superhero storyworld about a hero, an executive, a puzzling office
problem, and a swarm of tiny troublemakers. The world supports a few close
variations, but every valid story must still feel like one complete TinyStories-
style episode: a funny setup, a real conflict, a mystery to solve, and a clear
ending image.

Seed prompt:
- Words: swarm, executive
- Features: Humor, Conflict, Mystery to Solve
- Style: Superhero Story
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Mystery:
    id: str
    clue: str
    joke: str
    reveal: str
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
class SwarmThreat:
    id: str
    label: str
    effect: str
    sound: str
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
class Response:
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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    swarm: str
    response: str
    hero: str
    hero_gender: str
    executive: str
    executive_gender: str
    sidekick: str
    sidekick_gender: str
    hero_trait: str = "cheerful"
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


def _r_alarm(world: World) -> list[str]:
    out = []
    swarm = world.get("swarm")
    if swarm.meters["buzz"] >= THRESHOLD and ("alarm", swarm.id) not in world.fired:
        world.fired.add(("alarm", swarm.id))
        world.get("hall").meters["confusion"] += 1
        world.get("hero").memes["alert"] += 1
        world.get("exec").memes["worry"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(i for i in items if not i.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(setting: Setting, mystery: Mystery, swarm: SwarmThreat, response: Response) -> bool:
    return "mystery" in setting.affords and "swarm" in swarm.tags and response.sense >= SENSE_MIN and mystery.id in MYSTERY_BY_ID


SENSE_MIN = 2
BRAVERY_INIT = 6.0


def sensical_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for sw in SWARMS:
                for r in RESPONSES:
                    if reasonableness_ok(SETTINGS[s], MYSTERIES[m], SWARMS[sw], RESPONSES[r]):
                        combos.append((s, m, sw, r))
    return combos


def _do_swarm(world: World, narrate: bool = True) -> None:
    swarm = world.get("swarm")
    swarm.meters["buzz"] += 1
    swarm.meters["mischief"] += 1
    propagate(world, narrate=narrate)


def investigate(world: World, hero: Entity, exec_ent: Entity, setting: Setting, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"In {setting.place}, {hero.id} landed in a dramatic red cape and found {exec_ent.id}, "
        f"the executive, staring at a baffling clue. {setting.detail}"
    )
    world.say(
        f'{hero.id} pointed at the sticky note. "A mystery in an office? Now that is a job for a hero."'
    )
    world.say(
        f'The note said, "{mystery.clue}" but the room had no idea who wrote it.'
    )


def joke(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    world.say(
        f'{sidekick.id} squinted at the clue and whispered, "That note is so strange it almost '
        f'feels like a joke." {hero.id} snorted, because even heroes were allowed a giggle.'
    )
    world.say(
        f'Then {sidekick.id} found another hint: "{mystery.joke}"'
    )


def warn(world: World, sidekick: Entity, hero: Entity, exec_ent: Entity, swarm: SwarmThreat) -> None:
    sidekick.memes["caution"] += 1
    world.say(
        f'{sidekick.id} frowned. "Something is wrong. The {swarm.label} is not just noisy; '
        f'it is hiding inside the air vents." {exec_ent.id} gasped and clutched {exec_ent.pronoun("possessive")} tie.'
    )


def summon(world: World, swarm: SwarmThreat) -> None:
    world.get("swarm").tags.add("active")
    _do_swarm(world, narrate=False)
    world.say(
        f"Before anyone could finish the sentence, the {swarm.label} burst out with a {swarm.sound} "
        f"and zipped in every direction like a thousand tiny troublemakers."
    )


def battle(world: World, hero: Entity, exec_ent: Entity, swarm: SwarmThreat) -> None:
    hero.memes["defiance"] += 1
    exec_ent.memes["panic"] += 1
    world.say(
        f"{hero.id} tried to swoop the {swarm.label} into a jar, but the swarm split apart and slipped away."
    )


def solve(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    hero.memes["confidence"] += 1
    sidekick.memes["pride"] += 1
    world.say(
        f"Then {sidekick.id} noticed the reveal hiding in plain sight: {mystery.reveal}. "
        f"{hero.id} laughed so hard {hero.id} nearly dropped {hero.pronoun('possessive')} cape."
    )


def rescue(world: World, response: Response, swarm: SwarmThreat, exec_ent: Entity) -> None:
    body = response.text.replace("{swarm}", swarm.label)
    world.say(
        f"{exec_ent.id} called for help and {body}."
    )
    world.say(
        f"The buzzing slowed, the office lights steadied, and the executive finally stopped looking so flustered."
    )


def ending(world: World, hero: Entity, sidekick: Entity, exec_ent: Entity, setting: Setting, mystery: Mystery) -> None:
    world.say(
        f"Afterward, {exec_ent.id} taped the silly clue to the wall as a reminder, and {hero.id} "
        f"and {sidekick.id} stood beside the cleaned-up desk."
    )
    world.say(
        f"The mystery was solved, the swarm was gone, and {setting.place} looked calm again except for one crooked smiley face note."
    )


def tell(setting: Setting, mystery: Mystery, swarm: SwarmThreat, response: Response,
         hero_name: str, hero_gender: str, exec_name: str, exec_gender: str,
         sidekick_name: str, sidekick_gender: str, hero_trait: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[hero_trait]))
    exec_ent = world.add(Entity(id=exec_name, kind="character", type=exec_gender, role="executive", label="the executive"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_gender, role="sidekick"))
    hall = world.add(Entity(id="hall", kind="room", type="room", label="the hall"))
    swarm_ent = world.add(Entity(id="swarm", kind="thing", type="swarm", label=swarm.label, tags=set(swarm.tags)))
    world.facts["setting"] = setting
    world.facts["mystery"] = mystery
    world.facts["swarm"] = swarm
    world.facts["response"] = response

    investigate(world, hero, exec_ent, setting, mystery)
    world.para()
    joke(world, hero, sidekick, mystery)
    warn(world, sidekick, hero, exec_ent, swarm)
    summon(world, swarm)
    world.para()
    battle(world, hero, exec_ent, swarm)
    solve(world, hero, sidekick, mystery)
    if response.sense >= SENSE_MIN:
        rescue(world, response, swarm, exec_ent)
    ending(world, hero, sidekick, exec_ent, setting, mystery)

    world.facts.update(hero=hero, exec=exec_ent, sidekick=sidekick, hall=hall, swarm_ent=swarm_ent)
    return world


SETTINGS = {
    "tower": Setting(id="tower", place="Skyline Tower", detail="The elevator kept opening on the wrong floor, as if the building were playing hide-and-seek.", affords={"mystery", "swarm"}),
    "museum": Setting(id="museum", place="Metro Museum", detail="A velvet rope hung crookedly beside the elevator panel, which made the lobby look extra suspicious.", affords={"mystery", "swarm"}),
    "lab": Setting(id="lab", place="Starlight Lab", detail="A blinking dashboard and a squeaky cart made the hallway look like a comic book page.", affords={"mystery", "swarm"}),
}

MYSTERIES = {
    "note": Mystery(id="note", clue="Who keeps changing the elevator buttons?", joke="The elevator only stops on floors with extra cookies.", reveal="A wind-up pen had been bouncing in a pocket and pressing the buttons by accident.", tags={"mystery"}),
    "cap": Mystery(id="cap", clue="Who left the giant cape on the conference table?", joke="The cape was so long it could have auditioned to be a curtain.", reveal="The executive's own cape got stuck in the chair and slid off during lunch.", tags={"mystery"}),
    "stamp": Mystery(id="stamp", clue="Why are the memo pages covered in tiny circles?", joke="The circles looked like a polka-dot parade had marched through paperwork.", reveal="A seal stamp rolled off the desk and kept decorating every page it touched.", tags={"mystery"}),
}

SWARMS = {
    "robot_bees": SwarmThreat(id="robot_bees", label="robot bees", effect="buzz", sound="BZZZT", tags={"swarm"}),
    "paper_moths": SwarmThreat(id="paper_moths", label="paper moths", effect="flutter", sound="FRRRP", tags={"swarm"}),
    "micro_drones": SwarmThreat(id="micro_drones", label="micro-drones", effect="whirr", sound="WHIIII", tags={"swarm"}),
}

RESPONSES = {
    "net": Response(id="net", sense=3, power=3, text="hurled a glitter net over the {swarm} until the buzzing ball of trouble landed safely on the carpet", fail="tried a glitter net, but the {swarm} flew right through it", qa_text="hurled a glitter net over the swarm and pinned it to the carpet", tags={"net"}),
    "fan": Response(id="fan", sense=2, power=2, text="switched on the giant fan and blew the {swarm} straight into an open window", fail="switched on the fan, but it only made the {swarm} wobble faster", qa_text="switched on the giant fan and blew the swarm out the window", tags={"fan"}),
    "vacuum": Response(id="vacuum", sense=4, power=4, text="used the vacuum tube to scoop up the {swarm} before it could swarm the whole desk", fail="used the vacuum, but the {swarm} zipped away before the hose reached it", qa_text="used the vacuum tube to scoop up the swarm", tags={"vacuum"}),
    "paperbox": Response(id="paperbox", sense=1, power=1, text="opened a paper box and hoped the {swarm} would politely move in", fail="opened a paper box, but the {swarm} laughed and ignored it", qa_text="opened a paper box and hoped the swarm would move in", tags={"paperbox"}),
}

HEROES = ["Nova", "Spark", "Comet", "Vector", "Blaze", "Orbit"]
SIDEKICKS = ["Pip", "Milo", "June", "Tess", "Rin", "Otto"]
EXECUTIVES = ["Ms. Ledger", "Mr. Brisk", "Dr. Quartz", "Chief Banner"]
TRAITS = ["cheerful", "curious", "bright", "bold", "inventive"]

MYSTERY_BY_ID = MYSTERIES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: a mystery, an executive, and a troublesome swarm.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--swarm", choices=SWARMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--executive")
    ap.add_argument("--executive-gender", choices=["woman", "man"])
    ap.add_argument("--sidekick")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{args.response}': it is too silly for a real solution.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.swarm is None or c[2] == args.swarm)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, swarm, response = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    executive_gender = args.executive_gender or rng.choice(["woman", "man"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HEROES)
    executive = args.executive or rng.choice(EXECUTIVES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, mystery=mystery, swarm=swarm, response=response,
                       hero=hero, hero_gender=hero_gender, executive=executive,
                       executive_gender=executive_gender, sidekick=sidekick,
                       sidekick_gender=sidekick_gender, hero_trait=rng.choice(TRAITS))


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.swarm not in SWARMS or params.response not in RESPONSES:
        raise StoryError("(Invalid parameters for this storyworld.)")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], SWARMS[params.swarm],
                 RESPONSES[params.response], params.hero, params.hero_gender,
                 params.executive, params.executive_gender, params.sidekick,
                 params.sidekick_gender, params.hero_trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "{f["swarm"].label}" and "executive".',
        f"Tell a funny mystery story where {f['hero'].id} helps {f['exec'].id}, the executive, solve a strange office problem caused by a {f['swarm'].label}.",
        f"Write a short superhero story with humor, conflict, and a mystery to solve at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, exec_ent, sidekick = f["hero"], f["exec"], f["sidekick"]
    mystery, swarm = f["mystery"], f["swarm"]
    return [
        QAItem(question="Who was the story about?", answer=f"It was about {hero.id}, {sidekick.id}, and {exec_ent.id}, the executive. They worked together to solve the strange problem."),
        QAItem(question="What was the mystery?", answer=f"The mystery was {mystery.clue} The answer turned out to be {mystery.reveal}"),
        QAItem(question=f"What happened when the {swarm.label} appeared?", answer=f"The {swarm.label} burst out with a noisy surprise and caused real trouble in the building. That was the conflict the hero had to fix."),
        QAItem(question="How did the story end?", answer=f"It ended with the mystery solved and the office calm again. The executive could relax, and the hero stood by the cleaned-up desk."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["swarm"].tags) | set(f["mystery"].tags)
    out = []
    if "swarm" in tags:
        out.append(QAItem(question="What is a swarm?", answer="A swarm is a lot of small things moving together at once. It can seem noisy, busy, or hard to control."))
    if "mystery" in tags:
        out.append(QAItem(question="What is a mystery?", answer="A mystery is something puzzling that does not make sense right away. People solve it by finding clues and putting the clues together."))
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="tower", mystery="note", swarm="robot_bees", response="vacuum", hero="Nova", hero_gender="girl", executive="Ms. Ledger", executive_gender="woman", sidekick="Pip", sidekick_gender="boy", hero_trait="bright"),
    StoryParams(setting="museum", mystery="cap", swarm="paper_moths", response="net", hero="Comet", hero_gender="boy", executive="Mr. Brisk", executive_gender="man", sidekick="June", sidekick_gender="girl", hero_trait="curious"),
    StoryParams(setting="lab", mystery="stamp", swarm="micro_drones", response="fan", hero="Spark", hero_gender="girl", executive="Dr. Quartz", executive_gender="woman", sidekick="Rin", sidekick_gender="boy", hero_trait="inventive"),
]


ASP_RULES = r"""
valid(S, M, W, R) :- setting(S), mystery(M), swarm(W), response(R), sense(R, X), sense_min(N), X >= N.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for w in SWARMS:
        lines.append(asp.fact("swarm", w))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid-combos disagree.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, swarm=None, response=None, hero=None, hero_gender=None, executive=None, executive_gender=None, sidekick=None, sidekick_gender=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify smoke test passed.")
    return rc


def build_parser_show_asp() -> str:
    return asp_program("#show valid/4.")


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
        print(build_parser_show_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, swarm, response) combos:\n")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[tuple[str, str]]:
    return [(item.question, item.answer) for item in [QAItem(question=q, answer=a) for q, a in story_qa(world)]]
