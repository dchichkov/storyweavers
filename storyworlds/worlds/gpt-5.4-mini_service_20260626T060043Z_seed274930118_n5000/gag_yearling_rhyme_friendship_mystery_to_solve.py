#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gag_yearling_rhyme_friendship_mystery_to_solve.py
=================================================================================================

A compact whodunit-style story world about a child detective, a yearling friend,
and a mystery solved with rhyme and friendship.

Seed tale:
---
A child and a yearling friend notice a small mystery: something important has
gone missing. A harmless gag clue is found nearby, but it only makes sense once
they follow a little rhyme. The pair look for tracks, listen for echoes, and
ask kind questions. In the end, the truth is not mean or frightening; it is a
gentle mistake that friendship helps fix.

Core pattern:
---
setup -> something goes missing
investigation -> clues, rhyme, and careful noticing
turn -> the answer points to a culprit
resolution -> friendship repairs the trouble and returns calm

The world models both physical meters and emotional memes, and the narration is
driven by those state changes rather than by a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        for k in ["dust", "lost", "found", "clue", "calm", "tidy", "scuffed"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "hope", "friendship", "curiosity", "pride", "relief", "guilt"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "mare"}
        male = {"boy", "father", "dad", "man", "stallion", "gelding"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    detail: str = ""


@dataclass
class Mystery:
    id: str
    object_label: str
    object_phrase: str
    loss_verb: str
    clue_rhyme: str
    clue_kind: str
    culprit: str
    culprit_label: str
    resolution: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    type: str
    label: str
    phrase: str
    yearling: bool = True
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "barn": Setting(place="the red barn", affords={"rhyme", "search"}, detail="Hay made the air smell sweet, and old boards creaked softly."),
    "garden": Setting(place="the garden", affords={"rhyme", "search"}, detail="Leaves fluttered like little green flags between the paths."),
    "attic": Setting(place="the attic", affords={"rhyme", "search"}, detail="Dusty beams and moonlit boxes made every corner feel secret."),
    "porch": Setting(place="the porch", affords={"rhyme", "search"}, detail="The porch was quiet except for a ticking wind chime."),
}

COMPANIONS = {
    "foal": Companion(id="foal", type="horse", label="yearling foal", phrase="a yearling foal with a bright tail", yearling=True, tags={"yearling"}),
    "goat": Companion(id="goat", type="goat", label="yearling goat", phrase="a yearling goat with clever eyes", yearling=True, tags={"yearling"}),
    "puppy": Companion(id="puppy", type="dog", label="yearling puppy", phrase="a yearling puppy with quick little feet", yearling=True, tags={"yearling"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        object_label="bell",
        object_phrase="a little brass bell",
        loss_verb="gone missing",
        clue_rhyme="If something shiny hides away, look where the careful shadows stay.",
        clue_kind="shine",
        culprit="mouse",
        culprit_label="a mouse",
        resolution="The mouse had tucked the bell under a straw nest to make a jingling den.",
        risk="The yearling could not be found by sound without the bell.",
        tags={"rhyme", "friendship", "mystery"},
    ),
    "ribbon": Mystery(
        id="ribbon",
        object_label="ribbon",
        object_phrase="a blue ribbon",
        loss_verb="lost",
        clue_rhyme="If something soft is out of sight, follow the thread that caught the light.",
        clue_kind="thread",
        culprit="bird",
        culprit_label="a crow",
        resolution="The crow had carried the ribbon to line a tiny nest.",
        risk="The yearling looked plain and puzzled without the ribbon.",
        tags={"rhyme", "friendship", "mystery"},
    ),
    "gag": Mystery(
        id="gag",
        object_label="gag",
        object_phrase="a silly gag note",
        loss_verb="missing",
        clue_rhyme="If a joke is nowhere near, check the place where giggles clear.",
        clue_kind="laugh",
        culprit="kitten",
        culprit_label="a kitten",
        resolution="The kitten had dragged the gag note under a basket to play with it.",
        risk="The child wanted the joke back for the morning game.",
        tags={"gag", "rhyme", "friendship", "mystery"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    companion: str
    mystery: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lila", "Nora", "Pia", "Rosa", "Tess"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Ben", "Owen", "Jude"]
TRAITS = ["curious", "kind", "careful", "brave", "gentle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world with a yearling friend and a rhyme clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, m) for s in SETTINGS for c in COMPANIONS for m in MYSTERIES]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in COMPANIONS.items():
        lines.append(asp.fact("companion", cid))
        if c.yearling:
            lines.append(asp.fact("yearling", cid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("culprit", mid, m.culprit))
        if "gag" in m.tags:
            lines.append(asp.fact("seed_word", "gag"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,M) :- setting(S), companion(C), mystery(M).
yearling_story(C) :- companion(C), yearling(C).
featured_gag(M) :- mystery(M), seed_word(gag).
#show valid/3.
#show yearling_story/1.
#show featured_gag/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.companion is None or c[1] == args.companion)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, c, m = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=s, companion=c, mystery=m, child_name=name, child_gender=gender)


def _name_pronouns(gender: str) -> tuple[str, str, str]:
    return ("she", "her", "her") if gender == "girl" else ("he", "him", "his")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    comp = COMPANIONS[params.companion]
    world = World(setting)

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, label=params.child_name, traits=["little", "detective"]))
    friend = world.add(Entity(id=comp.id, kind="character", type=comp.type, label=comp.label, phrase=comp.phrase, traits=["yearling"]))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue_kind, phrase=mystery.clue_rhyme, owner=child.id))
    missing = world.add(Entity(id=mystery.id, type="thing", label=mystery.object_label, phrase=mystery.object_phrase, owner=friend.id, caretaker=child.id))
    culprit = world.add(Entity(id=mystery.culprit, kind="character", type="animal", label=mystery.culprit_label, traits=["sneaky"]))

    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    friend.memes["friendship"] += 1
    friend.memes["hope"] += 1
    missing.meters["lost"] = 1
    clue.meters["clue"] = 1

    subj, obj, pos = _name_pronouns(params.child_gender)
    world.say(f"{child.id} and the {friend.label} were in {setting.place}.")
    world.say(f"The {friend.label} was a yearling, and {child.id} liked how {friend.phrase} stayed close.")
    world.say(f"Then the {mystery.object_phrase} was {mystery.loss_verb}, and that made both friends pause.")
    world.para()
    world.say(f"{child.id} looked under a bucket, behind a crate, and near a hay pile, but the answer did not appear.")
    child.meters["clue"] += 1
    child.memes["curiosity"] += 1
    world.say(f"Near the floor, {child.id} found a harmless gag clue, and it made the mystery feel less lonely than before.")
    world.say(f"The note said, \"{mystery.clue_rhyme}\"")
    child.memes["hope"] += 1
    world.say(f"{friend.label} nudged {obj} gently, as if to say that two friends can solve one puzzly day together.")

    world.para()
    if mystery.id == "gag":
        world.say(f"{child.id} followed the rhyme to a basket, because the joke clue was the kind that liked to hide where laughter lives.")
    elif mystery.id == "bell":
        world.say(f"{child.id} followed the rhyme to a straw nest, because shiny things often end up where small paws build soft beds.")
    else:
        world.say(f"{child.id} followed the rhyme to a tidy nest, because threads and ribbons love to cling where birds rest.")

    child.meters["clue"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)
    world.say(f"There, the culprit was {mystery.culprit_label}.")
    culprit.memes["guilt"] += 1

    world.para()
    world.say(mystery.resolution)
    child.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    child.memes["relief"] += 1
    child.memes["worry"] = 0.0
    missing.meters["found"] = 1
    missing.meters["lost"] = 0

    world.say(f"{child.id} did not scold the {culprit.label}. Instead, {subj} spoke kindly and fixed the small trouble.")
    world.say(f"Then {child.id} and the {friend.label} laughed together, because the mystery was solved and nobody was left alone with the blame.")
    world.say(f"At the end, the {mystery.object_label} was back where it belonged, and the yearling friend stood close beside {obj} like a happy little shadow.")

    world.facts = {
        "child": child,
        "friend": friend,
        "culprit": culprit,
        "missing": missing,
        "clue": clue,
        "mystery": mystery,
        "setting": setting,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit where a {f["friend"].label} and {f["child"].id} solve a small mystery with a rhyme.',
        f'Tell a gentle friendship story in {f["setting"].place} where the word "gag" appears as a clue and a yearling helps solve the puzzle.',
        f'Write a short mystery about a missing {f["mystery"].object_label} that ends with kind friends discovering who took it.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    mystery = f["mystery"]
    culprit = f["culprit"]
    return [
        QAItem(
            question=f"Who helped {child.id} solve the mystery in {f['setting'].place}?",
            answer=f"The {friend.label} helped {child.id}. They worked together like close friends, and the yearling stayed beside {child.id} the whole time.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{mystery.object_phrase.capitalize()} was missing. That was the mystery everyone had to solve.",
        ),
        QAItem(
            question=f"How did {child.id} find the answer?",
            answer=f"{child.id} found a rhyme clue, followed it carefully, and then noticed where the missing thing had been hidden.",
        ),
        QAItem(
            question=f"Who was the culprit?",
            answer=f"The culprit was {mystery.culprit_label}. The story stayed gentle, so the trouble was fixed without meanness.",
        ),
        QAItem(
            question=f"Why did the story feel like friendship mattered?",
            answer=f"Because {child.id} and the yearling friend kept helping each other, sharing courage, and staying calm until the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a yearling?",
            answer="A yearling is an animal that is about one year old. It is still young, but it is not a newborn anymore.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a piece of language where words sound alike at the end. Rhymes can help people remember clues or songs.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that needs clues and careful thinking to understand.",
        ),
        QAItem(
            question="What does friendship help people do?",
            answer="Friendship helps people share, comfort each other, and solve problems together.",
        ),
    ]
    if "gag" in f["mystery"].tags:
        out.append(QAItem(
            question="What is a gag in a funny story?",
            answer="A gag is a joke or a silly bit that is meant to make people smile.",
        ))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append("character")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="barn", companion="foal", mystery="bell", child_name="Mina", child_gender="girl"),
    StoryParams(setting="garden", companion="goat", mystery="ribbon", child_name="Theo", child_gender="boy"),
    StoryParams(setting="attic", companion="puppy", mystery="gag", child_name="Lila", child_gender="girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos
              if (args.setting is None or c[0] == args.setting)
              and (args.companion is None or c[1] == args.companion)
              and (args.mystery is None or c[2] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, c, m = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=s, companion=c, mystery=m, child_name=name, child_gender=gender)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show yearling_story/1.\n#show featured_gag/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n#show yearling_story/1.\n#show featured_gag/1."))
        print("valid combos:", sorted(set(asp.atoms(model, "valid"))))
        print("yearling stories:", sorted(set(asp.atoms(model, "yearling_story"))))
        print("gag stories:", sorted(set(asp.atoms(model, "featured_gag"))))
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
