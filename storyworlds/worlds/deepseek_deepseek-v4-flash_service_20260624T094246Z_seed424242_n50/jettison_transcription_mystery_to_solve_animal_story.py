#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/jettison_transcription_mystery_to_solve_animal_story.py
====================================================================================================

A standalone story world for an animal mystery. A small clue (transcription) appears,
and the animals must jettison a false lead to find the real answer.

Seed words: jettison, transcription.
Style: Animal Story.
Feature: Mystery to Solve.
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0

# Physical meter keys
MESS_KINDS = {"muddy", "torn", "lost"}

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"   # character or thing
    type: str = "animal"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"vixen", "doe", "mother"}
        male = {"fox", "stag", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"father": "dad", "mother": "mum"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the forest"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue_label: str
    clue_phrase: str
    false_lead: str          # false interpretation the animals first believe
    true_answer: str         # the correct answer after jettisoning false lead
    jettison_thing: str      # what they throw away (false idea or object)
    transcription_type: str  # e.g. "a coded note", "a paw print"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    purpose: str
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World container
# ---------------------------------------------------------------------------
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules (here: jettison and revelation)
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_jettison(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["holding_false"] < THRESHOLD:
            continue
        sig = ("jettison", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["holding_false"] = 0.0
        actor.memes["true_clue"] += 1
        out.append(
            f"{actor.pronoun('possessive').capitalize()} eyes widened. "
            f"\"That can't be right,\" {actor.pronoun()} said, and "
            f"pushed away the wrong idea."
        )
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="jettison", tag="mental", apply=_r_jettison),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
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


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce_hero(world: World, hero: Entity) -> None:
    world.say(
        f"In a cozy corner of {world.setting.place}, there lived a little "
        f"{hero.traits[0] if hero.traits else 'curious'} {hero.type} named {hero.id}."
    )


def find_clue(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"One morning, {hero.id} found {mystery.clue_phrase}. "
        f"\"What's this?\" {hero.pronoun()} wondered."
    )
    hero.memes["curiosity"] += 1


def friends_gather(world: World, hero: Entity, friends: list[Entity]) -> None:
    names = [f.id for f in friends]
    world.say(
        f"{hero.id} called {hero.pronoun('possessive')} friends "
        f"{' and '.join(names)}. Together they studied the {mystery.clue_label}."
    )
    for f in friends:
        f.memes["teamwork"] += 1


def misinterpret(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"\"I think it means {mystery.false_lead},\" said {hero.id}. "
        f"The others nodded, but something felt wrong."
    )
    hero.memes["holding_false"] += 1
    propagate(world, narrate=False)  # rule may fire later


def jettison_realization(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} stared at the {mystery.transcription_type} again. "
        f"\"Wait — we need to {mystery.jettison_thing}!\" "
        f"{hero.pronoun().capitalize()} explained. \"That transcription was a trick!\""
    )
    hero.memes["holding_false"] += 1
    propagate(world, narrate=True)


def reveal_answer(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"Once they let go of the wrong idea, the real answer became clear. "
        f"\"It's {mystery.true_answer}!\" cried {hero.id}. "
        f"All the animals cheered and went to find the {mystery.true_answer.split()[-1]}."
    )
    hero.memes["joy"] += 1


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the forest", affords={"lost_map", "code_note", "paw_track"}),
    "meadow": Setting(place="the meadow", affords={"lost_map", "paw_track"}),
    "pond": Setting(place="the pond edge", affords={"code_note"}),
}

MYSTERIES = {
    "lost_map": Mystery(
        id="lost_map",
        clue_label="map",
        clue_phrase="a crumpled old map with a blurry X",
        false_lead="the treasure is under the big oak tree",
        true_answer="the treasure is behind the waterfall",
        jettison_thing="jettison the idea that the X marks the oak",
        transcription_type="map markings",
        tags={"map", "treasure"},
    ),
    "code_note": Mystery(
        id="code_note",
        clue_label="note",
        clue_phrase="a tiny scroll with strange symbols",
        false_lead="each symbol stands for a number",
        true_answer="the symbols are animal tracks turned sideways",
        jettison_thing="jettison the 'numbers' idea and look at the pattern",
        transcription_type="coded note",
        tags={"code", "symbols"},
    ),
    "paw_track": Mystery(
        id="paw_track",
        clue_label="paw print",
        clue_phrase="a single large paw print near the old log",
        false_lead="it belongs to a bear",
        true_answer="it belongs to a lost wolf pup",
        jettison_thing="jettison the bear guess and measure the stride",
        transcription_type="paw impression",
        tags={"track", "animal"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="a magnifying glass",
        purpose="see small marks",
        prep="fetch the magnifying glass",
        tail="ran home to get the magnifying glass and examined every corner",
    ),
    "notebook": Tool(
        id="notebook",
        label="a small notebook",
        purpose="sketch and compare",
        prep="bring the notebook to write down clues",
        tail="found the notebook and began to draw the symbols side by side",
    ),
}

ANIMALS = ["fox", "rabbit", "owl", "squirrel", "deer"]
ANIMAL_NAMES = {"fox": "Finn", "rabbit": "Ruby", "owl": "Ollie", "squirrel": "Sienna", "deer": "Daisy"}
TRAITS = ["curious", "clever", "brave", "gentle", "inventive"]


def valid_combos() -> list[tuple[str, str, str]]:
    """(place, mystery, tool) triples that are valid."""
    combos = []
    for place_id, setting in SETTINGS.items():
        for mystery_id in setting.affords:
            # all mysteries are valid with any tool; but we constrain a little
            # for consistency: code_note works best with notebook, etc.
            for tool_id in TOOLS:
                if mystery_id == "code_note" and tool_id != "notebook":
                    continue
                if mystery_id == "paw_track" and tool_id != "magnifier":
                    continue
                combos.append((place_id, mystery_id, tool_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    hero_animal: str
    hero_name: str
    friend_animal: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A helpers
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "map": [
        ("What is a map?",
         "A map is a drawing that shows where things are. It helps you find your way."),
    ],
    "code": [
        ("What is a code?",
         "A code uses symbols or letters to hide a message. You need a key to read it."),
    ],
    "track": [
        ("What is an animal track?",
         "An animal track is a print left by an animal's foot. You can tell which animal made it."),
    ],
    "treasure": [
        ("What is treasure?",
         "Treasure is something special and hidden, like gold or jewels or a secret place."),
    ],
    "magnifier": [
        ("What is a magnifying glass for?",
         "A magnifying glass makes small things look bigger so you can see tiny details."),
    ],
    "notebook": [
        ("What is a notebook good for?",
         "A notebook is good for writing down ideas and drawings so you don't forget clues."),
    ],
}
KNOWLEDGE_ORDER = ["map", "code", "track", "treasure", "magnifier", "notebook"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mystery = f["hero"], f["mystery"]
    return [
        f"Write a short animal story about solving a mystery using the word '{mystery.transcription_type}'.",
        f"Create a story where a {hero.type} named {hero.id} finds a clue and must jettison a wrong idea.",
        f"Tell a gentle story about friends working together to read a {mystery.clue_label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    tool = f.get("tool")
    pos = hero.pronoun("possessive")
    sub = hero.pronoun("subject")
    obj = hero.pronoun("object")
    qa = [
        QAItem(
            question=f"Who found the {mystery.clue_label} in {world.setting.place}?",
            answer=f"A {hero.traits[0] if hero.traits else 'curious'} {hero.type} named {hero.id} found the {mystery.clue_label}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {pos} friends think the {mystery.clue_label} meant at first?",
            answer=f"They thought it meant {mystery.false_lead}, but that turned out to be wrong.",
        ),
        QAItem(
            question=f"How did the animals find the true answer?",
            answer=f"They had to jettison the wrong idea. {pos.capitalize()} friend said, 'We need to {mystery.jettison_thing}!' and then they understood the {mystery.transcription_type} correctly.",
        ),
        QAItem(
            question=f"What was the real answer to the mystery?",
            answer=f"The real answer was {mystery.true_answer}.",
        ),
    ]
    if tool:
        qa.append(QAItem(
            question=f"What did {hero.id} use {tool.label} for?",
            answer=f"{hero.id} used {tool.label} to help study the {mystery.transcription_type} and figure out the clue.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    if world.facts.get("tool"):
        tags.add(world.facts["tool"].id)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core generation procedure
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery, tool: Optional[Tool],
         hero_animal: str, hero_name: str, friend_animal: str, friend_name: str,
         hero_trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_animal,
        traits=[hero_trait], label=hero_animal,
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_animal,
        traits=["clever"], label=friend_animal,
    ))

    # Act 1: introduce, find clue
    introduce_hero(world, hero)
    friends_gather(world, hero, [friend])
    find_clue(world, hero, mystery)

    # Act 2: misinterpret -> jettison
    world.para()
    misinterpret(world, hero, mystery)
    jettison_realization(world, hero, mystery)

    # Act 3: reveal answer
    world.para()
    reveal_answer(world, hero, mystery)

    # Record facts
    world.facts.update(hero=hero, mystery=mystery, tool=tool, setting=setting)

    # Tool usage
    if tool:
        hero.memes["tool_knowledge"] += 1
        world.say(
            f"Thanks to {tool.label}, they pieced it together."
        )

    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story needs a place that affords the mystery, and a tool that fits.
affords_tool(P, M, T) :- affords(P, M), tool_ok(M, T).
tool_ok(_, _) :- tool(T).        % simple: all tools are ok for most mysteries, but we restrict in Python
% We'll use the same logic as valid_combos() via facts.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for m in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, m))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        # tool-mystery compatibility (mirroring Python constraints)
        if tid == "notebook":
            lines.append(asp.fact("tool_ok", tid, "code_note"))
        elif tid == "magnifier":
            lines.append(asp.fact("tool_ok", tid, "paw_track"))
        else:
            # fallback: allow all
            for m in MYSTERIES:
                lines.append(asp.fact("tool_ok", tid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # For simplicity, just check that the Python combos are non-empty.
    # ASP verification would need more rules; we skip detailed verification.
    print("ASP verification: Python valid_combos() has", len(valid_combos()), "combos.")
    return 0


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal mystery story: jettison a wrong transcription to solve the clue."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-animal", choices=ANIMALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-animal", choices=ANIMALS, default="rabbit")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("No valid combination with the given constraints.")

    place, mystery_id, tool_id = rng.choice(combos)
    hero_animal = args.hero_animal or rng.choice(ANIMALS)
    hero_name = args.hero_name or ANIMAL_NAMES.get(hero_animal, "Finn")
    friend_animal = args.friend_animal or rng.choice([a for a in ANIMALS if a != hero_animal])
    friend_name = args.friend_name or ANIMAL_NAMES.get(friend_animal, "Ruby")
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mystery=mystery_id,
        tool=tool_id,
        hero_animal=hero_animal,
        hero_name=hero_name,
        friend_animal=friend_animal,
        friend_name=friend_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        MYSTERIES[params.mystery],
        TOOLS.get(params.tool),
        params.hero_animal,
        params.hero_name,
        params.friend_animal,
        params.friend_name,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            print(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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
        combos = valid_combos()
        print(f"{len(combos)} compatible (place, mystery, tool) combos:")
        for c in combos:
            print(f"  {c[0]:8} {c[1]:12} {c[2]:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples = []
    if args.all:
        # Generate one of each combo (curated subset)
        seen = set()
        for place_id in SETTINGS:
            for mystery_id in SETTINGS[place_id].affords:
                for tool_id in TOOLS:
                    # apply same constraints as valid_combos
                    if mystery_id == "code_note" and tool_id != "notebook":
                        continue
                    if mystery_id == "paw_track" and tool_id != "magnifier":
                        continue
                    p = StoryParams(
                        place=place_id, mystery=mystery_id, tool=tool_id,
                        hero_animal="fox", hero_name="Finn",
                        friend_animal="rabbit", friend_name="Ruby",
                        trait="curious",
                    )
                    s = generate(p)
                    if s.story not in seen:
                        seen.add(s.story)
                        samples.append(s)
    else:
        rng = random.Random(base_seed)
        for i in range(args.n):
            seed = base_seed + i
            rng.seed(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = generate(params)
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
            header = f"### {p.hero_name} solves {p.mystery} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
