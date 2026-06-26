#!/usr/bin/env python3
"""
storyworlds/worlds/jettison_transcription_mystery_to_solve_animal_story.py
=========================================================================

A standalone story world for a woodland mystery: a treasure map's transcription
is incomplete, and the characters must decide what to jettison from a leaf-boat
to solve the puzzle and reach Honey Hill before sunset.

Domain: Animal Story
Feature: Mystery to Solve
Seed words: jettison, transcription
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


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "animal"
    species: str = "mouse"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    holder: Optional[str] = None          # who carries this item
    location: str = "clearing"
    role: str = "friend"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"mouse", "squirrel", "rabbit", "hen", "deer"}
        male = {"badger", "fox", "owl", "toad", "hare"}
        if self.species in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.species in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.season: str = "autumn"
        self.time: str = "afternoon"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "item"]

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.season = self.season
        clone.time = self.time
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_jettison(world: World) -> list[str]:
    """If an item is marked for jettison, remove it from its holder."""
    out: list[str] = []
    for item in world.items():
        if item.meters["to_jettison"] >= THRESHOLD and item.holder:
            holder = world.get(item.holder)
            sig = ("jettisoned", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.holder = None
            item.location = "abandoned"
            holder.meters["load"] = max(0, holder.meters["load"] - 1)
            out.append(
                f"{holder.pronoun('possessive').capitalize()} {item.label} was "
                f"left behind, and the boat felt lighter."
            )
    return out


def _r_late_afternoon(world: World) -> list[str]:
    """As time passes, fatigue accumulates."""
    out: list[str] = []
    for animal in world.animals():
        if animal.meters["fatigue"] < THRESHOLD:
            continue
        sig = ("fatigued", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(
            f"{animal.pronoun('possessive').capitalize()} legs ached, but "
            f"{animal.pronoun()} kept going."
        )
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="jettison", apply=_r_jettison),
    Rule(name="late afternoon", apply=_r_late_afternoon),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# The Storytelling Engine
# ---------------------------------------------------------------------------
@dataclass
class Mystery:
    """The puzzle the animals must solve."""
    clue_objects: list[str]
    clue_transcription: str      # the partial copy of the map
    required_sacrifice: str      # what must be jettisoned
    solution: str                # how the mystery resolves


MYSTERIES = [
    Mystery(
        clue_objects=["a shiny acorn", "a red feather", "a crinkly leaf"],
        clue_transcription="The map said: go past the old oak, then past the mossy log",
        required_sacrifice="the heavy berry basket",
        solution="They realized the basket was too heavy and left it behind.",
    ),
    Mystery(
        clue_objects=["a pine cone", "a blue pebble", "a twisty twig"],
        clue_transcription="The copied note read: turn at the tumbled wall",
        required_sacrifice="the extra rolls of birch bark",
        solution="They set down the bark and found the path clearly ahead.",
    ),
    Mystery(
        clue_objects=["a striped snail shell", "a silver leaf", "a fuzzy caterpillar"],
        clue_transcription="The transcription said: after the mushroom ring, go east",
        required_sacrifice="the heavy stone for pressing flowers",
        solution="They jettisoned the stone and could finally climb the slope.",
    ),
]


@dataclass
class StoryParams:
    hero_species: str
    friend_species: str
    mystery_index: int
    clue_one: str
    clue_two: str
    clue_three: str
    name_hero: str
    name_friend: str
    seed: Optional[int] = None


HERO_NAMES = {
    "mouse": ["Pip", "Moss", "Whisk", "Tiny"],
    "squirrel": ["Fluff", "Chestnut", "Nibble", "Skitter"],
    "rabbit": ["Thumper", "Honey", "Dandelion", "Puff"],
}
FRIEND_NAMES = {
    "badger": ["Grumpy", "Dug", "Bruno", "Bramble"],
    "fox": ["Red", "Sly", "Rusty", "Vixen"],
    "owl": ["Hoot", "Wise", "Twilight", "Plume"],
}


def tell(params: StoryParams) -> World:
    world = World()
    mystery = MYSTERIES[params.mystery_index]

    hero = world.add(Entity(
        id=params.name_hero,
        species=params.hero_species,
        label=f"a little {params.hero_species}",
        phrase=f"a clever little {params.hero_species} named {params.name_hero}",
        traits=["curious", "brave"],
    ))
    friend = world.add(Entity(
        id=params.name_friend,
        species=params.friend_species,
        label=f"a {params.friend_species}",
        phrase=f"a wise {params.friend_species} named {params.name_friend}",
        traits=["patient", "thoughtful"],
    ))

    # Items the animals carry
    basket = world.add(Entity(
        id="basket",
        kind="item",
        label="heavy basket of berries",
        phrase="a heavy basket full of ripe berries",
        holder=hero.id,
    ))
    map_scroll = world.add(Entity(
        id="map_scroll",
        kind="item",
        label="old map with a transcription",
        phrase="an old map and its careful transcription on birch bark",
        holder=friend.id,
    ))
    bag = world.add(Entity(
        id="bag",
        kind="item",
        label="bag of extra bark rolls",
        phrase="a bag of extra birch bark rolls they had brought for notes",
        holder=friend.id,
    ))
    stone = world.add(Entity(
        id="stone",
        kind="item",
        label="heavy flower-pressing stone",
        phrase="a smooth heavy stone for pressing flower petals",
        holder=hero.id,
    ))

    # Act 1: Setup
    world.say(
        f"In a cozy woodland, {hero.phrase} found a tattered map showing the way "
        f"to Honey Hill, where the last golden berries grew before winter."
    )
    world.say(
        f"{hero.pronoun().capitalize()} ran to {friend.label} named {friend.id} "
        f"and said, \"Look what I found! A mystery to solve!\""
    )
    world.say(
        f"{friend.id} unrolled the map and began a careful transcription onto "
        f"fresh bark, copying every twist and turn."
    )

    world.para()

    # Act 2: The mystery deepens
    world.weather = "autumn"
    world.say(
        f"They packed their things into a leaf-boat and set sail down the "
        f"little stream. "
        f"{params.clue_one.capitalize()} floated past, and {hero.id} gasped."
    )
    world.say(
        f"\"That matches the transcription!\" {friend.id} chirped. "
        f"But the boat was riding low in the water."
    )

    # Mystery clue items appear
    clue1 = world.add(Entity(
        id="clue1",
        kind="item",
        label=params.clue_one,
        phrase=params.clue_one,
        location="stream",
    ))
    clue2 = world.add(Entity(
        id="clue2",
        kind="item",
        label=params.clue_two,
        phrase=params.clue_two,
        location="stream",
    ))
    clue3 = world.add(Entity(
        id="clue3",
        kind="item",
        label=params.clue_three,
        phrase=params.clue_three,
        location="stream",
    ))
    world.facts["clues_found"] = [params.clue_one, params.clue_two, params.clue_three]

    # Tension: the boat is too heavy
    hero.meters["load"] = 3
    friend.meters["load"] = 2
    world.say(
        f"\"We're too laden!\" {friend.id} cried. \"We must jettison something "
        f"or we'll never reach Honey Hill before sunset!\""
    )
    world.say(
        f"But {hero.id} looked at the {basket.label} and the {stone.label} and "
        f"the {bag.label}, and could not decide."
    )

    world.para()

    # Act 3: The turn – they puzzle over the transcription
    world.say(
        f"Then {friend.id} studied the transcription again. \"Wait! The map "
        f"mentions a {required_sacrifice}... that's what we must leave behind!\""
    )
    mystery_required = mystery.required_sacrifice
    world.say(
        f"\"{mystery_required.capitalize()}?\" {hero.id} repeated. "
        f"\"But we need it!\" A moment later, {hero.pronoun()} understood."
    )

    # Mark the correct item for jettison
    if "basket" in mystery_required:
        basket.meters["to_jettison"] = 1
    elif "bark" in mystery_required:
        bag.meters["to_jettison"] = 1
    elif "stone" in mystery_required:
        stone.meters["to_jettison"] = 1

    propagate(world)
    world.say(
        f"So {hero.id} and {friend.id} gently set {mystery_required} ashore, "
        f"promising to return for it. {mystery.solution}"
    )

    world.para()

    # Resolution
    world.say(
        f"The leaf-boat rose higher in the stream. {hero.pronoun().capitalize()} "
        f"and {friend.id} glided onward, following the clues—{params.clue_one}, "
        f"{params.clue_two}, and {params.clue_three}—until the golden berries "
        f"of Honey Hill glittered before them in the setting sun."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        mystery=mystery,
        hero_species=params.hero_species,
        friend_species=params.friend_species,
        jettisoned=mystery_required,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
GENERAL_KNOWLEDGE = {
    "jettison": [
        ("What does jettison mean?",
         "Jettison means to throw something overboard or leave it behind to "
         "make a boat or load lighter."),
    ],
    "transcription": [
        ("What is a transcription?",
         "A transcription is a written copy of something, like writing down "
         "the directions from a map onto a fresh piece of bark."),
    ],
    "mystery": [
        ("What is a mystery?",
         "A mystery is a puzzle or a secret waiting to be solved by looking "
         "for clues and using your cleverness."),
    ],
    "autumn": [
        ("What happens to leaves in autumn?",
         "In autumn, leaves turn gold and red and fall from the trees, "
         "covering the ground in a crunchy carpet."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        f"Write a short woodland animal story where {hero.species} and "
        f"{friend.species} find a map and must solve a mystery together.",
        f"Tell a gentle tale about two animal friends who have to jettison "
        f"something from their boat after reading a tricky transcription.",
        f"A story about autumn, clues, and a mystery to solve in the forest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    jettisoned = f["jettisoned"]
    clues = world.facts.get("clues_found", [])

    qa = [
        QAItem(
            question=(
                f"Who found the old map at the beginning of the story?"
            ),
            answer=(
                f"{hero.phrase} found the tattered old map showing the way "
                f"to Honey Hill."
            ),
        ),
        QAItem(
            question=(
                f"What did {friend.id} do when {hero.pronoun()} showed "
                f"{friend.pronoun('object')} the map?"
            ),
            answer=(
                f"{friend.id} did a careful transcription of the map onto "
                f"fresh birch bark so they could follow the directions."
            ),
        ),
        QAItem(
            question=(
                f"What three clues did the friends see floating in the stream?"
            ),
            answer=(
                f"They saw {clues[0]}, {clues[1]}, and {clues[2]} "
                f"floating past the leaf-boat."
            ),
        ),
        QAItem(
            question=(
                f"Why did the friends need to jettison something from the boat?"
            ),
            answer=(
                f"The boat was riding too low because they had packed too many "
                f"things. They needed to make it lighter to reach Honey Hill "
                f"before sunset."
            ),
        ),
        QAItem(
            question=(
                f"What did the {hero.species} and {friend.species} jettison "
                f"from their leaf-boat?"
            ),
            answer=(
                f"They jettisoned {jettisoned} after studying the transcription "
                f"and realizing it was the extra weight that slowed them down."
            ),
        ),
        QAItem(
            question=(
                f"Did the animals solve the mystery in the end?"
            ),
            answer=(
                f"Yes. By reading the transcription carefully and jettisoning "
                f"{jettisoned}, they solved the mystery and reached Honey Hill "
                f"just as the sun was setting."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = ["jettison", "transcription", "mystery", "autumn"]
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in GENERAL_KNOWLEDGE[tag])
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if hasattr(e, 'species'):
            bits.append(f"species={e.species}")
        lines.append(f"  {e.id:12} {e.kind:6} {' '.join(bits)}")
    lines.append(f"  fired: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid mystery story: two animals, one mystery, one jettison.
animal(mouse; squirrel; rabbit; badger; fox; owl).

mystery_item("basket"; "bark"; "stone").

% Jettison solves the weight problem
jettison_needed(M, "basket") :- mystery_item(M), M != "bark", M != "stone".
jettison_needed(M, "bark") :- mystery_item(M), M != "basket", M != "stone".
jettison_needed(M, "stone") :- mystery_item(M), M != "basket", M != "bark".

valid_story(H, F, J) :- animal(H), animal(F), H != F,
                        mystery_item(J).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for species in ["mouse", "squirrel", "rabbit", "badger", "fox", "owl"]:
        lines.append(asp.fact("animal", species))
    for item in ["basket", "bark", "stone"]:
        lines.append(asp.fact("mystery_item", item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_stories: set[tuple] = set()
    for h in ["mouse", "squirrel", "rabbit"]:
        for f in ["badger", "fox", "owl"]:
            if h == f:
                continue
            for j in ["basket", "bark", "stone"]:
                python_stories.add((h, f, j))
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_stories:
        print(f"OK: clingo matches python ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_stories:
        print("  only in clingo:", sorted(clingo_set - python_stories))
    if python_stories - clingo_set:
        print("  only in python:", sorted(python_stories - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story: Mystery to Solve")
    ap.add_argument("--hero-species", choices=["mouse", "squirrel", "rabbit"])
    ap.add_argument("--friend-species", choices=["badger", "fox", "owl"])
    ap.add_argument("--mystery", type=int, choices=[0, 1, 2])
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
    hero = args.hero_species or rng.choice(["mouse", "squirrel", "rabbit"])
    friend = args.friend_species or rng.choice(["badger", "fox", "owl"])
    if hero == friend:
        friend = {"mouse": "badger", "squirrel": "fox", "rabbit": "owl"}[hero]
    mi = args.mystery if args.mystery is not None else rng.randint(0, 2)
    mystery = MYSTERIES[mi]

    name_hero = rng.choice(HERO_NAMES[hero])
    name_friend = rng.choice(FRIEND_NAMES[friend])
    return StoryParams(
        hero_species=hero,
        friend_species=friend,
        mystery_index=mi,
        clue_one=mystery.clue_objects[0],
        clue_two=mystery.clue_objects[1],
        clue_three=mystery.clue_objects[2],
        name_hero=name_hero,
        name_friend=name_friend,
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid story combos:")
        for h, f, j in stories:
            print(f"  hero={h}, friend={f}, jettison={j}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("mouse", "badger", 0, "a shiny acorn", "a red feather", "a crinkly leaf", "Pip", "Grumpy"),
            StoryParams("squirrel", "fox", 1, "a pine cone", "a blue pebble", "a twisty twig", "Chestnut", "Red"),
            StoryParams("rabbit", "owl", 2, "a striped snail shell", "a silver leaf", "a fuzzy caterpillar", "Honey", "Hoot"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            story_text = sample.story
            if story_text in seen:
                continue
            seen.add(story_text)
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
            header = f"### {p.name_hero} and {p.name_friend}: {p.mystery_index}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
