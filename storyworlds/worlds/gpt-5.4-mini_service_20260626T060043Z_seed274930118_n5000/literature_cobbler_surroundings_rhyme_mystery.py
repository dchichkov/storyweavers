#!/usr/bin/env python3
"""
Standalone storyworld: literature + cobbler + surroundings, told as a small
mystery with rhyme woven into the prose.

A quiet cobbler notices strange clues in the shop's surroundings: a torn line of
verse, a mud print, a missing library book, and a curious sound in the lane.
The world model tracks what is found, what is guessed, and how the mystery
resolves.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "she"}
        male = {"boy", "man", "father", "dad", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    name: str
    description: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    title: str
    object_label: str
    object_phrase: str
    clue_word: str
    clue_rhyme: str
    missing_place: str
    suspect: str
    why: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace_notes: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


SETTINGS = {
    "shop": Setting(
        name="the cobbler's shop",
        description="A little cobbler's shop with a bell over the door and shelves of neat shoes.",
        indoors=True,
        affords={"search", "measure", "mend"},
    ),
    "library_lane": Setting(
        name="the library lane",
        description="A narrow lane beside the library, with brick walls, ivy, and soft evening light.",
        indoors=False,
        affords={"search", "listen", "follow"},
    ),
    "market": Setting(
        name="the market street",
        description="A busy market street with stalls, sacks, and a cobbler's bench near the curb.",
        indoors=False,
        affords={"search", "ask", "follow"},
    ),
}

MYSTERIES = {
    "lost_book": Mystery(
        id="lost_book",
        title="The Missing Book",
        object_label="book",
        object_phrase="a slim old book of poems",
        clue_word="verse",
        clue_rhyme="bright night",
        missing_place="the library shelf",
        suspect="the wind",
        why="the open window had fluttered the page loose",
        reveal="the book had slipped behind a bench, where the lantern light finally caught its blue cover",
        tags={"literature", "book", "poem"},
    ),
    "missing_page": Mystery(
        id="missing_page",
        title="The Vanished Page",
        object_label="page",
        object_phrase="a single torn page from a storybook",
        clue_word="line",
        clue_rhyme="fine line",
        missing_place="the reading table",
        suspect="the cat",
        why="a playful paw had dragged the page under the rug",
        reveal="the page was tucked under a chair leg, safe and sound",
        tags={"literature", "page", "rhyme"},
    ),
    "lost_key": Mystery(
        id="lost_key",
        title="The Tiny Key Mystery",
        object_label="key",
        object_phrase="a little brass key for the book box",
        clue_word="shine",
        clue_rhyme="near the pine",
        missing_place="the front step",
        suspect="the rain",
        why="the key had fallen while someone shook off a wet coat",
        reveal="the key gleamed in the cobbler's tray, caught beside a spool of thread",
        tags={"cobbler", "thread", "key"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lena", "Tess", "Ada", "Rosa", "Nia"],
    "boy": ["Finn", "Eli", "Owen", "Leo", "Ned", "Bram"],
}
TRAITS = ["curious", "careful", "brave", "gentle", "sharp-eyed", "quiet"]


def mystery_intro(m: Mystery) -> str:
    return f"{m.title} had a clue that liked to rhyme."


def resolve_mystery(world: World, cobbler: Entity, m: Mystery) -> None:
    if m.id == "lost_book":
        world.say(
            f"{cobbler.id} found a scrap of paper on the sill: "
            f'"{m.clue_word} and {m.clue_rhyme}," it said.'
        )
        world.say(
            f"The line was as neat as a stitched seam, and {cobbler.id} knew "
            f"this was no ordinary breeze."
        )
        world.facts["clue"] = m.clue_word
        world.facts["rhyme"] = m.clue_rhyme
        world.facts["suspect"] = m.suspect
        world.facts["reveal"] = m.reveal
        world.facts["why"] = m.why
    elif m.id == "missing_page":
        world.say(
            f"On the floor there was a tiny note: "
            f'"{m.clue_word} and {m.clue_rhyme}," it hummed like a tune.'
        )
        world.say(
            f"{cobbler.id} smiled, because a clue that sings is hard to miss."
        )
        world.facts["clue"] = m.clue_word
        world.facts["rhyme"] = m.clue_rhyme
        world.facts["suspect"] = m.suspect
        world.facts["reveal"] = m.reveal
        world.facts["why"] = m.why
    else:
        world.say(
            f"Near the bench, {cobbler.id} spotted a bright brass glimmer and a note: "
            f'"{m.clue_word} by the {m.clue_rhyme}," it chirped.'
        )
        world.say(
            f"That was enough for a cobbler's hunch; a hidden thing loves a snug little nook."
        )
        world.facts["clue"] = m.clue_word
        world.facts["rhyme"] = m.clue_rhyme
        world.facts["suspect"] = m.suspect
        world.facts["reveal"] = m.reveal
        world.facts["why"] = m.why


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, trait: str, parent: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    helper = world.add(Entity(id=parent, kind="character", type=parent, label=parent))
    cobbler = world.add(Entity(id="cobbler", kind="character", type="man", label="the cobbler"))
    obj = world.add(Entity(
        id=mystery.object_label,
        kind="thing",
        type=mystery.object_label,
        label=mystery.object_label,
        phrase=mystery.object_phrase,
        owner="library",
        location=mystery.missing_place,
    ))
    world.facts.update(hero=hero, helper=helper, cobbler=cobbler, obj=obj, mystery=mystery, trait=trait)

    world.say(f"{mystery_intro(mystery)}")
    world.say(
        f"In {setting.name}, {cobbler.id} worked by a window and listened to the street."
    )
    world.say(
        f"{name} was a {trait} {gender} who loved literature, especially when stories sounded like songs."
    )
    world.para()
    world.say(setting.description)
    world.say(
        f"Then {name} came in and said the {mystery.object_label} was missing from {mystery.missing_place}."
    )
    world.say(
        f"{helper.id} worried, but {cobbler.id} tapped the bench and said, "
        f'"When clues rhyme, the truth is close by."'
    )
    world.para()
    resolve_mystery(world, cobbler, mystery)
    if mystery.id == "lost_book":
        world.say(
            f"They checked the shelves, the step, and the strip of wall beside the door."
        )
        world.say(
            f"At last, {mystery.reveal.capitalize()}."
        )
    elif mystery.id == "missing_page":
        world.say(
            f"They looked under the rug, behind the chair, and beside the warm kettle."
        )
        world.say(
            f"At last, {mystery.reveal.capitalize()}."
        )
    else:
        world.say(
            f"They searched the tray, the string basket, and the shadow under the stool."
        )
        world.say(
            f"At last, {mystery.reveal.capitalize()}."
        )
    world.para()
    world.say(
        f"{name} laughed softly, and {cobbler.id} smiled, for the mystery had been mended."
    )
    world.say(
        f"The surroundings felt less strange now: the shelves were calm, the air was still, and the clue was no longer hiding."
    )
    world.facts["solved"] = True
    return world


def build_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    return [
        f'Write a gentle mystery for a child that features a cobbler, literature, and a clue that rhymes with "{m.clue_word}".',
        f"Tell a short story about {hero.id} and a cobbler finding {m.object_phrase} in the surroundings of {world.setting.name}.",
        f"Write a rhyming mystery where the answer is hidden in the shop surroundings and the ending feels warm and solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    qa = [
        QAItem(
            question=f"Who helped solve the mystery in {world.setting.name}?",
            answer=f"The cobbler helped solve it with {hero.id} and {helper.id}. They followed clues in the surroundings until the missing thing was found.",
        ),
        QAItem(
            question=f"What kind of clue did the story use?",
            answer=f"It used a clue that rhymed: “{m.clue_word}” and “{m.clue_rhyme}.” That rhyme helped point the search in the right direction.",
        ),
        QAItem(
            question=f"What was missing from {m.missing_place}?",
            answer=f"{m.object_phrase.capitalize()} was missing. The story treated it like a little mystery to solve.",
        ),
        QAItem(
            question=f"How did the cobbler know where to search next?",
            answer=f"The cobbler noticed the rhyme and looked around the surroundings where a small hidden thing might have slipped. That careful search led to the answer.",
        ),
    ]
    if m.id == "lost_book":
        qa.append(QAItem(
            question="Where was the missing book found?",
            answer="It was found behind a bench, where the lantern light finally caught its blue cover.",
        ))
    elif m.id == "missing_page":
        qa.append(QAItem(
            question="Where was the missing page hiding?",
            answer="It was tucked under a chair leg, safe and sound.",
        ))
    else:
        qa.append(QAItem(
            question="Where was the tiny key found?",
            answer="It gleamed in the cobbler's tray beside a spool of thread.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    return [
        QAItem(
            question="What is a cobbler?",
            answer="A cobbler is a person who makes and mends shoes and often works with leather, thread, and tools.",
        ),
        QAItem(
            question="What are surroundings?",
            answer="Surroundings are the places and things around you, like shelves, walls, tables, windows, and the street nearby.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when two words sound alike at the end, like “night” and “light.”",
        ),
        QAItem(
            question="Why do people like mysteries?",
            answer="People like mysteries because they get to notice clues, make guesses, and slowly find the truth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.kind:8} {e.type:10}) {' '.join(bits)}")
    for k, v in sorted(world.facts.items()):
        if k in {"hero", "helper", "cobbler", "obj", "mystery"}:
            continue
        lines.append(f"  fact[{k}] = {v}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return f"(No story: the chosen setting '{setting.name}' does not fit the mystery well enough.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with a cobbler, literature, and rhyming clues.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    settings = list(SETTINGS.keys())
    mysteries = list(MYSTERIES.keys())
    setting = args.setting or rng.choice(settings)
    mystery = args.mystery or rng.choice(mysteries)
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES[gender])
    trait = args.trait or rng.choice(TRAITS)
    if setting not in SETTINGS or mystery not in MYSTERIES:
        raise StoryError("(No valid story parameters.)")
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.gender, params.trait, params.parent)
    return StorySample(
        params=params,
        story=build_story_text(world),
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            combos.append((s, m))
    return combos


ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).

valid(S,M) :- setting(S), mystery(M).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_fact", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for s in SETTINGS:
            for m in MYSTERIES:
                params = StoryParams(setting=s, mystery=m, name="Mina", gender="girl", parent="mother", trait="curious")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
