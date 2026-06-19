#!/usr/bin/env python3
"""
storyworlds/worlds/shiny_pond_sounds.py
=======================================

A standalone storyworld for the seed:

    Words: shiny pond, petite, cozy
    Features: Sound Effects
    Style: Heartwarming

Source tale written from the seed
---------------------------------
Petite Nell made a paper boat at the cozy kitchen table while rain tapped
tip-tip on the window. When the sun came back, the shiny pond outside looked
like a silver button. Nell wanted to launch the boat at once.

Grandpa noticed the wind making tiny waves, plip-plap, across the pond. He
imagined the paper boat drifting into the reeds and getting soggy before Nell
could reach it. Nell hugged the boat and felt cross for a moment, because the
pond looked so bright and ready.

Then Grandpa tied a red ribbon to the boat and made a little twig dock. Nell
set the boat down, the ribbon went whisper-whisk, and the boat bobbed safely
near the shore. Nell laughed, Grandpa laughed, and the shiny pond carried their
cozy little voyage without carrying the boat away.

The model
---------
The story is about a loved small craft, a pond condition that could carry it
away, a caregiver who predicts that risk on a copy of the world, and a safeguard
that must actually address the condition. The real timeline launches only after
the safeguard is embedded, so the boat's loss stays counterfactual.
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
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    caretaker: str = ""
    region: str = ""
    anchored_by: str = ""
    reachable_by: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt"}
        male = {"boy", "father", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def kin_word(self) -> str:
        return {
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "father": "dad",
            "mother": "mom",
        }.get(self.type, self.type)


@dataclass
class Pond:
    id: str
    place: str
    cozy_from: str
    detail: str
    affords: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Condition:
    id: str
    phrase: str
    sound: str
    risk: str
    force: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Craft:
    id: str
    label: str
    phrase: str
    made_from: str
    stability: int
    delicate: bool
    prep_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Safeguard:
    id: str
    label: str
    handles: set[str]
    strength: int
    setup: str
    launch_sound: str
    final_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, pond: Pond, condition: Condition) -> None:
        self.pond = pond
        self.condition = condition
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
        clone = World(self.pond, self.condition)
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


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    craft = world.entities.get("craft")
    hero = world.entities.get("hero")
    if not craft or not hero or craft.meters["launched"] < THRESHOLD:
        return out
    if craft.meters["protected"] >= THRESHOLD:
        return out
    risk = world.condition.risk
    if risk == "carry" and craft.attrs["stability"] < world.condition.force:
        sig = ("drift", craft.id, world.condition.id)
        if sig not in world.fired:
            world.fired.add(sig)
            craft.meters["drifting"] += 1
            hero.memes["worry"] += 1
            out.append("The little craft began to slip away from the shore.")
    return out


def _r_soggy(world: World) -> list[str]:
    out: list[str] = []
    craft = world.entities.get("craft")
    if not craft or craft.meters["drifting"] < THRESHOLD or not craft.attrs.get("delicate"):
        return out
    sig = ("soggy", craft.id)
    if sig not in world.fired:
        world.fired.add(sig)
        craft.meters["soggy"] += 1
        out.append(f"The {craft.label} got soggy before anyone could reach it.")
    return out


def _r_safe_bob(world: World) -> list[str]:
    out: list[str] = []
    craft = world.entities.get("craft")
    hero = world.entities.get("hero")
    if not craft or not hero:
        return out
    if craft.meters["launched"] >= THRESHOLD and craft.meters["protected"] >= THRESHOLD:
        sig = ("safe_bob", craft.id)
        if sig not in world.fired:
            world.fired.add(sig)
            craft.meters["safe"] += 1
            hero.memes["joy"] += 1
            out.append("__safe__")
    return out


CAUSAL_RULES = [
    Rule("drift", "physical", _r_drift),
    Rule("soggy", "physical", _r_soggy),
    Rule("safe_bob", "physical_social", _r_safe_bob),
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


def craft_at_risk(condition: Condition, craft: Craft) -> bool:
    return condition.force > craft.stability


def protects(safeguard: Safeguard, condition: Condition, craft: Craft) -> bool:
    return condition.risk in safeguard.handles and safeguard.strength >= condition.force - craft.stability


def select_safeguard(condition: Condition, craft: Craft) -> Optional[Safeguard]:
    choices = [s for s in SAFEGUARDS.values() if protects(s, condition, craft)]
    return sorted(choices, key=lambda s: (s.strength, s.id))[0] if choices else None


def predict_drift(world: World) -> dict:
    sim = world.copy()
    launch(sim, sim.get("craft"), narrate=False)
    craft = sim.get("craft")
    return {
        "drifts": craft.meters["drifting"] >= THRESHOLD,
        "soggy": craft.meters["soggy"] >= THRESHOLD,
        "hero_worry": sim.get("hero").memes["worry"],
    }


def introduce(world: World, hero: Entity, helper: Entity, craft_cfg: Craft) -> None:
    hero.memes["love_make"] += 1
    craft = world.get("craft")
    world.say(
        f"{hero.id} was a petite {hero.type} who loved small, careful things. "
        f"At the {world.pond.cozy_from}, {hero.pronoun()} made {craft.phrase} "
        f"from {craft_cfg.made_from}; {craft_cfg.prep_sound}."
    )
    world.say(
        f"{helper.id} watched with warm hands around a mug and said the "
        f"{craft.label} looked ready for a voyage."
    )


def see_pond(world: World, hero: Entity) -> None:
    world.say(
        f"When the clouds moved away, the shiny pond outside looked bright and "
        f"round. {world.pond.detail}"
    )
    world.say(
        f'{hero.id} hugged the craft to {hero.pronoun("possessive")} chest. '
        f'"Can we launch it now?" {hero.pronoun()} asked.'
    )


def warn(world: World, hero: Entity, helper: Entity, craft_cfg: Craft) -> bool:
    pred = predict_drift(world)
    helper.memes["care"] += 1
    if not pred["drifts"]:
        return False
    world.facts["predicted_drift"] = True
    world.facts["predicted_soggy"] = pred["soggy"]
    consequence = "drift into the reeds"
    if pred["soggy"]:
        consequence += " and get soggy"
    world.say(
        f'{helper.id} listened to the pond: {world.condition.sound}. '
        f'"If we put {craft_cfg.phrase} straight in, it may {consequence}," '
        f"{helper.pronoun()} said. \"Let's help it stay close.\""
    )
    return True


def resist(world: World, hero: Entity) -> None:
    hero.memes["impatience"] += 1
    if hero.memes["impatience"] >= THRESHOLD:
        world.say(
            f"{hero.id} frowned for one tiny moment, because the shiny pond "
            f"looked ready right now."
        )


def prepare_safeguard(world: World, hero: Entity, helper: Entity,
                      safeguard: Safeguard) -> None:
    craft = world.get("craft")
    guard = world.add(Entity("safeguard", type="safeguard", label=safeguard.label))
    guard.meters["ready"] += 1
    craft.anchored_by = guard.id
    craft.meters["protected"] += 1
    hero.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Together they chose {safeguard.label}. "
        f"{safeguard.setup.format(hero=hero.id, helper=helper.id)} "
        f"{hero.id}'s shoulders softened; the waiting did not feel like no "
        f"anymore, it felt like help."
    )


def launch(world: World, craft: Entity, narrate: bool = True) -> None:
    craft.meters["launched"] += 1
    propagate(world, narrate=narrate)


def safe_launch(world: World, hero: Entity, helper: Entity, safeguard: Safeguard) -> None:
    craft = world.get("craft")
    launch(world, craft)
    world.say(
        f"{hero.id} set the {craft.label} on the water. {safeguard.launch_sound} "
        f"The pond answered with soft plip-plap sounds, but the {craft.label} "
        f"bobbed safely near the shore."
    )
    if craft.meters["safe"] >= THRESHOLD:
        hero.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.say(
            f"{safeguard.final_image.format(hero=hero.id, helper=helper.id)} "
            f"{hero.id} laughed, {helper.id} laughed, "
            f"and the cozy little voyage stayed close enough to love."
        )


def tell(pond: Pond, condition: Condition, craft_cfg: Craft, safeguard: Safeguard,
         name: str = "Nell", gender: str = "girl", helper_type: str = "grandfather",
         trait: str = "patient") -> World:
    world = World(pond, condition)
    hero = world.add(Entity("hero", kind="character", type=gender, label=name,
                            traits=["petite", trait]))
    hero.id = name
    helper = world.add(Entity("helper", kind="character", type=helper_type,
                              label="the helper"))
    helper.id = helper_type.capitalize() if helper_type in {"mother", "father"} else {
        "grandfather": "Grandpa", "grandmother": "Grandma", "uncle": "Uncle Ray",
        "aunt": "Aunt Mira",
    }[helper_type]
    craft = world.add(Entity("craft", type="craft", label=craft_cfg.label,
                             owner=hero.id, caretaker=helper.id,
                             attrs={"stability": craft_cfg.stability,
                                    "delicate": craft_cfg.delicate}))
    craft.phrase = craft_cfg.phrase

    introduce(world, hero, helper, craft_cfg)
    world.para()
    see_pond(world, hero)
    warn(world, hero, helper, craft_cfg)
    resist(world, hero)
    world.para()
    prepare_safeguard(world, hero, helper, safeguard)
    safe_launch(world, hero, helper, safeguard)

    world.facts.update(hero=hero, helper=helper, craft=craft, craft_cfg=craft_cfg,
                       pond=pond, condition=condition, safeguard=safeguard,
                       resolved=craft.meters["safe"] >= THRESHOLD)
    return world


PONDS = {
    "garden": Pond("garden", "the garden pond", "cozy kitchen table",
                   "The stones around it held little dots of sun.",
                   {"breeze", "ripples", "still"}, {"pond", "cozy"}),
    "courtyard": Pond("courtyard", "the courtyard pond", "cozy window seat",
                      "Goldfish stitched orange lines under the shine.",
                      {"breeze", "ripples"}, {"pond"}),
    "park": Pond("park", "the park pond", "cozy picnic blanket",
                 "Ducks tucked their beaks and made sleepy circles.",
                 {"breeze", "current", "still"}, {"pond", "ducks"}),
}

CONDITIONS = {
    "breeze": Condition("breeze", "a teasing breeze", "whish-whish", "carry", 3,
                        {"wind", "sound"}),
    "ripples": Condition("ripples", "busy little ripples", "plip-plap", "carry", 2,
                         {"ripples", "sound"}),
    "current": Condition("current", "a slow side current", "shoop, shoop", "carry", 4,
                         {"current", "sound"}),
    "still": Condition("still", "still water", "plink", "carry", 1,
                       {"pond", "sound"}),
}

CRAFTS = {
    "paper_boat": Craft("paper_boat", "paper boat", "a paper boat",
                        "a square of blue paper", 1, True, "Crease, pat, crease went the folds",
                        {"paper", "boat"}),
    "leaf_boat": Craft("leaf_boat", "leaf boat", "a leaf boat",
                       "a wide green leaf and a twig mast", 2, True,
                       "Tap-tap went the twig mast", {"leaf", "boat"}),
    "cork_raft": Craft("cork_raft", "cork raft", "a cork raft",
                       "three corks and a bit of string", 3, False,
                       "Tug-tug went the knot", {"raft"}),
    "wooden_duck": Craft("wooden_duck", "wooden duck", "a tiny wooden duck",
                         "a smooth scrap of wood", 4, False,
                         "Scritch-scratch went the sanding", {"duck"}),
}

SAFEGUARDS = {
    "ribbon": Safeguard("ribbon", "a red ribbon tether", {"carry"}, 2,
                        "{helper} tied one end gently to the craft and kept the other end loose in {hero}'s hand.",
                        "Whisper-whisk went the ribbon.",
                        "The red ribbon drew a bright line from {hero}'s hand to the water.",
                        {"ribbon", "tether"}),
    "twig_dock": Safeguard("twig_dock", "a twig dock", {"carry"}, 1,
                           "They tucked twigs between two stones to make a snug little harbor.",
                           "Tok-tok went the twigs.",
                           "The twig dock made a tiny harbor by the shiny shore.",
                           {"dock"}),
    "landing_net": Safeguard("landing_net", "the little landing net", {"carry"}, 3,
                             "{helper} rested the net beside the reeds so it could catch the craft if it wandered.",
                             "Swish went the net.",
                             "The net waited like a soft gate beside the reeds.",
                             {"net"}),
}

GIRL_NAMES = ["Nell", "Mia", "Ava", "Lily", "Rose", "Ivy"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Finn", "Max"]
TRAITS = ["patient", "gentle", "curious", "quiet", "hopeful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for pond_id, pond in PONDS.items():
        for cond_id in pond.affords:
            cond = CONDITIONS[cond_id]
            for craft_id, craft in CRAFTS.items():
                if not craft_at_risk(cond, craft):
                    continue
                for guard_id, guard in SAFEGUARDS.items():
                    if protects(guard, cond, craft):
                        combos.append((pond_id, cond_id, craft_id, guard_id))
    return sorted(combos)


@dataclass
class StoryParams:
    pond: str
    condition: str
    craft: str
    safeguard: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "pond": [("What is a pond?",
              "A pond is a small body of water. It can be still, shiny, muddy, or full of tiny ripples.")],
    "wind": [("What can wind do to a small toy boat?",
              "Wind can push a small toy boat across the water. If the boat is very light, it can drift away quickly.")],
    "ripples": [("What are ripples?",
                 "Ripples are small waves on the surface of water. They can move tiny floating things a little at a time.")],
    "current": [("What is a current in water?",
                 "A current is moving water. Even a slow current can carry leaves, sticks, or little boats away.")],
    "paper": [("Why does paper get soggy in water?",
               "Paper soaks up water. When it gets too wet, it becomes soft and can tear or sink.")],
    "ribbon": [("How can a string or ribbon help a toy boat?",
                "A string or ribbon can act like a tether. It lets the boat float while keeping it close enough to bring back.")],
    "dock": [("What does a little dock do?",
              "A dock gives a boat a safe place to start and stop. Even a pretend twig dock can make a small harbor.")],
    "net": [("What is a landing net for?",
             "A landing net can gently catch something in the water so a grown-up can bring it back safely.")],
}
KNOWLEDGE_ORDER = ["pond", "wind", "ripples", "current", "paper", "ribbon", "dock", "net"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, craft, condition = f["hero"], f["craft_cfg"], f["condition"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes "shiny pond", "petite", and "cozy", with sound effects.',
        f"Tell a story where {hero.id}, a petite {hero.type}, wants to launch {craft.phrase} on a shiny pond, but {condition.phrase} might carry it away.",
        f"Write a cozy pond story where a caregiver predicts a problem and helps a child choose a safe way to play.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    craft, condition, safeguard = f["craft_cfg"], f["condition"], f["safeguard"]
    hp = hero.pronoun("possessive")
    qa = [
        ("Who is the story about?",
         f"It is about a petite {hero.type} named {hero.id} and {hp} {helper.kin_word}. They are trying to launch {craft.phrase} at a shiny pond."),
        (f"What did {hero.id} make?",
         f"{hero.id} made {craft.phrase} from {craft.made_from}. The craft mattered because {hero.pronoun()} had made it carefully."),
        ("Why did the caregiver ask the child to wait?",
         f"{helper.id} predicted that {condition.phrase} could carry the {craft.label} away. In the model, the unprotected craft would drift before {hero.id} could enjoy it."),
        ("How did they solve the problem?",
         f"They used {safeguard.label}, which addressed the carrying risk. That let the {craft.label} float on the pond while staying close to shore."),
        ("How did the story end?",
         f"The {craft.label} bobbed safely near the shore, and both {hero.id} and {helper.id} laughed. The final image shows the pond carrying their voyage without carrying the craft away."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["pond"].tags) | set(f["condition"].tags) | set(f["craft_cfg"].tags) | set(f["safeguard"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.anchored_by:
            bits.append(f"anchored_by={ent.anchored_by}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "breeze", "paper_boat", "ribbon", "Nell", "girl", "grandfather", "patient"),
    StoryParams("courtyard", "ripples", "paper_boat", "twig_dock", "Mia", "girl", "grandmother", "gentle"),
    StoryParams("park", "current", "paper_boat", "landing_net", "Leo", "boy", "father", "curious"),
    StoryParams("park", "breeze", "leaf_boat", "ribbon", "Finn", "boy", "aunt", "hopeful"),
]


def explain_rejection(condition: Condition, craft: Craft, safeguard: Optional[Safeguard] = None) -> str:
    if not craft_at_risk(condition, craft):
        return (f"(No story: {condition.phrase} is not strong enough to carry away "
                f"{craft.phrase}, so the warning would be dishonest.)")
    if safeguard and not protects(safeguard, condition, craft):
        return (f"(No story: {safeguard.label} does not handle the pond's "
                f"{condition.risk} risk strongly enough for {craft.phrase}.)")
    return (f"(No story: no available safeguard can honestly keep {craft.phrase} "
            f"safe from {condition.phrase}.)")


ASP_RULES = r"""
risk_at(Cond, Craft) :- force(Cond, F), stability(Craft, S), F > S.
protects(Guard, Cond, Craft) :- safeguard(Guard), handles(Guard, Risk),
                                risk(Cond, Risk), strength(Guard, G),
                                force(Cond, F), stability(Craft, S), G >= F - S.
valid(Pond, Cond, Craft, Guard) :- affords(Pond, Cond), risk_at(Cond, Craft),
                                   protects(Guard, Cond, Craft).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pond_id, pond in PONDS.items():
        lines.append(asp.fact("pond", pond_id))
        for cond in sorted(pond.affords):
            lines.append(asp.fact("affords", pond_id, cond))
    for cond_id, cond in CONDITIONS.items():
        lines.append(asp.fact("condition", cond_id))
        lines.append(asp.fact("risk", cond_id, cond.risk))
        lines.append(asp.fact("force", cond_id, cond.force))
    for craft_id, craft in CRAFTS.items():
        lines.append(asp.fact("craft", craft_id))
        lines.append(asp.fact("stability", craft_id, craft.stability))
    for guard_id, guard in SAFEGUARDS.items():
        lines.append(asp.fact("safeguard", guard_id))
        lines.append(asp.fact("strength", guard_id, guard.strength))
        for risk in sorted(guard.handles):
            lines.append(asp.fact("handles", guard_id, risk))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a petite child, a shiny pond, and a safe tiny voyage.")
    ap.add_argument("--pond", choices=PONDS)
    ap.add_argument("--condition", choices=CONDITIONS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--safeguard", choices=SAFEGUARDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandfather", "grandmother", "uncle", "aunt"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print facts plus inline ASP rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.pond and args.condition and args.condition not in PONDS[args.pond].affords:
        raise StoryError(f"(No story: {PONDS[args.pond].place} does not have {CONDITIONS[args.condition].phrase} in this world.)")
    if args.condition and args.craft:
        cond, craft = CONDITIONS[args.condition], CRAFTS[args.craft]
        if not craft_at_risk(cond, craft):
            raise StoryError(explain_rejection(cond, craft))
        if args.safeguard and not protects(SAFEGUARDS[args.safeguard], cond, craft):
            raise StoryError(explain_rejection(cond, craft, SAFEGUARDS[args.safeguard]))

    combos = [
        c for c in valid_combos()
        if (args.pond is None or c[0] == args.pond)
        and (args.condition is None or c[1] == args.condition)
        and (args.craft is None or c[2] == args.craft)
        and (args.safeguard is None or c[3] == args.safeguard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    pond, condition, craft, safeguard = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "grandfather", "grandmother", "uncle", "aunt"])
    trait = rng.choice(TRAITS)
    return StoryParams(pond, condition, craft, safeguard, name, gender, helper, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PONDS[params.pond], CONDITIONS[params.condition],
                 CRAFTS[params.craft], SAFEGUARDS[params.safeguard],
                 params.name, params.gender, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (pond, condition, craft, safeguard) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{x:12}" for x in combo))
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
            header = f"### {p.name}: {p.craft} at {p.pond} ({p.condition}, {p.safeguard})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
