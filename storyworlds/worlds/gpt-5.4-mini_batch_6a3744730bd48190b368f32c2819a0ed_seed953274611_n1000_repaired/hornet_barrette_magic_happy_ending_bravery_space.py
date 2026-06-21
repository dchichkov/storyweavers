#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hornet_barrette_magic_happy_ending_bravery_space.py
====================================================================================

A small, self-contained storyworld about a space adventure in which a child
finds a hornet in a floating garden pod, gets scared, uses a magical barrette
as a brave little tool, and ends with a happy, safe image.

This world keeps the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not a frozen paragraph template
- a reasonableness gate and inline ASP twin
- three QA sets generated from the simulated world state
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
BRAVERY_MIN = 1.0
MAGIC_MIN = 1.0
SPACE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class Beacon:
    id: str
    label: str
    kind: str
    prompt: str
    scene: str
    location: str
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
class Hazard:
    id: str
    label: str
    scene: str
    danger: str
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
class MagicTool:
    id: str
    label: str
    phrase: str
    glow: str
    power: int
    sense: int
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
class Rescue:
    id: str
    label: str
    action: str
    success: str
    fail: str
    qa: str
    power: int
    sense: int
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
    beacon: str
    hazard: str
    magic: str
    rescue: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None
    bravery: int = 2
    delay: int = 0
    relation: str = "friends"
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


SETTINGS = {
    "orbital_garden": "a small orbital garden with glass walls and silver vines",
    "moon_bay": "a moon bay with pale rocks and a low blue sky",
    "starship_hall": "a starship hall with bright panels and humming doors",
}

BEACONS = {
    "signal_chime": Beacon(
        id="signal_chime",
        label="a blinking signal chime",
        kind="light",
        prompt="twinkled softly",
        scene="the control nook",
        location="on a shelf",
        tags={"light", "space"},
    ),
    "comet_glass": Beacon(
        id="comet_glass",
        label="a comet glass globe",
        kind="light",
        prompt="shone like a tiny star",
        scene="the garden walkway",
        location="by the door",
        tags={"light", "space"},
    ),
}

HAZARDS = {
    "hornet": Hazard(
        id="hornet",
        label="a hornet",
        scene="inside the garden pod",
        danger="it could sting and make everyone rush away",
        tags={"hornet", "sting"},
    ),
}

MAGICS = {
    "barrette": MagicTool(
        id="barrette",
        label="a glittering barrette",
        phrase="a glittering barrette",
        glow="sparkled with soft blue light",
        power=1,
        sense=2,
        tags={"magic", "barrette"},
    ),
}

RESCUES = {
    "gentle_shield": Rescue(
        id="gentle_shield",
        label="a gentle shield spell",
        action="raised the barrette and whispered a tiny spell",
        success="made a soft magic bubble that nudged the hornet back outside",
        fail="made only a weak shimmer, and the hornet kept buzzing too close",
        qa="used the barrette to make a little shield of light",
        power=2,
        sense=2,
        tags={"magic", "shield"},
    ),
    "star_window": Rescue(
        id="star_window",
        label="an opening star window",
        action="opened the window and waved calmly",
        success="opened the window wide and guided the hornet out toward the stars",
        fail="opened the window, but the hornet stayed inside and kept circling",
        qa="opened the window and guided the hornet outside",
        power=1,
        sense=1,
        tags={"window"},
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Zoe", "Ava", "Nia", "Iris"]
BOY_NAMES = ["Noel", "Kai", "Milo", "Theo", "Leo", "Oren"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for beacon in BEACONS:
            for hazard in HAZARDS:
                if hazard == "hornet":
                    for magic in MAGICS:
                        for rescue in RESCUES:
                            if MAGICS[magic].sense >= MAGIC_MIN and RESCUES[rescue].sense >= BRAVERY_MIN:
                                combos.append((setting, beacon, hazard))
    return combos


def hazard_reasonable(hazard: Hazard) -> bool:
    return hazard.id == "hornet"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.hazard not in HAZARDS:
        raise StoryError("Unknown hazard.")
    if args.magic and MAGICS[args.magic].sense < MAGIC_MIN:
        raise StoryError("That magic is too weak for this world.")
    if args.rescue and RESCUES[args.rescue].sense < BRAVERY_MIN:
        raise StoryError("That rescue is too weak for this world.")
    if args.hazard and not hazard_reasonable(HAZARDS[args.hazard]):
        raise StoryError("That hazard does not fit the storyworld.")

    setting = args.setting or rng.choice(list(SETTINGS))
    beacon = args.beacon or rng.choice(list(BEACONS))
    hazard = args.hazard or "hornet"
    magic = args.magic or rng.choice(list(MAGICS))
    rescue = args.rescue or rng.choice(list(RESCUES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    helper_pool = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(hero_pool)
    helper = args.helper or rng.choice([n for n in helper_pool if n != hero] or helper_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    bravery = args.bravery if args.bravery is not None else rng.randint(1, 4)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = args.relation or rng.choice(["friends", "siblings"])
    return StoryParams(
        setting=setting,
        beacon=beacon,
        hazard=hazard,
        magic=magic,
        rescue=rescue,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        bravery=bravery,
        delay=delay,
        relation=relation,
    )


def _r_danger(world: World) -> list[str]:
    out = []
    h = world.get("hazard")
    if h.meters["buzzing"] >= THRESHOLD and ("danger", h.id) not in world.fired:
        world.fired.add(("danger", h.id))
        world.get("hero").memes["fear"] += 1
        world.get("helper").memes["fear"] += 1
        out.append("__danger__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in [_r_danger]:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("hazard").meters["buzzing"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("hero").memes["fear"],
        "buzzing": sim.get("hazard").meters["buzzing"],
    }


def tell(setting: str, beacon: Beacon, hazard: Hazard, magic: MagicTool, rescue: Rescue,
         hero: str, hero_gender: str, helper: str, helper_gender: str, parent: str,
         bravery: int, delay: int, relation: str) -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    k = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper"))
    p = world.add(Entity(id=parent, kind="character", type="mother" if parent == "mother" else "father", role="parent", label=f"the {parent}"))
    hz = world.add(Entity(id="hazard", type="hazard", label=hazard.label, role="hazard", tags=set(hazard.tags)))
    bg = world.add(Entity(id="beacon", type="beacon", label=beacon.label, role="beacon", tags=set(beacon.tags)))
    tl = world.add(Entity(id="magic", type="tool", label=magic.label, role="tool", tags=set(magic.tags)))

    h.memes["bravery"] = float(bravery)
    k.memes["bravery"] = 1.0
    world.facts.update(setting=setting, beacon=beacon, hazard=hazard, magic=magic,
                       rescue=rescue, hero=h, helper=k, parent=p, delay=delay,
                       relation=relation, setting_text=SETTINGS[setting])

    world.say(f"{h.id} and {k.id} drifted through {SETTINGS[setting]}.")
    world.say(f"Near {beacon.location}, {beacon.label} {beacon.prompt}.")
    world.say(f"Then {h.id} spotted {hazard.label} in {hazard.scene}, and {hazard.danger}.")

    world.para()
    h.memes["curiosity"] += 1
    k.memes["caution"] += 1
    world.say(f"{k.id} gasped, but {h.id}'s {magic.label} {magic.glow}.")
    world.say(f'"That is not scary," {h.id} said, even though {h.pronoun()} felt small.')

    if delay > 0:
        hz.meters["buzzing"] += 1
        propagate(world, narrate=False)

    if bravery <= 1:
        world.say(f"{h.id} took a breath, stepped back, and called for a grown-up.")
        world.para()
        world.say(f"{p.label.capitalize()} came quickly, and the hornet floated out through the open air vent.")
        world.say(f"Afterward, {h.id} held {tl.label} like a charm and smiled at the safe, quiet pod.")
        outcome = "averted"
        rescued = True
    else:
        world.say(f"{h.id} lifted {magic.label} and chose to be brave.")
        world.say(f"{k.id} stood beside {h.id} like a second star.")
        world.para()
        if rescue.power >= 2:
            world.say(f"{p.label.capitalize()} {rescue.action}, and {rescue.success}.")
            world.say("The hornet flew out toward the dark window, and the room became calm again.")
            world.para()
            world.say(f"Then everyone laughed softly, and {h.id} tucked {bg.label} back on the shelf.")
            world.say(f"Their little space adventure ended with a happy ending, bright as moonlight.")
            outcome = "contained"
            rescued = True
        else:
            world.say(f"{p.label.capitalize()} tried to help, but {rescue.fail}.")
            world.say(f"The hornet circled once more, and everyone had to hurry to the hall.")
            world.say(f"Still, {h.id} kept {magic.label} tight and did not cry.")
            world.say("That brave pause gave the grown-up enough time to guide the hornet away.")
            outcome = "contained"
            rescued = True

    world.facts["outcome"] = outcome
    world.facts["rescued"] = rescued
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a 3-to-5-year-old that includes the words "{f["hazard"].id}" and "{f["magic"].id}".',
        f"Tell a gentle story where {f['hero'].id} uses {f['magic'].label} bravely when a hornet appears in a space garden.",
        f"Write a happy ending story about courage, magic, and a tiny hornet in a moonlit room.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    hazard: Hazard = f["hazard"]
    magic: MagicTool = f["magic"]
    rescue: Rescue = f["rescue"]
    qa = [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {hero.id} and {helper.id}, who were exploring a space place together. The hornet made the moment scary, but the story stayed gentle and brave.",
        ),
        QAItem(
            question="What made the children scared?",
            answer=f"A hornet appeared in the garden pod. It was scary because it could sting and make everyone rush away.",
        ),
        QAItem(
            question=f"What did {hero.id} use to be brave?",
            answer=f"{hero.id} used {magic.label}. It {magic.glow}, and that helped turn fear into courage.",
        ),
    ]
    if world.facts["outcome"] == "contained":
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended happily. The grown-up helped, the hornet went outside, and {hero.id} smiled in the calm light afterward.",
            )
        )
        qa.append(
            QAItem(
                question=f"What did the grown-up do to help?",
                answer=f"{parent.label.capitalize()} {rescue.qa}. That let the hornet leave safely and kept the ending happy.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did bravery help?",
                answer=f"{hero.id} did not run away in panic. {hero.pronoun().capitalize()} stayed steady long enough to call for help, and that made the danger pass.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hornet?",
            answer="A hornet is a kind of flying insect. It can sting, so people should stay calm and get help if one is close.",
        ),
        QAItem(
            question="What is a barrette?",
            answer="A barrette is a small clip that holds hair in place. In a magic story, it can also shine like a tiny charm.",
        ),
        QAItem(
            question="Why is bravery important?",
            answer="Bravery helps someone do the right thing even when they feel scared. A brave person can stop, think, and ask for help.",
        ),
        QAItem(
            question="What makes the story magical?",
            answer="The glittering barrette makes the story magical because it glows like a charm and helps with a tiny spell.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(H) :- hazard_fact(H).
magic(M) :- magic_fact(M), magic_sense(M,S), S >= magic_min.
rescue(R) :- rescue_fact(R), rescue_sense(R,S), S >= rescue_min.
valid(S,B,H) :- setting(S), beacon(B), hazard_fact(H).
outcome(contained) :- chosen_rescue(R), rescue_power(R,P), P >= 2.
outcome(averted) :- bravery(B), B < 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BEACONS:
        lines.append(asp.fact("beacon", bid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard_fact", hid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic_fact", mid))
        lines.append(asp.fact("magic_sense", mid, m.sense))
    for rid, r in RESCUES.items():
        lines.append(asp.fact("rescue_fact", rid))
        lines.append(asp.fact("rescue_sense", rid, r.sense))
        lines.append(asp.fact("rescue_power", rid, r.power))
    lines.append(asp.fact("magic_min", MAGIC_MIN))
    lines.append(asp.fact("rescue_min", BRAVERY_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        p = StoryParams(
            setting="orbital_garden",
            beacon="signal_chime",
            hazard="hornet",
            magic="barrette",
            rescue="gentle_shield",
            hero="Luna",
            hero_gender="girl",
            helper="Kai",
            helper_gender="boy",
            parent="mother",
        )
        sample = generate(p)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    if rc == 0:
        print("OK: ASP parity and generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with hornet, barrette, magic, bravery, and a happy ending.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--beacon", choices=list(BEACONS))
    ap.add_argument("--hazard", choices=list(HAZARDS))
    ap.add_argument("--magic", choices=list(MAGICS))
    ap.add_argument("--rescue", choices=list(RESCUES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--bravery", type=int)
    ap.add_argument("--delay", type=int)
    ap.add_argument("--relation", choices=["friends", "siblings"])
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.beacon not in BEACONS:
        raise StoryError("Unknown beacon.")
    if params.hazard not in HAZARDS:
        raise StoryError("Unknown hazard.")
    if params.magic not in MAGICS:
        raise StoryError("Unknown magic.")
    if params.rescue not in RESCUES:
        raise StoryError("Unknown rescue.")

    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent, role="parent", label=f"the {params.parent}"))
    beacon = BEACONS[params.beacon]
    hazard = HAZARDS[params.hazard]
    magic = MAGICS[params.magic]
    rescue = RESCUES[params.rescue]
    hz = world.add(Entity(id="hazard", type="hazard", label=hazard.label, role="hazard", tags=set(hazard.tags)))
    mg = world.add(Entity(id="magic", type="tool", label=magic.label, role="tool", tags=set(magic.tags)))
    bg = world.add(Entity(id="beacon", type="beacon", label=beacon.label, role="beacon", tags=set(beacon.tags)))

    hero.memes["bravery"] = float(params.bravery)
    helper.memes["bravery"] = 1.0
    world.facts.update(hero=hero, helper=helper, parent=parent, beacon=beacon, hazard=hazard, magic=magic, rescue=rescue, setting=params.setting, outcome="contained")
    story = tell(params.setting, beacon, hazard, magic, rescue, params.hero, params.hero_gender, params.helper, params.helper_gender, params.parent, params.bravery, params.delay, params.relation)
    return StorySample(
        params=params,
        story=story.render(),
        prompts=generation_prompts(story),
        story_qa=story_qa(story),
        world_qa=world_knowledge_qa(story),
        world=story,
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


def resolve_seeded_choice(rng: random.Random, items: list[str]) -> str:
    return rng.choice(items)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.hazard not in HAZARDS:
        raise StoryError("Unknown hazard.")
    setting = args.setting or resolve_seeded_choice(rng, list(SETTINGS))
    beacon = args.beacon or resolve_seeded_choice(rng, list(BEACONS))
    hazard = args.hazard or "hornet"
    magic = args.magic or resolve_seeded_choice(rng, list(MAGICS))
    rescue = args.rescue or resolve_seeded_choice(rng, list(RESCUES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_pool = GIRL_NAMES if helper_gender == "girl" else BOY_NAMES
    helper = args.helper or rng.choice([n for n in helper_pool if n != hero] or helper_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    bravery = args.bravery if args.bravery is not None else rng.randint(1, 3)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = args.relation or "friends"
    return StoryParams(
        setting=setting,
        beacon=beacon,
        hazard=hazard,
        magic=magic,
        rescue=rescue,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        bravery=bravery,
        delay=delay,
        relation=relation,
    )


CURATED = [
    StoryParams(setting="orbital_garden", beacon="signal_chime", hazard="hornet", magic="barrette", rescue="gentle_shield", hero="Luna", hero_gender="girl", helper="Kai", helper_gender="boy", parent="mother", bravery=2, delay=0, relation="friends"),
    StoryParams(setting="moon_bay", beacon="comet_glass", hazard="hornet", magic="barrette", rescue="star_window", hero="Mira", hero_gender="girl", helper="Noel", helper_gender="boy", parent="father", bravery=1, delay=0, relation="siblings"),
]


def asp_outcome(params: StoryParams) -> str:
    return "contained" if RESCUES[params.rescue].power >= 2 else "averted" if params.bravery < 2 else "contained"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i),)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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


if __name__ == "__main__":
    main()
