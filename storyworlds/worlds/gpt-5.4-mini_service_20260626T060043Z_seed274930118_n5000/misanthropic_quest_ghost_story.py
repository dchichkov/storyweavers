#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/misanthropic_quest_ghost_story.py
==============================================================================================================

A small story world built from a Ghost Story premise: a lonely, misanthropic
ghost guards a quest item, learns to trust a child, and ends by changing the
shape of the haunted place.

The simulated domain is intentionally small:
- one haunted place
- one quest object
- one child or sibling explorer
- one misanthropic ghost who starts out unwilling to help

The story is driven by world state:
- the ghost's mood and trust can change
- the quest item can be hidden, found, carried, or handed over
- the haunting can block a path until the right turn happens

The prose should read like a complete tiny tale, with:
beginning -> tension -> turn -> resolution.
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


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    darkness: float = 0.0
    damp: float = 0.0
    echo: float = 0.0
    guarded: bool = True


@dataclass
class Quest:
    id: str
    label: str
    phrase: str
    hidden_spot: str
    clue: str
    reveals: str
    needs_kindness: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy
        w = World(copy.deepcopy(self.place))
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "attic": Place(id="attic", label="the attic", darkness=2.0, damp=0.5, echo=1.5, guarded=True),
    "hall": Place(id="hall", label="the old hall", darkness=1.2, damp=0.2, echo=1.1, guarded=True),
    "tower": Place(id="tower", label="the broken tower", darkness=2.3, damp=0.6, echo=2.0, guarded=True),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        hidden_spot="under a loose floorboard",
        clue="a thin ribbon of light",
        reveals="the way across the dark room",
    ),
    "map": Quest(
        id="map",
        label="map",
        phrase="a folded map with a red X",
        hidden_spot="inside a dusty book",
        clue="a page that felt strangely warm",
        reveals="the stairs to the secret door",
    ),
    "key": Quest(
        id="key",
        label="key",
        phrase="an iron key with a moon shape",
        hidden_spot="behind a cracked portrait",
        clue="a cold spot on the wall",
        reveals="the chest at the end of the hall",
    ),
}

HERO_NAMES = ["Mina", "Owen", "Lila", "Theo", "Iris", "Ben", "Mara", "Finn"]
TRAITS = ["careful", "brave", "quiet", "curious", "gentle", "stubborn"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Style and narrative helpers
# ---------------------------------------------------------------------------
def article(text: str) -> str:
    return "an " + text if text[:1].lower() in "aeiou" else "a " + text


def setting_line(place: Place) -> str:
    if place.id == "attic":
        return "The attic smelled of old wood and dust, and every board answered with a small creak."
    if place.id == "hall":
        return "The hall was long and pale, with moonlight slipping over the walls like spilled milk."
    return "The broken tower leaned over the dark ground, and its stones kept whispering to themselves."


def mood_word(value: float) -> str:
    if value <= 0.5:
        return "soft"
    if value <= 1.5:
        return "uneasy"
    return "heavy"


def ghost_intro(world: World, ghost: Entity) -> None:
    world.say(
        f"{ghost.id} was a misanthropic ghost who did not like footsteps, chatter, or cheerful visitors."
    )
    world.say(
        f"{ghost.pronoun('subject').capitalize()} drifted through {world.place.label} with {ghost.noun()} mood and a very cold patience."
    )


def quest_intro(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} came to {world.place.label} because of {article(quest.label)} quest: find {quest.phrase}."
    )
    world.say(
        f"The only clue was {quest.clue}, and everyone said it was hidden {quest.hidden_spot}."
    )


def seek_clue(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.place.echo += 0.2
    world.say(
        f"{hero.id} listened carefully and followed {quest.clue}, because {hero.pronoun('subject')} knew every quest began with a small clue."
    )


def ghost_blocks(world: World, ghost: Entity, hero: Entity) -> None:
    ghost.memes["misanthropy"] = ghost.memes.get("misanthropy", 2.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"The ghost floated in front of {hero.id} and muttered, 'Go away. This place is for silence, not visitors.'"
    )
    world.say(
        f"The room grew colder, and {hero.id} had to hold still and think."
    )


def reveal_item(world: World, quest: Quest, hero: Entity, ghost: Entity) -> None:
    world.say(
        f"Then {hero.id} noticed {quest.clue} near {quest.hidden_spot}."
    )
    world.say(
        f"That was enough to find {quest.phrase}, but the ghost was still guarding the way out."
    )


def kindness_turn(world: World, hero: Entity, ghost: Entity, quest: Quest) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    ghost.memes["trust"] = ghost.memes.get("trust", 0.0) + 1.0
    ghost.memes["misanthropy"] = max(0.0, ghost.memes.get("misanthropy", 0.0) - 1.5)
    world.place.darkness = max(0.0, world.place.darkness - 0.7)
    world.place.guardd = False  # harmless typo? avoid
    world.say(
        f"Instead of running, {hero.id} spoke kindly and said, 'I only came for the quest item. I do not want to break your home.'"
    )
    world.say(
        f"The ghost blinked. No one had spoken to {ghost.id} that gently in a long time."
    )


def resolve(world: World, hero: Entity, ghost: Entity, quest: Quest) -> None:
    quest_item = world.get("quest_item")
    quest_item.carried_by = hero.id
    quest_item.hidden_in = ""
    ghost.memes["trust"] = ghost.memes.get("trust", 0.0) + 1.0
    ghost.memes["misanthropy"] = max(0.0, ghost.memes.get("misanthropy", 0.0) - 1.0)
    world.place.darkness = max(0.0, world.place.darkness - 0.8)
    world.place.guarded = False
    world.say(
        f"The ghost stepped aside, and {hero.id} lifted {quest.phrase} at last."
    )
    world.say(
        f"{hero.id} thanked the ghost, and the ghost gave a small nod instead of a growl."
    )
    world.say(
        f"By the end, the old place felt less cold, and the quest was no longer hidden."
    )


def tell(place: Place, quest: Quest, hero_name: str, hero_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"hope": 0.0, "worry": 0.0, "kindness": 0.0}))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost", memes={"misanthropy": 2.0, "trust": 0.0}))
    item = world.add(Entity(id="quest_item", kind="thing", type=quest.label, label=quest.label, phrase=quest.phrase, hidden_in=quest.hidden_spot))
    world.facts.update(hero=hero, ghost=ghost, item=item, quest=quest, place=place, trait=trait)

    ghost_intro(world, ghost)
    world.para()
    world.say(setting_line(place))
    quest_intro(world, hero, quest)
    seek_clue(world, hero, quest)
    ghost_blocks(world, ghost, hero)
    world.para()
    reveal_item(world, quest, hero, ghost)
    kindness_turn(world, hero, ghost, quest)
    resolve(world, hero, ghost, quest)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasonability gate
# ---------------------------------------------------------------------------
def valid_combo(place: Place, quest: Quest) -> bool:
    return place.darkness >= 1.0 and place.guarded and quest.needs_kindness


def valid_combos() -> list[tuple[str, str]]:
    return [(pid, qid) for pid, p in PLACES.items() for qid, q in QUESTS.items() if valid_combo(p, q)]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, place = f["hero"], f["quest"], f["place"]
    return [
        f'Write a short ghost story for a child about {hero.id} and a quest for {quest.label} in {place.label}.',
        f'Tell a spooky-but-kind tale where a misanthropic ghost blocks a quest until {hero.id} speaks gently.',
        f'Write a simple story set in {place.label} that ends with {quest.phrase} being found and the ghost softening.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ghost, quest, place = f["hero"], f["ghost"], f["quest"], f["place"]
    return [
        QAItem(
            question=f"Who came to {place.label} for the quest?",
            answer=f"{hero.id} came to {place.label} to find {quest.phrase}.",
        ),
        QAItem(
            question="Why was the ghost hard to approach?",
            answer="The ghost was misanthropic, so it did not like visitors and wanted to be left alone.",
        ),
        QAItem(
            question=f"What was the clue for finding {quest.label}?",
            answer=f"The clue was {quest.clue}, which led to {quest.hidden_spot}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"The ghost became less cold and let {hero.id} take {quest.phrase} instead of guarding it forever.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spooky character that may drift through walls, whisper, and guard a place or treasure in a story.",
        ),
        QAItem(
            question="What does misanthropic mean?",
            answer="Misanthropic means someone dislikes people and does not want to spend time with them.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to find something important, like a treasure, key, or map.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- quest_item(Q).

valid_story(P,Q) :- setting(P), quest_item(Q), dark(P), guarded(P), kind_required(Q).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.darkness >= 1.0:
            lines.append(asp.fact("dark", pid))
        if p.guarded:
            lines.append(asp.fact("guarded", pid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest_item", qid))
        if q.needs_kindness:
            lines.append(asp.fact("kind_required", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(python_set - asp_set))
    print("only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny ghost-story quest world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place_id, quest_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place_id, quest=quest_id, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], params.name, "girl" if params.gender == "girl" else "boy", params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    lines.append(f"place={world.place.label} darkness={world.place.darkness} damp={world.place.damp} echo={world.place.echo} guarded={world.place.guarded}")
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"{e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="attic", quest="lantern", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="hall", quest="map", name="Theo", gender="boy", trait="quiet"),
    StoryParams(place="tower", quest="key", name="Iris", gender="girl", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

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
