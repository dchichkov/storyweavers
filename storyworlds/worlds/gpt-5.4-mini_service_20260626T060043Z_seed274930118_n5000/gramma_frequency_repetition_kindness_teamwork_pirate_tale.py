#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gramma_frequency_repetition_kindness_teamwork_pirate_tale.py
===============================================================================================================================

A small pirate-tale story world about a crew, a gramma, and the way kindness
and teamwork can turn repetition into a win.

Premise:
- A pirate crew practices a repeated sea task.
- The task's frequency matters: too much repetition without care makes the work
  feel tiring and noisy.
- Gramma notices the problem, offers kindness, and helps the crew work together.
- The ending shows that a gentler rhythm and shared effort changed the mood.

The world models physical meters and emotional memes for:
- people, a ship, and a important signal bell
- repeated actions, fatigue, clutter, cheer, and cooperation

The script supports:
- normal story generation
- --qa, --json, --trace
- --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# -----------------------------------------------------------------------------
# World constants
# -----------------------------------------------------------------------------
THRESHOLD = 1.0

CREW_NAMES = ["Mira", "Tess", "Nell", "Pip", "Jory", "Bea", "Mabel", "Rory"]
PIRATE_NAMES = ["Cap'n Reed", "Cap'n Willow", "Cap'n Flint", "Cap'n Sable"]
TRAITS = ["brave", "sparkly-eyed", "quick", "curious", "cheerful", "mischievous"]

FREQUENCIES = {
    "often": 3,
    "again and again": 4,
    "many times": 5,
    "three times": 3,
    "five times": 5,
}

# -----------------------------------------------------------------------------
# Shared entity model
# -----------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "gramma", "grandma"}
        male = {"boy", "man", "father", "grandfather", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    name: str = "the bright harbor"
    place_detail: str = "the deck beside the mast"
    affords: set[str] = field(default_factory=lambda: {"bell", "sort"})

@dataclass
class Ritual:
    id: str
    verb: str
    gerund: str
    noun: str
    mess: str
    fatigue: float
    clutter: float
    keyword: str
    tags: set[str] = field(default_factory=set)

@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    kind_action: str
    teamwork_gain: float
    kindness_gain: float

@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False

class World:
    def __init__(self, harbor: Harbor):
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.frequency_word: str = ""
        self.frequency_n: int = 0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self):
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
        import copy as _copy
        w = World(self.harbor)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.frequency_word = self.frequency_word
        w.frequency_n = self.frequency_n
        return w


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
HARBOR = Harbor()

RITUALS = {
    "bell": Ritual(
        id="bell",
        verb="ring the ship bell",
        gerund="ringing the ship bell",
        noun="bell",
        mess="noise",
        fatigue=1.0,
        clutter=0.5,
        keyword="frequency",
        tags={"bell", "frequency", "repetition"},
    ),
    "sort": Ritual(
        id="sort",
        verb="sort the tangled ropes",
        gerund="sorting tangled ropes",
        noun="ropes",
        mess="tangle",
        fatigue=1.0,
        clutter=1.0,
        keyword="repetition",
        tags={"rope", "repetition", "teamwork"},
    ),
}

HELPERS = {
    "lantern": Helper(
        id="lantern",
        label="a warm lantern",
        prep="bring a warm lantern to the rope pile",
        tail="set the lantern near the ropes",
        kind_action="guided the work",
        teamwork_gain=1.0,
        kindness_gain=1.0,
    ),
    "song": Helper(
        id="song",
        label="a soft humming song",
        prep="hum a soft song together",
        tail="hummed softly while they worked",
        kind_action="kept everyone gentle",
        teamwork_gain=1.0,
        kindness_gain=1.0,
    ),
}

PRIZES = {
    "box": Prize(
        id="box",
        label="supply box",
        phrase="a little supply box with biscuits and string",
        region="deck",
    ),
    "flag": Prize(
        id="flag",
        label="bright flag",
        phrase="a bright flag for the mast",
        region="mast",
    ),
}

# -----------------------------------------------------------------------------
# Story parameters
# -----------------------------------------------------------------------------
@dataclass
class StoryParams:
    ritual: str
    helper: str
    prize: str
    hero_name: str
    gramma_name: str
    captain_name: str
    frequency: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def choose_frequency_word(rng: random.Random) -> str:
    return rng.choice(sorted(FREQUENCIES))

def ensure_reasonable(params: StoryParams) -> None:
    if params.frequency not in FREQUENCIES:
        raise StoryError("Unknown frequency word.")
    if params.ritual not in RITUALS:
        raise StoryError("Unknown pirate ritual.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")

def predict(world: World, ritual: Ritual) -> dict:
    sim = world.copy()
    actor = sim.get("hero")
    actor.meters[ritual.mess] = actor.meters.get(ritual.mess, 0) + 1
    actor.memes["tired"] = actor.memes.get("tired", 0) + ritual.fatigue
    actor.memes["stuck"] = actor.memes.get("stuck", 0) + ritual.clutter
    return {
        "tired": actor.memes["tired"] >= THRESHOLD,
        "stuck": actor.memes["stuck"] >= THRESHOLD,
    }

def opening(world: World, hero: Entity, gramma: Entity, captain: Entity, prize: Entity, ritual: Ritual) -> None:
    world.say(
        f"On the bright harbor, {hero.id} was a little pirate with a quick grin, "
        f"and {gramma.id} was the kindest gramma on the pier."
    )
    world.say(
        f"{hero.id} loved {ritual.gerund}, because {ritual.verb} made the ship feel busy and brave."
    )
    world.say(
        f"{captain.id} had brought {prize.phrase}, and the crew kept it safe by hanging it near the mast."
    )

def repeated_work(world: World, hero: Entity, ritual: Ritual, frequency_word: str) -> None:
    n = FREQUENCIES[frequency_word]
    world.frequency_word = frequency_word
    world.frequency_n = n
    world.say(
        f"That day, {hero.id} had to {ritual.verb} {frequency_word}, and the same sound kept coming back."
    )
    for i in range(n):
        hero.meters[ritual.mess] = hero.meters.get(ritual.mess, 0) + 1
        hero.memes["tired"] = hero.memes.get("tired", 0) + ritual.fatigue
        if i == 0:
            world.say(f"The first ring was loud and shiny.")
        elif i == n - 1:
            world.say(f"By the last time, {hero.id} was blinking hard and rubbing a sore wrist.")

def worry(world: World, gramma: Entity, hero: Entity, ritual: Ritual, prize: Prize) -> None:
    pred = predict(world, ritual)
    if pred["tired"] or pred["stuck"]:
        gramma.memes["kindness"] = gramma.memes.get("kindness", 0) + 1
        world.say(
            f"{gramma.id} saw the tired look and said, "
            f"\"No little pirate should do all that alone when the work comes back so often.\""
        )
        world.say(
            f"She pointed at the ropes and the {prize.label}, and her voice sounded warm as tea."
        )

def offer_help(world: World, gramma: Entity, hero: Entity, helper: Helper, ritual: Ritual) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.memes["stuck"] = max(0.0, hero.memes.get("stuck", 0) - 1)
    world.say(
        f"{gramma.id} smiled and said they could {helper.prep}, then do the job together."
    )

def teamwork(world: World, hero: Entity, gramma: Entity, helper: Helper, ritual: Ritual, prize: Prize) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0) + helper.teamwork_gain
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + helper.kindness_gain
    hero.memes["tired"] = max(0.0, hero.memes.get("tired", 0) - 1)
    world.say(
        f"{hero.id} and {gramma.id} worked side by side, and {helper.tail}."
    )
    world.say(
        f"With two pairs of hands, the repeated job felt lighter, and the {prize.label} stayed safe."
    )

def ending(world: World, hero: Entity, gramma: Entity, prize: Prize, ritual: Ritual) -> None:
    world.say(
        f"In the end, {hero.id} still did {ritual.gerund}, but now it had a gentler rhythm."
    )
    world.say(
        f"{hero.id} laughed beside {gramma.id}, and the bright {prize.label} shone over the calm deck."
    )

# -----------------------------------------------------------------------------
# Story generation
# -----------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    ensure_reasonable(params)
    world = World(HARBOR)
    ritual = RITUALS[params.ritual]
    helper = HELPERS[params.helper]
    prize = PRIZES[params.prize]

    hero = world.add(Entity(id="hero", kind="character", type="pirate", label=params.hero_name))
    gramma = world.add(Entity(id="gramma", kind="character", type="grandmother", label=params.gramma_name))
    captain = world.add(Entity(id="captain", kind="character", type="pirate", label=params.captain_name))
    box = world.add(Entity(id="prize", kind="thing", type=prize.id, label=prize.label, phrase=prize.phrase, caretaker=gramma.id))

    opening(world, hero, gramma, captain, box, ritual)
    world.para()
    repeated_work(world, hero, ritual, params.frequency)
    worry(world, gramma, hero, ritual, prize)
    world.para()
    offer_help(world, gramma, hero, helper, ritual)
    teamwork(world, hero, gramma, helper, ritual, prize)
    ending(world, hero, gramma, prize, ritual)

    world.facts.update(
        hero=hero, gramma=gramma, captain=captain, prize=box,
        ritual=ritual, helper=helper, frequency=params.frequency,
        frequency_n=FREQUENCIES[params.frequency], resolved=True
    )
    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child about "{f["frequency"]}" and a crew that learns to share a repeated job.',
        f"Tell a story where {f['gramma'].label} helps {f['hero'].label} through {f['frequency']} rounds of {f['ritual'].gerund}.",
        f"Write a gentle pirate story that includes gramma, repetition, kindness, and teamwork.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    gramma = f["gramma"]
    prize = f["prize"]
    ritual = f["ritual"]
    helper = f["helper"]
    freq = f["frequency"]
    return [
        QAItem(
            question=f"Who was doing the repeated pirate job at the harbor?",
            answer=f"{hero.label} was the little pirate doing the repeated job, and {gramma.label} watched over the work."
        ),
        QAItem(
            question=f"What word tells how often {hero.label} had to {ritual.verb}?",
            answer=f"The story says {freq}, which means the same pirate job kept coming back that many times."
        ),
        QAItem(
            question=f"Why did {gramma.label} step in when {hero.label} kept {ritual.gerund}?",
            answer=f"{gramma.label} noticed that the work was happening again and again, and it was making {hero.label} tired. She wanted to be kind and help."
        ),
        QAItem(
            question=f"How did {gramma.label} and {hero.label} change the end of the story?",
            answer=f"They worked together, so the repeated job felt lighter and the {prize.label} stayed safe by the mast."
        ),
        QAItem(
            question=f"What did the helper plan do for the crew?",
            answer=f"The helper plan let {gramma.label} and {hero.label} share the work, which showed teamwork and made the pirate task gentler."
        ),
    ]

KNOWLEDGE = {
    "frequency": [
        QAItem(
            question="What does frequency mean?",
            answer="Frequency means how often something happens or how many times it repeats."
        ),
    ],
    "repetition": [
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying the same thing again and again."
        ),
    ],
    "kindness": [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, caring, and helpful to someone else."
        ),
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other reach the same goal."
        ),
    ],
    "gramma": [
        QAItem(
            question="Who is a gramma?",
            answer="A gramma is a child's grandmother, a family member who is often caring and warm."
        ),
    ],
    "pirate": [
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a sea traveler from stories who sails ships and goes on adventures."
        ),
    ],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["ritual"].tags)
    out: list[QAItem] = []
    for tag in ["frequency", "repetition", "kindness", "teamwork", "gramma", "pirate"]:
        if tag in tags or tag in {"frequency", "repetition", "kindness", "teamwork", "gramma", "pirate"}:
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

# -----------------------------------------------------------------------------
# Trace
# -----------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  frequency: {world.frequency_word} ({world.frequency_n})")
    return "\n".join(lines)

# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
% The ritual becomes burdensome when it repeats many times.
burdensome(R) :- frequency_word(R), repeats(R,N), N >= 3.

% Gramma helps when the repeated job is burdensome.
needs_kindness(R) :- burdensome(R).
needs_teamwork(R) :- burdensome(R).

% A happy tale exists when kindness and teamwork are both available.
happy_story(R) :- needs_kindness(R), needs_teamwork(R), helper(H), gramma(G).

#show happy_story/1.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, ritual in RITUALS.items():
        lines.append(asp.fact("ritual", rid))
        lines.append(asp.fact("frequency_word", ritual.keyword))
    for word, n in FREQUENCIES.items():
        lines.append(asp.fact("repeats", word, n))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
    lines.append(asp.fact("gramma", "gramma"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program("#show happy_story/1."), models=1)
    py_ok = any(FREQUENCIES[w] >= 3 for w in FREQUENCIES)
    asp_ok = bool(models)
    if py_ok == asp_ok:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP and Python do not agree.")
    return 1

# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale story world about gramma, frequency, repetition, kindness, and teamwork.")
    ap.add_argument("--ritual", choices=sorted(RITUALS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--frequency", choices=sorted(FREQUENCIES))
    ap.add_argument("--hero-name")
    ap.add_argument("--gramma-name", default="Gramma Rose")
    ap.add_argument("--captain-name", default="Cap'n Reed")
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
    ritual = args.ritual or rng.choice(sorted(RITUALS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    prize = args.prize or rng.choice(sorted(PRIZES))
    frequency = args.frequency or choose_frequency_word(rng)
    hero_name = args.hero_name or rng.choice(CREW_NAMES)
    return StoryParams(
        ritual=ritual,
        helper=helper,
        prize=prize,
        hero_name=hero_name,
        gramma_name=args.gramma_name,
        captain_name=args.captain_name,
        frequency=frequency,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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

CURATED = [
    StoryParams(ritual="bell", helper="song", prize="flag", hero_name="Mira", gramma_name="Gramma Rose", captain_name="Cap'n Reed", frequency="again and again"),
    StoryParams(ritual="sort", helper="lantern", prize="box", hero_name="Pip", gramma_name="Gramma June", captain_name="Cap'n Sable", frequency="often"),
]

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_story/1."))
        print(f"{len(model)} shown atoms")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
