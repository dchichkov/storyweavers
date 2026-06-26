#!/usr/bin/env python3
"""
A standalone story world for a small Animal Story domain:
a curious animal in the country notices crocus flowers, follows foreshadowing
clues, and helps solve a gentle mystery.

The world is built around:
- curiosity as the main emotional drive
- foreshadowing as early clue-state
- mystery as a problem that can be resolved by observation and action

This script follows the Storyweavers world contract:
- self-contained stdlib storyworld script
- shared result containers imported eagerly
- lazy ASP import inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
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
        female = {"doe", "girl", "mother", "aunt", "sister"}
        male = {"buck", "boy", "father", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)
    near: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    question: str
    clue_words: set[str]
    solution_word: str
    suspicious_place: str
    hidden_thing: str
    requires: set[str] = field(default_factory=set)


@dataclass
class Foreshadow:
    id: str
    sign: str
    clue: str
    hints: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    mystery: Optional[Mystery] = None
    foreshadowing: list[Foreshadow] = field(default_factory=list)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        return World(
            place=self.place,
            entities=_copy.deepcopy(self.entities),
            mystery=_copy.deepcopy(self.mystery),
            foreshadowing=_copy.deepcopy(self.foreshadowing),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=_copy.deepcopy(self.facts),
        )


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_kind: str
    companion: str
    mystery: str
    seed: Optional[int] = None


PLACES = {
    "country_lane": Place(
        name="the country lane",
        affords={"walk", "look", "search"},
        near={"hedge", "pond", "field", "gate"},
    ),
    "country_garden": Place(
        name="the country garden",
        affords={"walk", "look", "search"},
        near={"hedge", "crocus_patch", "shed", "well"},
    ),
    "orchard": Place(
        name="the orchard",
        affords={"walk", "look", "search"},
        near={"tree", "barrel", "fence"},
    ),
}

HEROES = {
    "rabbit": ("rabbit", "curious", "little rabbit"),
    "fox": ("fox", "clever", "small fox"),
    "hedgehog": ("hedgehog", "careful", "round hedgehog"),
    "mouse": ("mouse", "bright-eyed", "tiny mouse"),
}

COMPANIONS = {
    "sparrow": ("sparrow", "helpful"),
    "turtle": ("turtle", "slow and steady"),
    "goat": ("goat", "kind"),
    "cat": ("cat", "soft-footed"),
}

MYSTERIES = {
    "missing_bell": Mystery(
        id="missing_bell",
        title="The Missing Bell",
        question="Who took the small bell from the country gate?",
        clue_words={"bell", "gate", "shiny"},
        solution_word="nest",
        suspicious_place="hedge",
        hidden_thing="the small bell",
        requires={"search", "look"},
    ),
    "crocus_path": Mystery(
        id="crocus_path",
        title="The Crocus Path",
        question="Why were the crocus flowers opening one by one along the path?",
        clue_words={"crocus", "path", "opening"},
        solution_word="sunlight",
        suspicious_place="field",
        hidden_thing="the crocus flowers",
        requires={"look", "walk"},
    ),
    "lost_seedbag": Mystery(
        id="lost_seedbag",
        title="The Lost Seed Bag",
        question="Where did the packet of seeds go in the country garden?",
        clue_words={"seeds", "packet", "garden"},
        solution_word="shed",
        suspicious_place="shed",
        hidden_thing="the seed packet",
        requires={"search", "look"},
    ),
}

FORESHADOWINGS = {
    "soft_wind": Foreshadow(
        id="soft_wind",
        sign="A soft wind kept brushing the grass.",
        clue="The grass leaned the same way again and again.",
        hints={"field", "path", "sunlight"},
    ),
    "blue_wings": Foreshadow(
        id="blue_wings",
        sign="A blue-winged bird darted over the hedge.",
        clue="It glanced down toward something hidden below.",
        hints={"hedge", "nest", "bell"},
    ),
    "yellow_petals": Foreshadow(
        id="yellow_petals",
        sign="A row of yellow petals showed near the lane.",
        clue="They pointed the way like tiny lanterns.",
        hints={"crocus", "path", "sunlight"},
    ),
    "scratch_marks": Foreshadow(
        id="scratch_marks",
        sign="There were little scratch marks by the shed door.",
        clue="Something small had been busy there earlier.",
        hints={"shed", "seeds", "packet"},
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mystery_id in MYSTERIES:
            if mystery_id == "crocus_path" and place_id not in {"country_lane", "country_garden", "orchard"}:
                continue
            combos.append((place_id, mystery_id))
    return combos


def hero_name_options(hero_kind: str) -> list[str]:
    return {
        "rabbit": ["Pip", "Tilly", "Nip", "Mabel"],
        "fox": ["Nia", "Roux", "Fenn", "Sable"],
        "hedgehog": ["Dot", "Moss", "Prickle", "Tansy"],
        "mouse": ["Mina", "Tib", "Lumi", "Peep"],
    }.get(hero_kind, ["Pip"])


def companion_name_options(companion_kind: str) -> list[str]:
    return {
        "sparrow": ["Beep", "Sky", "Chirp"],
        "turtle": ["Tuck", "Shell", "Milo"],
        "goat": ["Glen", "Merri", "Puff"],
        "cat": ["Flick", "Wisp", "Penny"],
    }.get(companion_kind, ["Beep"])


def make_world(place_id: str, hero_kind: str, companion_kind: str, mystery_id: str) -> World:
    world = World(place=PLACES[place_id])
    hero_type, hero_trait, hero_label = HEROES[hero_kind]
    comp_type, comp_trait = COMPANIONS[companion_kind]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_label,
        meters={"curiosity": 0.0, "confidence": 0.0, "worry": 0.0},
        memes={"curiosity": 0.0, "wonder": 0.0, "resolve": 0.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=comp_type,
        label=f"the {comp_type}",
        meters={"help": 0.0, "worry": 0.0},
        memes={"kindness": 0.0, "trust": 0.0},
    ))
    mystery = MYSTERIES[mystery_id]
    world.mystery = mystery
    world.facts.update(hero=hero, companion=companion, mystery=mystery, hero_kind=hero_kind, companion_kind=companion_kind)

    # Start with one foreshadowing clue and one extra clue that may or may not matter.
    if mystery_id == "crocus_path":
        world.foreshadowing.append(FORESHADOWINGS["yellow_petals"])
        world.foreshadowing.append(FORESHADOWINGS["soft_wind"])
    elif mystery_id == "missing_bell":
        world.foreshadowing.append(FORESHADOWINGS["blue_wings"])
        world.foreshadowing.append(FORESHADOWINGS["soft_wind"])
    else:
        world.foreshadowing.append(FORESHADOWINGS["scratch_marks"])
        world.foreshadowing.append(FORESHADOWINGS["yellow_petals"])
    return world


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero kind.")
    if params.companion not in COMPANIONS:
        raise StoryError("Unknown companion kind.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.hero == params.companion:
        raise StoryError("The hero and companion should be different kinds for this story.")
    if params.mystery == "crocus_path" and params.place not in {"country_lane", "country_garden", "orchard"}:
        raise StoryError("The crocus mystery needs an outdoor country place.")


def predict_solution(world: World) -> bool:
    sim = world.copy()
    return solve_mystery(sim, narrate=False)


def r_curiosity(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("curiosity", world.mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["search"] = hero.meters.get("search", 0.0) + 1
    out.append(f"{hero.label.capitalize()} could not ignore the clues and began to look more closely.")
    return out


def r_foreshadow(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    for clue in world.foreshadowing:
        sig = ("foreshadow", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["notice"] = hero.meters.get("notice", 0.0) + 1
        out.append(clue.sign + " " + clue.clue)
    return out


def r_reveal(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    mystery = world.mystery
    if hero.meters.get("notice", 0.0) < THRESHOLD or hero.meters.get("search", 0.0) < THRESHOLD:
        return out
    sig = ("reveal", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["confidence"] = hero.meters.get("confidence", 0.0) + 1
    out.append(f"The clues fit together at last.")
    return out


def r_solve(world: World) -> list[str]:
    hero = world.get("hero")
    companion = world.get("companion")
    mystery = world.mystery
    if hero.meters.get("confidence", 0.0) < THRESHOLD:
        return []
    if ("solve", mystery.id) in world.fired:
        return []
    world.fired.add(("solve", mystery.id))
    hero.memes["resolve"] += 1
    companion.memes["trust"] += 1
    return [f"__solved__"]


CAUSAL_RULES = [
    r_curiosity,
    r_foreshadow,
    r_reveal,
    r_solve,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__solved__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solve_mystery(world: World, narrate: bool = True) -> bool:
    hero = world.get("hero")
    companion = world.get("companion")
    mystery = world.mystery
    if mystery is None:
        raise StoryError("No mystery loaded.")
    if mystery.id == "crocus_path":
        hero.memes["curiosity"] += 1
        world.say(f"{hero.label.capitalize()} noticed the crocus flowers first and wanted to know why they were there.")
        world.say(f"The {world.place.name} was bright, but the line of crocus blooms looked like a message.")
        world.say(f"{companion.label.capitalize()} stayed close, because some messages are easy to miss.")
        propagate(world, narrate=narrate)
        if mystery.solution_word == "sunlight":
            world.say("In the end, the little flowers were opening toward the warm sunlight, one by one.")
            return True
        return False

    if mystery.id == "missing_bell":
        hero.memes["curiosity"] += 1
        world.say(f"{hero.label.capitalize()} heard about the missing bell and followed the shiny clues near the hedge.")
        world.say(f"{companion.label.capitalize()} pointed at a fluttering bird and a tucked-away nest.")
        propagate(world, narrate=narrate)
        world.say("The bell had been carried into a nest to make a bright, tinkly home.")
        return True

    if mystery.id == "lost_seedbag":
        hero.memes["curiosity"] += 1
        world.say(f"{hero.label.capitalize()} sniffed around the country garden and noticed scratch marks by the shed.")
        world.say(f"{companion.label.capitalize()} peered under a little shelf where something brown and square was hiding.")
        propagate(world, narrate=narrate)
        world.say("The seed packet had slid behind a sack in the shed and was waiting to be found.")
        return True

    return False


def intro(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    mystery = world.mystery
    world.say(f"Once in the {world.place.name}, {hero.label} met {companion.label} on a day that felt full of questions.")
    world.say(f"{hero.label.capitalize()} was the sort of little {hero.type} who liked to ask what, why, and where.")
    world.say(f"Nearby, something in the country scene hinted that a mystery was waiting to be solved.")


def middle(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    mystery = world.mystery
    world.para()
    if mystery.id == "crocus_path":
        world.say(f"Along the lane, crocus petals opened in a neat line, as if the ground itself were pointing the way.")
    elif mystery.id == "missing_bell":
        world.say(f"Near the hedge, the quiet felt strange, and the missing bell left a small empty shape in the morning.")
    else:
        world.say(f"In the garden, a little gap by the shed made the space feel less tidy than before.")
    world.say(f"{hero.label.capitalize()} wanted to look closer, and {companion.label} agreed to follow.")
    solve_mystery(world, narrate=True)


def ending(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    mystery = world.mystery
    world.para()
    if mystery.id == "crocus_path":
        world.say(f"At last, the crocus flowers made sense: they were turning to the sunlight, just as living things do.")
        world.say(f"{hero.label.capitalize()} smiled at the tidy row of blooms and walked home with a lighter step.")
    elif mystery.id == "missing_bell":
        world.say(f"The bell was safe again, and the hedge no longer looked secretive.")
        world.say(f"{hero.label.capitalize()} and {companion.label} left the country lane with a happy answer in mind.")
    else:
        world.say(f"The seed packet was found, and the garden could grow what it had been waiting to grow.")
        world.say(f"{hero.label.capitalize()} and {companion.label} stood beside the shed, pleased that the mystery had a clear end.")
    hero.memes["worry"] = 0.0
    companion.memes["worry"] = 0.0


def tell_story(params: StoryParams) -> World:
    reasonableness_gate(params)
    hero_kind = params.hero
    companion_kind = params.companion
    world = make_world(params.place, hero_kind, companion_kind, params.mystery)
    intro(world)
    middle(world)
    ending(world)
    world.facts.update(solved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    m = world.mystery
    return [
        f'Write a short Animal Story about {world.place.name} with crocus flowers and a mystery to solve.',
        f"Tell a gentle story where a curious {world.get('hero').type} follows foreshadowing clues and solves {m.title}.",
        f'Write a child-friendly story that uses the words "crocus" and "country" and ends with a clear answer to a mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    companion = world.get("companion")
    m = world.mystery
    place = world.place.name
    qa = [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"The story was about a curious little {hero.type} named {hero.label} and {companion.label}.",
        ),
        QAItem(
            question=f"What mystery did {hero.label} help solve?",
            answer=f"{hero.label.capitalize()} helped solve {m.title.lower()}: {m.question}",
        ),
        QAItem(
            question=f"What clue first made the story feel like a mystery?",
            answer=f"The first clue was one of the foreshadowing signs, which helped {hero.label} notice that something important was hidden nearby.",
        ),
    ]
    if m.id == "crocus_path":
        qa.append(QAItem(
            question="Why were the crocus flowers opening one by one?",
            answer="They were turning toward the sunlight, so the flowers opened little by little in the country air.",
        ))
    if world.facts.get("solved"):
        qa.append(QAItem(
            question=f"How did the story end after {hero.label} understood the clues?",
            answer=f"{hero.label.capitalize()} solved the mystery and left the {world.place.name} with a happy answer instead of confusion.",
        ))
    return qa


KNOWLEDGE = {
    "crocus": [
        QAItem(
            question="What is a crocus?",
            answer="A crocus is a small flower that often blooms early in spring.",
        )
    ],
    "country": [
        QAItem(
            question="What does the word country mean in a story?",
            answer="In a story, the country usually means open land away from a busy city, with fields, paths, and quiet places.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions and learn more.",
        )
    ],
    "foreshadowing": [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue early on that hints at what may happen later.",
        )
    ],
    "mystery": [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question or secret in a story that characters try to figure out.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["crocus"])
    out.extend(KNOWLEDGE["country"])
    out.extend(KNOWLEDGE["curiosity"])
    out.extend(KNOWLEDGE["foreshadowing"])
    out.extend(KNOWLEDGE["mystery"])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {e.type:10} {' '.join(bits)}")
    lines.append(f"  mystery: {world.mystery.id if world.mystery else 'none'}")
    lines.append(f"  foreshadowing: {[f.id for f in world.foreshadowing]}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solved when the hero notices clues, searches, and the clues fit.
curious(H) :- curiosity(H).
notices(H, C) :- curious(H), clue(C).
foreshadows(C) :- clue(C).
has_mystery(M) :- mystery(M).
can_solve(M) :- has_mystery(M), curious(hero).

% crocus_path is compatible with country places and sunlight.
valid_story(P, M) :- place(P), mystery(M), compatible(P, M).

compatible(country_lane, crocus_path).
compatible(country_garden, crocus_path).
compatible(orchard, crocus_path).
compatible(country_lane, missing_bell).
compatible(country_garden, lost_seedbag).
compatible(orchard, missing_bell).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    lines.append(asp.fact("curiosity", "hero"))
    for cid in FORESHADOWINGS:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
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
    ap = argparse.ArgumentParser(description="Animal Story world: crocus, country, curiosity, foreshadowing, mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero = args.hero or rng.choice(list(HEROES))
    companion = args.companion or rng.choice([c for c in COMPANIONS if c != hero])
    params = StoryParams(place=place, hero=hero, hero_kind=hero, companion=companion, mystery=mystery)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="country_garden", hero="rabbit", hero_kind="rabbit", companion="sparrow", mystery="crocus_path"),
    StoryParams(place="country_lane", hero="mouse", hero_kind="mouse", companion="cat", mystery="missing_bell"),
    StoryParams(place="orchard", hero="hedgehog", hero_kind="hedgehog", companion="goat", mystery="lost_seedbag"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.hero} with {p.companion} at {p.place} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
