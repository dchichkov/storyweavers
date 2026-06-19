#!/usr/bin/env python3
"""
storyworlds/worlds/misty_cozy_cave_rhyme.py
===========================================

Seed prompt used:
    Write a story that includes the following words and narrative instruments.
    Words: misty cave, cozy cave
    Features: Foreshadowing, Twist
    Style: Rhyming Story

Source tale written from the seed:
    Mina climbed Fern Hill with Dad, tapping a rhyme on her tin cup:
    "A misty cave, a chilly wave, may hide the cozy cave."
    She wanted to run inside because the picnic blanket smelled like jam and the
    cave mouth breathed warm air. Dad saw the fog fold over the stones and said
    they needed a guide first; otherwise the cave could turn them around.
    Mina sulked, then helped tie a red thread to the gate stone. They followed
    the thread through the mist and found the surprise: the misty cave and the
    cozy cave were the same cave. Glowworms lit the back wall, the warm spring
    hummed below, and the thread led them safely home after tea.

This script models that story as a tiny world: a child wants to enter a cave, a
guardian predicts the cave hazard on a copy of the world, and the real story is
only allowed when the chosen guide actually solves that hazard. The twist is
earned by state: once the safe guide is embedded in the cave, the scary "misty
cave" can be rendered as the same physical place as the "cozy cave."
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
RISK_METERS = {"lost", "cold", "slip"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass(frozen=True)
class Cave:
    id: str
    hill: str
    mouth: str
    heart: str
    clue: str
    sound: str
    treasure: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Hazard:
    id: str
    adjective: str
    risk: str
    sign: str
    warning: str
    consequence: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Guide:
    id: str
    label: str
    action: str
    solves: set[str]
    proof: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Treat:
    id: str
    label: str
    smell: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, cave: Cave, hazard: Hazard) -> None:
        self.cave = cave
        self.hazard = hazard
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.active_guide: Optional[Guide] = None
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def role(self, role: str) -> Entity:
        for ent in self.entities.values():
            if ent.role == role:
                return ent
        raise KeyError(role)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.cave, self.hazard)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.active_guide = self.active_guide
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def guide_solves(guide: Guide, hazard: Hazard) -> bool:
    return hazard.id in guide.solves


def _r_cave_risk(world: World) -> list[str]:
    cave = world.get("cave")
    hero = world.role("hero")
    guardian = world.role("guardian")
    if hero.memes["entered"] < THRESHOLD:
        return []
    if world.active_guide and guide_solves(world.active_guide, world.hazard):
        return []
    sig = ("risk", world.hazard.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters[world.hazard.risk] += 1
    cave.meters[world.hazard.risk] += 1
    guardian.memes["worry"] += 1
    return [f"The {world.hazard.adjective} cave would make {hero.id} {world.hazard.consequence}."]


def _r_safe_path(world: World) -> list[str]:
    hero = world.role("hero")
    cave = world.get("cave")
    if hero.memes["entered"] < THRESHOLD or not world.active_guide:
        return []
    if not guide_solves(world.active_guide, world.hazard):
        return []
    sig = ("safe_path", world.active_guide.id, world.hazard.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    cave.memes["mapped"] += 1
    return []


def _r_twist(world: World) -> list[str]:
    cave = world.get("cave")
    if cave.memes["mapped"] < THRESHOLD or cave.memes["heart_seen"] < THRESHOLD:
        return []
    sig = ("twist", world.cave.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cave.memes["cozy"] += 1
    cave.memes["wonder"] += 1
    return []


CAUSAL_RULES = [
    Rule("cave_risk", _r_cave_risk),
    Rule("safe_path", _r_safe_path),
    Rule("twist", _r_twist),
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


def _enter(world: World, hero: Entity, narrate: bool = True) -> None:
    hero.memes["entered"] += 1
    propagate(world, narrate=narrate)


def predict_entry(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim.active_guide = None
    _enter(sim, sim.get(hero.id), narrate=False)
    return {
        "risk": world.hazard.risk,
        "amount": sim.get(hero.id).meters[world.hazard.risk],
        "worry": sim.get("guardian").memes["worry"],
    }


def opening_rhyme(cave: Cave) -> str:
    return (
        f'"A {cave.mouth}, a chilly wave, '
        f'may hide the {cave.heart},"'
    )


def introduce(world: World, hero: Entity, guardian: Entity, treat: Treat) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} climbed {world.cave.hill} with {hero.pronoun('possessive')} "
        f"{guardian.label_word}, tapping a rhyme on a tin cup."
    )
    world.say(f"{opening_rhyme(world.cave)} {hero.pronoun()} sang.")
    world.say(
        f"In the basket waited {treat.label}, smelling of {treat.smell}, "
        f"and the cave mouth breathed one small warm puff."
    )


def foreshadow(world: World) -> None:
    world.get("cave").memes["hint"] += 1
    world.say(
        f"That puff was the first clue: {world.cave.clue}. "
        f"From inside came {world.cave.sound}, soft enough to feel secret."
    )


def desire(world: World, hero: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f'{hero.id} bounced on {hero.pronoun("possessive")} toes. '
        f'"Let me race through the {world.cave.mouth} and find the {world.cave.heart}!"'
    )


def warn(world: World, hero: Entity, guardian: Entity) -> None:
    pred = predict_entry(world, hero)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_amount"] = pred["amount"]
    world.say(
        f'{guardian.label_word.capitalize()} looked at the fog folding over the stones. '
        f'"{world.hazard.warning}," {guardian.pronoun()} said. '
        f'"A rhyme is brave, but a guide is braver."'
    )


def sulk(world: World, hero: Entity) -> None:
    hero.memes["frustration"] += 1
    world.say(
        f"{hero.id} made a small frown and kicked one pebble, "
        f"but the pebble vanished before it made a sound."
    )


def prepare_guide(world: World, hero: Entity, guardian: Entity, guide: Guide) -> None:
    guide_ent = world.add(Entity("guide", type="guide", label=guide.label))
    guide_ent.memes["trusted"] += 1
    world.active_guide = guide
    hero.memes["patience"] += 1
    guardian.memes["trust"] += 1
    action = guide.action.replace("{hero}", hero.id)
    proof = guide.proof.replace("{hero}", hero.id)
    world.say(
        f"So {hero.id} helped {guardian.label_word} {action}. "
        f"{proof}"
    )


def discover(world: World, hero: Entity, treat: Treat) -> None:
    _enter(world, hero, narrate=False)
    cave = world.get("cave")
    cave.memes["heart_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They stepped in slowly: drip, tip, dip. The {world.cave.mouth} "
        f"did not steal their way."
    )
    world.say(
        f"Past the bend, glowworms lit the stone like stars. "
        f"There was the twist: the {world.cave.mouth} and the {world.cave.heart} "
        f"were one cave after all."
    )
    world.say(
        f"They shared {treat.label} beside {world.cave.treasure}, "
        f"and the safe guide led them home before night. "
        f"{hero.id} sang the rhyme again, softer and wiser this time."
    )


def tell(cave: Cave, hazard: Hazard, guide: Guide, treat: Treat,
         name: str = "Mina", gender: str = "girl", guardian_type: str = "father",
         trait: str = "curious") -> World:
    world = World(cave, hazard)
    hero = world.add(Entity("hero", kind="character", type=gender, label=name,
                            traits=["little", trait], role="hero"))
    hero.id = name
    world.entities[name] = world.entities.pop("hero")
    guardian = world.add(Entity("guardian", kind="character", type=guardian_type,
                                label="the guardian", role="guardian"))
    world.add(Entity("cave", type="cave", label=cave.mouth))

    introduce(world, hero, guardian, treat)
    foreshadow(world)
    world.para()
    desire(world, hero)
    warn(world, hero, guardian)
    sulk(world, hero)
    world.para()
    prepare_guide(world, hero, guardian, guide)
    discover(world, hero, treat)
    world.facts.update(hero=hero, guardian=guardian, cave=cave, hazard=hazard,
                       guide=guide, treat=treat,
                       resolved=world.get("cave").memes["cozy"] >= THRESHOLD)
    return world


CAVES = {
    "fern_hill": Cave("fern_hill", "Fern Hill", "misty cave", "cozy cave",
                      "warm air curled out where cold mist should have been",
                      "a murmur like a kettle far away", "a warm spring",
                      tags={"cave", "mist", "glowworms"}),
    "moss_bank": Cave("moss_bank", "Moss Bank", "misty cave", "cozy cave",
                      "a dry leaf drifted inward instead of out",
                      "a hum as gentle as bees in a wall", "a bed of soft moss",
                      tags={"cave", "mist", "moss"}),
    "silver_ridge": Cave("silver_ridge", "Silver Ridge", "misty cave", "cozy cave",
                         "the mist smelled faintly of cinnamon stone",
                         "a tick-tock drip keeping time", "a glittering quartz shelf",
                         tags={"cave", "mist", "quartz"}),
}

HAZARDS = {
    "mist": Hazard("mist", "misty", "lost",
                   "fog curled over the path",
                   "This mist can turn a child around before the child knows it",
                   "lose the path", tags={"mist", "lost"}),
    "dark": Hazard("dark", "shadowy", "lost",
                   "the cave swallowed the daylight",
                   "This dark can hide every mark we pass",
                   "wander past the turn", tags={"dark", "lost"}),
    "cold_draft": Hazard("cold_draft", "drafty", "cold",
                         "cold air slid along the floor",
                         "This draft can chill small fingers fast",
                         "shiver too hard to enjoy the cave", tags={"cold"}),
    "slick_stones": Hazard("slick_stones", "dripping", "slip",
                           "water shone on the stones",
                           "These wet stones can slip under quick feet",
                           "slide on the floor", tags={"slippery", "water"}),
}

GUIDES = {
    "red_thread": Guide("red_thread", "a red thread",
                        "tie a red thread to the gate stone and let it trail behind them",
                        {"mist", "dark"},
                        "The thread made a bright line back to the day.",
                        tags={"thread", "guide"}),
    "lantern": Guide("lantern", "a small lantern",
                     "light a small covered lantern and hold it low",
                     {"dark", "slick_stones"},
                     "The lantern showed each stone before a shoe touched it.",
                     tags={"lantern", "light"}),
    "wool_cloak": Guide("wool_cloak", "a wool cloak",
                        "wrap a wool cloak around {hero}'s shoulders",
                        {"cold_draft"},
                        "The cloak caught the draft before the draft caught {hero}.",
                        tags={"warmth", "cloak"}),
    "walking_stick": Guide("walking_stick", "a walking stick",
                           "test each wet stone with a walking stick",
                           {"slick_stones"},
                           "Tap, tap, tap went the stick, finding the safe stones first.",
                           tags={"stick", "slippery"}),
}

TREATS = {
    "jam_buns": Treat("jam_buns", "two jam buns", "strawberry jam", tags={"picnic"}),
    "honey_cakes": Treat("honey_cakes", "honey cakes", "honey and oats", tags={"picnic"}),
    "apple_tea": Treat("apple_tea", "warm apple tea", "apples and spice", tags={"tea"}),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Rose"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Sam"]
TRAITS = ["curious", "rhyming", "eager", "bright", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for cave_id in CAVES:
        for hazard_id, hazard in HAZARDS.items():
            for guide_id, guide in GUIDES.items():
                if guide_solves(guide, hazard):
                    combos.append((cave_id, hazard_id, guide_id))
    return sorted(combos)


@dataclass
class StoryParams:
    cave: str
    hazard: str
    guide: str
    treat: str
    name: str
    gender: str
    guardian: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cave": [("What is a cave?",
              "A cave is a hollow place inside rock or earth. Some caves are dark or wet, so people move carefully inside them.")],
    "mist": [("What is mist?",
              "Mist is tiny drops of water floating in the air. It can make faraway things look blurry.")],
    "lost": [("Why can fog or darkness make people get lost?",
              "Fog and darkness hide landmarks, so paths and turns are harder to see. A guide or light helps people find their way back.")],
    "thread": [("How can a thread help in a cave?",
                "A thread can mark the way back. If someone follows it carefully, they can return to where they started.")],
    "lantern": [("What does a lantern do?",
                 "A lantern carries light safely, so people can see the ground and the walls in a dark place.")],
    "warmth": [("Why does warm clothing help in a draft?",
                "Warm clothing holds body heat close and keeps cold air from chilling your skin.")],
    "slippery": [("Why should you walk slowly on wet stones?",
                  "Wet stones can be slick. Slow steps and a steady stick make slipping less likely.")],
    "glowworms": [("What are glowworms?",
                   "Glowworms are tiny living things that can make soft light. In stories, they often make caves feel magical.")],
}
KNOWLEDGE_ORDER = ["cave", "mist", "lost", "thread", "lantern", "warmth", "slippery", "glowworms"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, cave, hazard, guide = f["hero"], f["cave"], f["hazard"], f["guide"]
    return [
        'Write a rhyming story for young children that includes "misty cave" and "cozy cave" with foreshadowing and a twist.',
        f"Tell a gentle cave story where {hero.id} wants to rush into a {cave.mouth}, "
        f"but a guardian predicts {hazard.consequence} and uses {guide.label} first.",
        f"Write a story where the twist is that the scary {cave.mouth} and the {cave.heart} are the same physical cave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, guardian = f["hero"], f["guardian"]
    cave, hazard, guide = f["cave"], f["hazard"], f["guide"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, a {hero.type} who likes rhymes, and {hero.pronoun('possessive')} {guardian.label_word}."),
        ("What did the first clue suggest?",
         f"The warm puff from the {cave.mouth} suggested the cave might not be only scary or cold. It foreshadowed the cozy place inside."),
        (f"Why did {guardian.label_word} stop {hero.id}?",
         f"{guardian.label_word.capitalize()} predicted that the {hazard.adjective} cave could make {hero.id} {hazard.consequence}. That risk was not happening yet; it came from imagining what would happen without a guide."),
        ("What guide did they use?",
         f"They used {guide.label}. It worked because it addressed the actual cave problem: {guide.proof.replace('{hero}', hero.id)}"),
        ("What was the twist?",
         f"The twist was that the {cave.mouth} and the {cave.heart} were the same cave. Once they entered safely, the same place changed from frightening to welcoming."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["cave"].tags) | set(world.facts["hazard"].tags) | set(world.facts["guide"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  active guide: {world.active_guide.id if world.active_guide else 'none'}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("fern_hill", "mist", "red_thread", "jam_buns", "Mina", "girl", "father", "rhyming"),
    StoryParams("moss_bank", "dark", "lantern", "honey_cakes", "Theo", "boy", "mother", "curious"),
    StoryParams("silver_ridge", "cold_draft", "wool_cloak", "apple_tea", "Nora", "girl", "uncle", "eager"),
    StoryParams("fern_hill", "slick_stones", "walking_stick", "jam_buns", "Finn", "boy", "aunt", "bold"),
]


def explain_rejection(hazard: Hazard, guide: Guide) -> str:
    return (
        f"(No story: {guide.label} does not solve the {hazard.id.replace('_', ' ')} problem. "
        f"The guardian's plan must address the predicted risk that the cave would make the child {hazard.consequence}.)"
    )


ASP_RULES = r"""
solves_problem(G,H) :- guide(G), hazard(H), solves(G,H).
valid(C,H,G) :- cave(C), hazard(H), guide(G), solves_problem(G,H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cave_id in CAVES:
        lines.append(asp.fact("cave", cave_id))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for guide_id, guide in GUIDES.items():
        lines.append(asp.fact("guide", guide_id))
        for hazard_id in sorted(guide.solves):
            lines.append(asp.fact("solves", guide_id, hazard_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
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
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rhyming cave story with foreshadowing and a twist.")
    ap.add_argument("--cave", choices=CAVES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.guide:
        hazard, guide = HAZARDS[args.hazard], GUIDES[args.guide]
        if not guide_solves(guide, hazard):
            raise StoryError(explain_rejection(hazard, guide))
    combos = [
        combo for combo in valid_combos()
        if (args.cave is None or combo[0] == args.cave)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.guide is None or combo[2] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    cave, hazard, guide = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father", "aunt", "uncle"])
    treat = args.treat or rng.choice(sorted(TREATS))
    trait = rng.choice(TRAITS)
    return StoryParams(cave, hazard, guide, treat, name, gender, guardian, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(CAVES[params.cave], HAZARDS[params.hazard], GUIDES[params.guide],
                 TREATS[params.treat], params.name, params.gender,
                 params.guardian, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cave, hazard, guide) combos:\n")
        for cave, hazard, guide in combos:
            print(f"  {cave:12} {hazard:12} {guide}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.hazard} solved by {p.guide} ({p.cave})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
