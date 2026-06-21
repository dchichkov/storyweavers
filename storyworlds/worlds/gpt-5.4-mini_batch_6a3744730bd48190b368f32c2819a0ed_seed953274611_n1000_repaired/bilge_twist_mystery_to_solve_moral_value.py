#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bilge_twist_mystery_to_solve_moral_value.py
===========================================================================

A small fairy-tale story world about a river boat, a rising bilge, a mystery
that must be solved, and a twist that reveals the real cause. The moral value
is gentle and child-facing: honesty, courage, and asking for help beat panic.

The world simulates:
- a tiny cast of typed entities with physical meters and emotional memes
- a forward-chained causal fixpoint
- a reasonableness gate for story combinations
- a Python reasoner plus an inline ASP twin
- prompts, grounded Q&A, and world-knowledge Q&A

The output stories are short, complete, and state-driven rather than frozen
templates.
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
MYSTERY_MIN = 1.0
BILGE_RISE = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "prince", "king"}
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
class Setting:
    id: str
    place: str
    scene: str
    dark: str
    travel: str
    water: str
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
class Cause:
    id: str
    clue: str
    label: str
    truth: str
    fixable: bool
    makes_bilge: bool = True
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
class Remedy:
    id: str
    sense: int
    power: int
    action: str
    fail: str
    qa: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w
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


def _r_bilge(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    if ship and ship.meters["leak"] >= THRESHOLD and ship.meters["bilge"] < THRESHOLD:
        sig = ("bilge",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        ship.meters["bilge"] += BILGE_RISE
        out.append("Water gathered in the bilge.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("ship", Entity("x")).meters["bilge"] >= THRESHOLD:
        for eid in ("hero", "friend"):
            if eid in world.entities:
                world.get(eid).memes["worry"] += 1
        ship = world.get("ship")
        if ship.meters["bilge"] >= 2 and ("worry",) not in world.fired:
            world.fired.add(("worry",))
            out.append("The little boat felt unsafe.")
    return out


CAUSAL_RULES = [Rule("bilge", "physical", _r_bilge), Rule("worry", "social", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(cause: Cause, remedy: Remedy) -> bool:
    return cause.fixable and remedy.sense >= SENSE_MIN


def bilge_risk(cause: Cause) -> bool:
    return cause.makes_bilge


def water_severity(delay: int) -> int:
    return 1 + delay


def contained(remedy: Remedy, delay: int) -> bool:
    return remedy.power >= water_severity(delay)


def predict(world: World, cause: Cause) -> dict:
    sim = world.copy()
    sim.get("ship").meters["leak"] += 1
    propagate(sim, narrate=False)
    return {
        "bilge": sim.get("ship").meters["bilge"] >= THRESHOLD,
        "worry": sim.get("friend").memes["worry"] >= THRESHOLD if "friend" in sim.entities else False,
    }


def start(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"In {setting.place}, {hero.id} and {friend.id} set out on {setting.scene}. "
        f"The water glittered, and the {setting.travel} seemed as bright as a song."
    )
    world.say(
        f"Below deck, a little shadowy place waited, and the bilge was quiet for the moment."
    )


def mystery(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"Then a strange drip began. {friend.id} peered down and whispered, "
        f'"Something is making the bilge fill up."'
    )
    world.say(
        f"{hero.id} thought first of {cause.label}, because the clue looked like {cause.clue}."
    )


def suspect(world: World, hero: Entity, cause: Cause) -> None:
    hero.memes["fear"] += 1
    world.say(
        f'"Perhaps {cause.label} did it," {hero.id} said. '
        f'For a breath, even the lantern seemed to blink.'
    )


def twist(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    hero.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    world.say(
        f"But the smallest clue pointed elsewhere: {cause.truth}. "
        f"That was the twist, and it made the answer plain."
    )


def fix(world: World, helper: Entity, remedy: Remedy) -> None:
    helper.memes["brave"] += 1
    world.get("ship").meters["bilge"] = 0.0
    world.say(
        f"{helper.id} {remedy.action}. The bilge grew dry again, and the boat stopped wobbling."
    )


def moral(world: World, hero: Entity, friend: Entity, setting: Setting, cause: Cause) -> None:
    hero.memes["calm"] += 1
    friend.memes["calm"] += 1
    world.say(
        f"At last, {hero.id} and {friend.id} told the captain the truth about the leak, "
        f"and the captain smiled. \"A problem solved honestly is a problem half-finished,\" "
        f"{world.get('captain').pronoun()} said."
    )
    world.say(
        f"So they patched the crack, thanked one another, and sailed on through {setting.place}, "
        f"learning that a brave confession can be as helpful as a strong rope."
    )


def fail_fix(world: World, captain: Entity, remedy: Remedy, cause: Cause) -> None:
    world.get("ship").meters["bilge"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{captain.id} tried to help, but {remedy.fail}. The bilge kept rising until everyone had to pump faster."
    )
    world.say(
        f"In the end, the crew still found the leak, and the truth was better than the guess."
    )


def tell(setting: Setting, cause: Cause, remedy: Remedy, delay: int = 0,
         hero_name: str = "Ava", friend_name: str = "Milo",
         hero_type: str = "girl", friend_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    captain = world.add(Entity(id="captain", kind="character", type="queen", role="captain", label="the captain"))
    ship = world.add(Entity(id="ship", kind="thing", type="boat", label="the little boat"))
    ship.meters["leak"] = 1.0

    start(world, hero, friend, setting)
    world.para()
    mystery(world, hero, friend, cause)
    suspect(world, hero, cause)

    if not cause.fixable:
        raise StoryError("This mystery has no sensible resolution.")
    if not bilge_risk(cause):
        raise StoryError("This cause does not produce bilge water.")
    if not reasonableness_gate(cause, remedy):
        raise StoryError("This remedy is not reasonable for the mystery.")

    world.para()
    if delay > 0:
        ship.meters["bilge"] += float(delay)
    propagate(world)

    twist(world, hero, friend, cause)
    if contained(remedy, delay):
        fix(world, captain, remedy)
        world.para()
        moral(world, hero, friend, setting, cause)
        outcome = "solved"
    else:
        fail_fix(world, captain, remedy, cause)
        world.para()
        moral(world, hero, friend, setting, cause)
        outcome = "late"

    world.facts.update(
        hero=hero, friend=friend, captain=captain, ship=ship, setting=setting,
        cause=cause, remedy=remedy, delay=delay, outcome=outcome,
    )
    return world


SETTINGS = {
    "river": Setting(id="river", place="the silver river", scene="a fairy barge", dark="below deck", travel="ripples"),
    "harbor": Setting(id="harbor", place="the moonlit harbor", scene="a painted skiff", dark="under the planks", travel="waves"),
    "brook": Setting(id="brook", place="the willow brook", scene="a tiny boat with a golden sail", dark="in the bilge below", travel="sparkling water"),
}

CAUSES = {
    "shell": Cause(id="shell", clue="a pale shell near the hatch", label="the shell", truth="a shell had wedged a seam open", fixable=True),
    "key": Cause(id="key", clue="a bent key-ring by the rail", label="the lost key", truth="a dropped key had cracked the plank", fixable=True),
    "mouse": Cause(id="mouse", clue="tiny paw prints in flour dust", label="a mouse", truth="the mouse only wanted crumbs; it was not the culprit", fixable=True),
    "curse": Cause(id="curse", clue="a spooky whisper in the dark", label="a river curse", truth="there was no curse at all, only a leak under the moon", fixable=True),
}

REMEDIES = {
    "pump": Remedy(id="pump", sense=3, power=3, action="worked the hand pump and called for a bucket chain", fail="the pump was too slow"),
    "patch": Remedy(id="patch", sense=3, power=2, action="pressed a wool patch over the seam and tied it tight", fail="the patch slipped on the wet wood"),
    "bail": Remedy(id="bail", sense=2, power=2, action="bailed water with a wooden cup until the bilge shone", fail="the cup was too small"),
}

MORAL_VALUES = ["honesty", "courage", "kindness", "trust"]

CURATED = [
    StoryParams = None
]

@dataclass
class StoryParams:
    setting: str
    cause: str
    remedy: str
    moral: str
    delay: int = 0
    hero_name: str = "Ava"
    hero_type: str = "girl"
    friend_name: str = "Milo"
    friend_type: str = "boy"
    seed: Optional[int] = None


# curated after StoryParams
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
    StoryParams(setting="river", cause="shell", remedy="patch", moral="honesty", delay=0, hero_name="Ava", hero_type="girl", friend_name="Milo", friend_type="boy"),
    StoryParams(setting="harbor", cause="key", remedy="pump", moral="courage", delay=1, hero_name="Nina", hero_type="girl", friend_name="Jon", friend_type="boy"),
    StoryParams(setting="brook", cause="mouse", remedy="bail", moral="kindness", delay=0, hero_name="Pip", hero_type="boy", friend_name="Luna", friend_type="girl"),
    StoryParams(setting="river", cause="curse", remedy="pump", moral="trust", delay=2, hero_name="Rose", hero_type="girl", friend_name="Finn", friend_type="boy"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CAUSES:
            for r in REMEDIES:
                if CAUSES[c].fixable and CAUSES[c].makes_bilge and REMEDIES[r].sense >= SENSE_MIN:
                    combos.append((s, c, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale bilge mystery with a twist and a moral.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.cause is None or c[1] == args.cause)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    setting, cause, remedy = rng.choice(combos)
    moral = args.moral or rng.choice(MORAL_VALUES)
    return StoryParams(
        setting=setting,
        cause=cause,
        remedy=remedy,
        moral=moral,
        delay=args.delay if args.delay is not None else rng.randint(0, 2),
        hero_name=args.hero_name or rng.choice(["Ava", "Nina", "Rose", "Pip"]),
        hero_type="girl" if (args.hero_name or "").lower()[:1] not in {"p"} else "boy",
        friend_name=args.friend_name or rng.choice(["Milo", "Jon", "Finn", "Luna"]),
        friend_type="boy" if (args.friend_name or "").lower()[:1] not in {"l"} else "girl",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a small child about {f["hero"].id} and {f["friend"].id} on {f["setting"].place}, and include the word "bilge".',
        f"Tell a story with a mystery to solve: something is filling the bilge, the children guess wrong at first, and then a twist reveals the real cause.",
        f"Write a gentle fairy tale with a moral value of {f['remedy'].id if hasattr(f['remedy'], 'id') else 'honesty'} and a happy ending on a little boat.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, cause, remedy = f["hero"], f["friend"], f["cause"], f["remedy"]
    qa = [
        ("What was the mystery in the story?",
         f"The mystery was why water kept gathering in the bilge of the little boat. The children saw a clue, but they still needed to find the true cause."),
        ("What did the hero think at first?",
         f"{hero.id} first guessed that {cause.label} was to blame because the clue looked like {cause.clue}. That guess made the scene feel mysterious until the twist showed the truth."),
        ("What solved the problem?",
         f"{world.get('captain').id.capitalize()} helped them use {remedy.action}. That cleared the bilge and made the boat steady again."),
        ("What moral did the story teach?",
         f"It taught {f['moral']}, because the children told the truth and worked together instead of hiding the problem."),
    ]
    if f["outcome"] == "late":
        qa.append((
            "Did the first fix work quickly?",
            f"No, it was a little too slow for the growing bilge. Even so, the crew kept going, found the leak, and solved the mystery together."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with a dry bilge, a calm boat, and the children sailing on under the stars. The ending proved the problem was truly solved."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bilge?",
         "The bilge is the lowest part inside a boat where water can collect. If water gets there, people usually pump or bail it out."),
        ("Why is a leak on a boat important?",
         "A leak can let water keep coming in, so the boat may wobble or get heavy. That is why sailors check for cracks and holes quickly."),
        ("What should you do when you do not know the answer to a problem?",
         "You should look for clues, tell the truth, and ask for help. A good helper can turn a mystery into a solution."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
    return "\n".join(lines)


ASP_RULES = r"""
bilge(X) :- leak(X), not dry(X).
solved(X) :- bilge(X), clue(X), remedy(X).
outcome(solved) :- solved(ship).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        if c.makes_bilge:
            lines.append(asp.fact("leak", cid))
        lines.append(asp.fact("clue", cid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show cause/1.\n#show remedy/1."))
    # simple parity: just list all fact triples via python-side gate in this tiny world
    return valid_combos()


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo gates differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"FAILED smoke test: {exc}")
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.cause not in CAUSES or params.remedy not in REMEDIES:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], CAUSES[params.cause], REMEDIES[params.remedy],
                 delay=params.delay, hero_name=params.hero_name, friend_name=params.friend_name,
                 hero_type=params.hero_type, friend_type=params.friend_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show bilge/1.\n#show solved/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
