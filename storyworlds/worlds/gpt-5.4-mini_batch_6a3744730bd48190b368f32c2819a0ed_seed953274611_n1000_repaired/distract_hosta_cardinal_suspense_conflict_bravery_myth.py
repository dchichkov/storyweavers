#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distract_hosta_cardinal_suspense_conflict_bravery_myth.py
=========================================================================================

A standalone storyworld about a small mythic garden: a child, a restless
cardinal, a hosta patch, a tempting distraction, a tense conflict, and a brave
choice that restores calm.

The story engine is state-driven. Characters and objects carry physical meters
and emotional memes; the prose is rendered from the evolving world model rather
than from a frozen template. The world is intentionally small, with a single
premise and a few constraint-checked variants:

- a proud child spots a cardinal near a cherished hosta;
- the child is tempted to distract the bird;
- a careful warning creates suspense and conflict;
- bravery resolves the moment by choosing a gentler action;
- the ending image proves what changed.

The style aims for a mythic, child-facing cadence: simple, concrete, and a touch
legend-like, while still grounded in the simulated state.
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
BRAVERY_INIT = 5.0


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
        return self.label or self.id
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
    mood: str
    mythic_phrase: str
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
class CharacterCfg:
    id: str
    type: str
    role: str
    title: str
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
class PlantCfg:
    id: str
    label: str
    kind: str
    vulnerable: bool = True
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
class BirdCfg:
    id: str
    label: str
    song: str
    wary: bool = True
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
class DistractionCfg:
    id: str
    label: str
    lure: str
    decoy: str
    subtle: bool = True
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
class ResponseCfg:
    id: str
    courage: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    setting: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    plant: str
    bird: str
    distract: str
    response: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    h = world.get("hero")
    b = world.get("bird")
    p = world.get("plant")
    if h.memes["worry"] >= THRESHOLD and b.meters["near"] >= THRESHOLD:
        sig = ("suspense",)
        if sig not in world.fired:
            world.fired.add(sig)
            h.memes["suspense"] += 1
            out.append(f"The garden held its breath beside the {p.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    h = world.get("hero")
    h.memes["defiance"] += 1 if h.memes["tempted"] >= THRESHOLD else 0
    if h.memes["defiance"] >= THRESHOLD and h.memes["care"] < THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            h.memes["conflict"] += 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_of_distraction(distraction: DistractionCfg, plant: PlantCfg, bird: BirdCfg) -> bool:
    return distraction.subtle and plant.vulnerable and bird.wary


def sensible_responses() -> list[ResponseCfg]:
    return [r for r in RESPONSES.values() if r.courage >= 2]


def is_brave(response: ResponseCfg) -> bool:
    return response.courage >= 2


def quiet_warning(world: World, helper: Entity, hero: Entity, plant: PlantCfg, bird: BirdCfg) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} touched {hero.id}\'s sleeve and whispered, '
        f'"Not here. The {bird.label} startles easily, and the {plant.label} must not be trampled."'
    )
    world.say("For a moment, the bright path of play grew narrow and still.")


def tempt(world: World, hero: Entity, distraction: DistractionCfg, bird: BirdCfg) -> None:
    hero.memes["tempted"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'{hero.id} looked at the {bird.label} and thought of a trick. '
        f'"I could {distraction.label}," {hero.pronoun()} said, and the idea glittered like a dare.'
    )


def crossroad(world: World, hero: Entity, helper: Entity, plant: PlantCfg, bird: BirdCfg) -> None:
    world.say(
        f'Then the {bird.label} hopped close to the {plant.label}, and the air went still. '
        f'{helper.id} stared at the bird, then at {hero.pronoun("object")}, waiting.'
    )


def choose_brave(world: World, hero: Entity, helper: Entity, response: ResponseCfg, bird: BirdCfg) -> None:
    hero.memes["bravery"] += 1
    hero.memes["worry"] = 0.0
    helper.memes["relief"] += 1
    world.say(
        f'{hero.id} drew one brave breath and chose a kinder way. '
        f'{hero.pronoun().capitalize()} {response.text}.'
    )
    world.say(
        f'The {bird.label} settled its feathers and sang once more, because the threat was gone.'
    )


def fail_choice(world: World, hero: Entity, helper: Entity, response: ResponseCfg, bird: BirdCfg) -> None:
    world.say(
        f'{hero.id} tried anyway, but the moment slipped away. {response.fail}. '
        f'The {bird.label} flapped off in a rush of leaves.'
    )
    helper.memes["sadness"] += 1


def ending_image(world: World, hero: Entity, helper: Entity, plant: PlantCfg, bird: BirdCfg) -> None:
    world.say(
        f'By sunset, the {plant.label} still stood green and whole, and the {bird.label} '
        f'was back on its branch. {hero.id} and {helper.id} stood beneath it, '
        f'braver for having chosen well.'
    )


def tell(setting: Setting, hero_cfg: CharacterCfg, helper_cfg: CharacterCfg,
         plant: PlantCfg, bird: BirdCfg, distraction: DistractionCfg,
         response: ResponseCfg) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg.type, label=hero_cfg.id, role=hero_cfg.role))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.type, label=helper_cfg.id, role=helper_cfg.role))
    plant_ent = world.add(Entity(id="plant", type="plant", label=plant.label))
    bird_ent = world.add(Entity(id="bird", type="bird", label=bird.label))

    hero.memes["bravery"] = BRAVERY_INIT
    world.say(
        f"Long ago, in {setting.place}, the {setting.mythic_phrase}. "
        f"{hero_cfg.id} and {helper_cfg.id} came walking through the quiet green."
    )
    world.say(
        f"They found a {plant.label} shining like a little shield, while a {bird.label} "
        f"flashed red above it."
    )

    world.para()
    tempt(world, hero, distraction, bird)
    quiet_warning(world, helper, hero, plant, bird)
    crossroad(world, hero, helper, plant, bird)

    if response.courage >= 2:
        if risk_of_distraction(distraction, plant, bird):
            hero.memes["conflict"] += 1
        choose_brave(world, hero, helper, response, bird)
    else:
        fail_choice(world, hero, helper, response, bird)

    world.para()
    ending_image(world, hero, helper, plant, bird)

    world.facts.update(
        hero=hero, helper=helper, plant=plant, bird=bird, distraction=distraction,
        response=response, setting=setting, outcome="brave" if response.courage >= 2 else "failed"
    )
    return world


SETTINGS = {
    "myth": Setting(
        id="myth",
        place="an old temple garden",
        mood="still",
        mythic_phrase="the stones remembered every footstep",
    ),
    "grove": Setting(
        id="grove",
        place="a moonlit grove",
        mood="hushed",
        mythic_phrase="the trees kept secrets in their leaves",
    ),
    "courtyard": Setting(
        id="courtyard",
        place="a sunlit courtyard",
        mood="bright",
        mythic_phrase="the fountains sang softly at the center",
    ),
}

HEROES = {
    "child": CharacterCfg(id="Ari", type="boy", role="hero", title="young seeker"),
    "girl": CharacterCfg(id="Mina", type="girl", role="hero", title="young watcher"),
}
HELPERS = {
    "elder": CharacterCfg(id="Nia", type="girl", role="helper", title="wise guide"),
    "brother": CharacterCfg(id="Joren", type="boy", role="helper", title="older brother"),
}
PLANTS = {
    "hosta": PlantCfg(id="hosta", label="hosta", kind="plant", vulnerable=True),
    "big_hosta": PlantCfg(id="big_hosta", label="big hosta", kind="plant", vulnerable=True),
}
BIRDS = {
    "cardinal": BirdCfg(id="cardinal", label="cardinal", song="bright song", wary=True),
    "young_cardinal": BirdCfg(id="young_cardinal", label="cardinal", song="quick chirp", wary=True),
}
DISTRACTIONS = {
    "call": DistractionCfg(id="call", label="call out to distract the cardinal", lure="a loud call", decoy="noise", subtle=True),
    "wave": DistractionCfg(id="wave", label="wave a sleeve to distract the cardinal", lure="a sweeping wave", decoy="motion", subtle=True),
}
RESPONSES = {
    "gentle_step": ResponseCfg(
        id="gentle_step",
        courage=3,
        power=3,
        text="stepped back, lifted a hand in greeting, and let the cardinal choose its own path",
        fail="the attempt only stirred the leaves and made the moment worse",
        qa_text="stepped back and let the cardinal choose its own path",
    ),
    "shield_plant": ResponseCfg(
        id="shield_plant",
        courage=2,
        power=2,
        text="moved around the hosta without touching it, guarding it like a tiny altar",
        fail="the plan shook and fell apart in a flurry of leaves",
        qa_text="moved around the hosta without touching it",
    ),
    "wait": ResponseCfg(
        id="wait",
        courage=2,
        power=2,
        text="waited still as stone until the cardinal hopped away on its own",
        fail="waiting turned to fussing, and the bird fled before peace came",
        qa_text="waited still until the cardinal hopped away",
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid in HEROES:
            for helper_id in HELPERS:
                if hid == helper_id:
                    continue
                for pid, plant in PLANTS.items():
                    for bid, bird in BIRDS.items():
                        for did, dist in DISTRACTIONS.items():
                            for rid, resp in RESPONSES.items():
                                if risk_of_distraction(dist, plant, bird) and is_brave(resp):
                                    combos.append((sid, hid, pid, bid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic garden storyworld with suspense, conflict, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--distract", choices=DISTRACTIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not is_brave(RESPONSES[args.response]):
        raise StoryError("(No story: the chosen response is too timid for this mythic conflict.)")
    settings = list(SETTINGS)
    heroes = list(HEROES)
    helpers = [k for k in HELPERS if k != args.hero]
    plants = list(PLANTS)
    birds = list(BIRDS)
    distracts = list(DISTRACTIONS)
    responses = [k for k, r in RESPONSES.items() if is_brave(r)]

    if args.setting:
        settings = [args.setting]
    if args.hero:
        heroes = [args.hero]
    if args.helper:
        helpers = [args.helper]
    if args.plant:
        plants = [args.plant]
    if args.bird:
        birds = [args.bird]
    if args.distract:
        distracts = [args.distract]
    if args.response:
        responses = [args.response]

    candidates = []
    for sid in settings:
        for hid in heroes:
            for helper_id in helpers:
                if hid == helper_id:
                    continue
                for pid in plants:
                    for bid in birds:
                        for did in distracts:
                            if risk_of_distraction(DISTRACTIONS[did], PLANTS[pid], BIRDS[bid]):
                                for rid in responses:
                                    candidates.append((sid, hid, helper_id, pid, bid, did, rid))
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")
    sid, hid, helper_id, pid, bid, did, rid = rng.choice(sorted(candidates))
    return StoryParams(
        setting=sid,
        hero=HEROES[hid].id,
        hero_type=HEROES[hid].type,
        helper=HELPERS[helper_id].id,
        helper_type=HELPERS[helper_id].type,
        plant=pid,
        bird=bid,
        distract=did,
        response=rid,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic children\'s story that includes the words "distract", "{f["plant"].label}", and "{f["bird"].label}".',
        f"Tell a suspenseful garden myth where {f['hero'].label_word} nearly tries to distract a {f['bird'].label}, but chooses bravery instead.",
        f"Write a short story with conflict and bravery in an old garden, ending with the {f['plant'].label} still safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    plant = f["plant"]
    bird = f["bird"]
    response = f["response"]
    return [
        QAItem(
            question="What made the moment suspenseful?",
            answer=(
                f"The {bird.label} was close to the {plant.label}, and {hero.id} was tempted to distract it. "
                f"That made everyone pause and watch carefully, because one wrong move could have ruined the quiet garden."
            ),
        ),
        QAItem(
            question="Why was there conflict?",
            answer=(
                f"{hero.id} wanted to act at once, but {helper.id} warned them to be careful. "
                f"The hero had to choose between a risky trick and a gentler path."
            ),
        ),
        QAItem(
            question="How did bravery change the story?",
            answer=(
                f"Bravery let {hero.id} choose {response.qa_text} instead of causing trouble. "
                f"That choice protected the {plant.label} and gave the {bird.label} room to stay calm."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cardinal?",
            answer=(
                "A cardinal is a small bird with a bright red body and a lively song. "
                "It is quick to notice movement and can be startled by sudden action."
            ),
        ),
        QAItem(
            question="What is hosta?",
            answer=(
                "A hosta is a garden plant with broad leaves. It stays rooted in one place and can be harmed if someone steps on it."
            ),
        ),
        QAItem(
            question="What does it mean to distract someone?",
            answer=(
                "To distract means to pull attention away from what someone was doing or watching. "
                "It can be useful, but it can also be careless if it causes harm."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,H,P,B) :- setting(S), hero(H), plant(P), bird(B), risk(P,B).
risk(P,B) :- plant(P), bird(B).
brave(R) :- response(R), courage(R,C), C >= 2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for pid in PLANTS:
        lines.append(asp.fact("plant", pid))
    for bid in BIRDS:
        lines.append(asp.fact("bird", bid))
    for did in DISTRACTIONS:
        lines.append(asp.fact("distract", did))
        lines.append(asp.fact("risk", did))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("courage", rid, resp.courage))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if py - cl:
            print(" only in python:", sorted(py - cl))
        if cl - py:
            print(" only in asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.hero_type not in {"boy", "girl"}:
        raise StoryError("Unknown hero type.")
    if params.helper_type not in {"boy", "girl"}:
        raise StoryError("Unknown helper type.")
    if params.plant not in PLANTS or params.bird not in BIRDS or params.distract not in DISTRACTIONS or params.response not in RESPONSES:
        raise StoryError("Unknown world parameter.")
    if not risk_of_distraction(DISTRACTIONS[params.distract], PLANTS[params.plant], BIRDS[params.bird]):
        raise StoryError("This distraction is not risky enough for a story.")
    if not is_brave(RESPONSES[params.response]):
        raise StoryError("This response is too timid for the storyworld.")
    world = tell(
        SETTINGS[params.setting],
        HEROES["child"] if params.hero == HEROES["child"].id else HEROES["girl"],
        HELPERS["elder"] if params.helper == HELPERS["elder"].id else HELPERS["brother"],
        PLANTS[params.plant],
        BIRDS[params.bird],
        DISTRACTIONS[params.distract],
        RESPONSES[params.response],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(setting="myth", hero="Ari", hero_type="boy", helper="Nia", helper_type="girl", plant="hosta", bird="cardinal", distract="call", response="gentle_step"),
    StoryParams(setting="grove", hero="Mina", hero_type="girl", helper="Joren", helper_type="boy", plant="big_hosta", bird="young_cardinal", distract="wave", response="shield_plant"),
    StoryParams(setting="courtyard", hero="Ari", hero_type="boy", helper="Nia", helper_type="girl", plant="hosta", bird="cardinal", distract="call", response="wait"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    settings = [args.setting] if args.setting else list(SETTINGS)
    heroes = [args.hero] if args.hero else list(HEROES)
    helpers = [args.helper] if args.helper else list(HELPERS)
    plants = [args.plant] if args.plant else list(PLANTS)
    birds = [args.bird] if args.bird else list(BIRDS)
    distracts = [args.distract] if args.distract else list(DISTRACTIONS)
    responses = [args.response] if args.response else [k for k, v in RESPONSES.items() if is_brave(v)]
    candidates = []
    for sid in settings:
        for hid in heroes:
            for hid2 in helpers:
                if hid == hid2:
                    continue
                for pid in plants:
                    for bid in birds:
                        for did in distracts:
                            if not risk_of_distraction(DISTRACTIONS[did], PLANTS[pid], BIRDS[bid]):
                                continue
                            for rid in responses:
                                candidates.append((sid, hid, hid2, pid, bid, did, rid))
    if not candidates:
        raise StoryError("(No valid combination matches the given options.)")
    sid, hid, hid2, pid, bid, did, rid = rng.choice(sorted(candidates))
    return StoryParams(
        setting=sid,
        hero=HEROES[hid].id,
        hero_type=HEROES[hid].type,
        helper=HELPERS[hid2].id,
        helper_type=HELPERS[hid2].type,
        plant=pid,
        bird=bid,
        distract=did,
        response=rid,
    )


def build_sample_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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


if __name__ == "__main__":
    main()
