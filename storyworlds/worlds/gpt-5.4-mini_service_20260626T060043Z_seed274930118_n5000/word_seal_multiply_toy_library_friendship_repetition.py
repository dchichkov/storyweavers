#!/usr/bin/env python3
"""
storyworlds/worlds/word_seal_multiply_toy_library_friendship_repetition.py
============================================================================

A standalone storyworld for a small whodunit set in a toy library.

Seed tale idea:
- In a toy library, a child notices that the same strange word keeps showing up on slips of paper.
- A sealed box and a repeating trail of copied labels make the mystery feel bigger.
- A friend helps the child follow the repeated clue until the reason is found.

This world is built around:
- word: a clue written on cards and labels
- seal: a wax seal / sticker seal used to close a box
- multiply: copied cards and duplicated stickers, which create repeated evidence

Narrative instruments:
- Friendship: a helper and the sleuth work together
- Repetition: repeated words and repeated clues make the mystery readable

Style:
- Child-facing whodunit with a clear beginning, clue trail, reveal, and resolution.
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


# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    sealed: bool = False
    copied: int = 0
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["order", "dust", "mess", "count"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "worry", "joy", "friendship", "confidence"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "librarian"}
        male = {"boy", "father", "dad", "man", "boy-sleuth"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the toy library"
    secret_room: str = "the back shelf"
    open_hours: bool = True


@dataclass
class StoryParams:
    place: str
    sleuth_name: str
    sleuth_gender: str
    sleuth_trait: str
    friend_name: str
    friend_gender: str
    friend_trait: str
    culprit: str
    seed: Optional[int] = None


@dataclass
class Clue:
    id: str
    text: str
    repeated: bool = False


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    clues: list[Clue] = field(default_factory=list)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities)  # type: ignore[attr-defined]
        clone.clues = dataclasses.deepcopy(self.clues)  # type: ignore[attr-defined]
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "toy_library": Place(name="the toy library", secret_room="the back shelf"),
}

SLEUTHS = [
    ("Mina", "girl", "curious"),
    ("Toby", "boy", "careful"),
    ("Nora", "girl", "patient"),
    ("Eli", "boy", "brave"),
]

FRIENDS = [
    ("Pip", "boy", "kind"),
    ("Luna", "girl", "gentle"),
    ("Ravi", "boy", "helpful"),
    ("Sara", "girl", "bright"),
]

CULPRITS = {
    "copy_paste_mouse": "a tiny copy mouse",
    "stamp_owl": "a stamp owl",
    "windup_bunny": "a wind-up bunny",
}

TRAITS = ["curious", "careful", "patient", "brave", "gentle", "bright"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

def _repetition_rule(world: World) -> list[str]:
    out: list[str] = []
    wordcards = [e for e in world.entities.values() if e.type == "wordcard"]
    for card in wordcards:
        if card.copied < 2:
            continue
        sig = ("repeat", card.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        card.meters["count"] += card.copied
        out.append(f"The same word kept showing up again and again on little cards.")
    return out


def _seal_rule(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.type != "box" or not ent.sealed:
            continue
        sig = ("seal", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The box stayed shut, with a shiny seal on top.")
    return out


def _friendship_rule(world: World) -> list[str]:
    out: list[str] = []
    sleuth = next((e for e in world.entities.values() if e.kind == "character" and e.type == "sleuth"), None)
    friend = next((e for e in world.entities.values() if e.kind == "character" and e.type == "friend"), None)
    if not sleuth or not friend:
        return out
    if sleuth.memes["friendship"] < 1 or friend.memes["friendship"] < 1:
        return out
    sig = ("friendship", sleuth.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sleuth.memes["confidence"] += 1
    friend.memes["confidence"] += 1
    out.append("Working together made the clue trail feel less spooky.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_repetition_rule, _seal_rule, _friendship_rule):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Domain logic
# ---------------------------------------------------------------------------

def pronoun_name(name: str, gender: str, kind: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[kind]
    return {"subject": "he", "object": "him", "possessive": "his"}[kind]


def setup_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    sleuth = world.add(Entity(
        id=params.sleuth_name,
        kind="character",
        type="sleuth",
        label=params.sleuth_name,
        phrase=f"a {params.sleuth_trait} little detective",
        meters={"order": 0.0, "dust": 0.0, "mess": 0.0, "count": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "joy": 0.0, "friendship": 0.0, "confidence": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type="friend",
        label=params.friend_name,
        phrase=f"a {params.friend_trait} helper",
        meters={"order": 0.0, "dust": 0.0, "mess": 0.0, "count": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "friendship": 0.0, "confidence": 0.0},
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type=params.culprit,
        label=CULPRITS[params.culprit],
        phrase=CULPRITS[params.culprit],
        meters={"order": 0.0, "dust": 0.0, "mess": 0.0, "count": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "friendship": 0.0, "confidence": 0.0},
    ))
    box = world.add(Entity(
        id="box",
        kind="thing",
        type="box",
        label="box",
        phrase="a small toy box",
        sealed=True,
        meters={"order": 0.0, "dust": 0.0, "mess": 0.0, "count": 0.0},
    ))
    wordcard = world.add(Entity(
        id="wordcard",
        kind="thing",
        type="wordcard",
        label="word card",
        phrase="a paper card with one word on it",
        owner=sleuth.id,
        held_by=sleuth.id,
        copied=0,
        plural=False,
        meters={"order": 0.0, "dust": 0.0, "mess": 0.0, "count": 0.0},
    ))
    sealstamp = world.add(Entity(
        id="sealstamp",
        kind="thing",
        type="seal",
        label="seal stamp",
        phrase="a little seal stamp",
        owner=friend.id,
        held_by=friend.id,
        plural=False,
        meters={"order": 0.0, "dust": 0.0, "mess": 0.0, "count": 0.0},
    ))

    world.facts.update(
        sleuth=sleuth,
        friend=friend,
        culprit=culprit,
        box=box,
        wordcard=wordcard,
        sealstamp=sealstamp,
        place=world.place,
    )
    return world


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    sleuth: Entity = world.facts["sleuth"]
    friend: Entity = world.facts["friend"]
    culprit: Entity = world.facts["culprit"]
    box: Entity = world.facts["box"]
    wordcard: Entity = world.facts["wordcard"]
    sealstamp: Entity = world.facts["sealstamp"]

    # Setup
    world.say(
        f"{sleuth.id} liked visiting {world.place.name}, where tiny chairs and toy books waited on low shelves."
    )
    world.say(
        f"{sleuth.id} was a {params.sleuth_trait} little detective, and {sleuth.pronoun('subject')} noticed every odd detail."
    )
    world.say(
        f"{friend.id} was there too, and {friend.pronoun('subject')} was a {params.friend_trait} friend who liked helping."
    )
    world.para()
    world.say(
        f"That morning, a strange word kept turning up on the floor near the reading rug: {wordcard.label}."
    )
    world.say(
        f"Then the same word appeared again on another card, and again on a third card, as if it wanted to multiply."
    )

    # Mystery begins
    world.para()
    sleuth.memes["worry"] += 1
    world.say(
        f"{sleuth.id} frowned. 'Why is the same word showing up over and over?' {sleuth.pronoun('subject').capitalize()} asked."
    )
    world.say(
        f"{friend.id} knelt to look, and together they followed the repeated cards toward the back shelf."
    )
    world.say(
        f"There they found a small box, sealed tight with a bright mark on the lid."
    )
    box.sealed = True
    propagate(world)

    # Clue trail
    world.para()
    wordcard.copied = 3
    world.say(
        f"One card had a smudge like a paw print, and another had the word stamped on it twice."
    )
    world.say(
        f"The repeated word looked important, but it did not look like a lie; it looked like a clue."
    )
    culprit.meters["mess"] += 1
    world.say(
        f"Near the shelf, they spotted {culprit.label}, blinking innocent eyes and carrying a tiny ink pad."
    )
    world.say(
        f"{friend.id} noticed the ink pad matched the shiny seal, so the mystery started to make sense."
    )
    propagate(world)

    # Reveal
    world.para()
    world.say(
        f"{culprit.label} had not stolen the toy books at all. {culprit.pronoun('subject').capitalize()} had been making copy after copy of one card to help children practice a word."
    )
    world.say(
        f"The seal was there to keep the practice cards in one safe box, and the repeated word was there so the children could read it again and again."
    )
    world.say(
        f"{sleuth.id} and {friend.id} looked at each other and laughed. It was a mystery, but not a mean one."
    )
    sleuth.memes["joy"] += 1
    friend.memes["joy"] += 1
    sleuth.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    propagate(world)

    # Resolution
    world.para()
    box.sealed = False
    world.say(
        f"At last, {friend.id} peeled up the seal, and {sleuth.id} counted the cards one by one."
    )
    world.say(
        f"They put the word cards back in order, and the toy library felt calm again."
    )
    world.say(
        f"Before they left, {sleuth.id} tucked one card into a pocket and thanked {friend.id} for the friendship that made the answer easy to find."
    )
    world.say(
        f"On the way out, the same word still seemed to repeat in {sleuth.id}'s head, but now it sounded cheerful instead of strange."
    )

    world.facts["solved"] = True
    world.facts["theme_word"] = "word"
    world.facts["theme_seal"] = "seal"
    world.facts["theme_multiply"] = "multiply"
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly whodunit set in a toy library, where a repeated word becomes the clue to a mystery.',
        'Tell a short mystery story about friendship, a seal on a box, and cards that seem to multiply.',
        'Write a simple detective tale in a toy library that uses the words word, seal, and multiply.',
    ]


def story_qa(world: World) -> list[QAItem]:
    sleuth: Entity = world.facts["sleuth"]
    friend: Entity = world.facts["friend"]
    culprit: Entity = world.facts["culprit"]
    box: Entity = world.facts["box"]

    return [
        QAItem(
            question=f"Who was the child detective in the toy library?",
            answer=f"{sleuth.id} was the child detective. {sleuth.pronoun('subject').capitalize()} noticed the repeated clues first.",
        ),
        QAItem(
            question=f"Who helped {sleuth.id} with the mystery?",
            answer=f"{friend.id} helped with the mystery. {friend.pronoun('subject').capitalize()} was a kind friend who looked at the clues together with {sleuth.id}.",
        ),
        QAItem(
            question=f"What did the sealed box mean in the story?",
            answer=(
                f"The sealed box held the practice cards safely. "
                f"It was not hiding a bad secret; it was keeping the cards together."
            ),
        ),
        QAItem(
            question=f"Why did the same word keep appearing again and again?",
            answer=(
                f"The word kept repeating because the cards were being copied for practice. "
                f"That repetition was the clue that led {sleuth.id} and {friend.id} to the back shelf."
            ),
        ),
        QAItem(
            question=f"Who made the clue trail at the toy library?",
            answer=(
                f"{culprit.label} made the clue trail by copying the word cards and using the seal stamp. "
                f"That is why the clues seemed to multiply."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"The friends opened the box, sorted the cards, and solved the mystery. "
                f"Everything felt calm again at the toy library."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seal on a box?",
            answer="A seal is a mark or sticker that keeps a box closed until someone opens it.",
        ),
        QAItem(
            question="What does multiply mean?",
            answer="To multiply means to make more of something, so one thing becomes many things.",
        ),
        QAItem(
            question="Why can repetition help in learning?",
            answer="Repetition can help because seeing or hearing the same word again and again makes it easier to remember.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind of relationship where people help, share, and care about each other.",
        ),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.sealed:
            bits.append("sealed=True")
        if e.copied:
            bits.append(f"copied={e.copied}")
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
world(place,toy_library).
character(sleuth).
character(friend).
character(culprit).
thing(box).
thing(wordcard).
thing(sealstamp).

clue_repeated(wordcard) :- copied(wordcard, N), N >= 2.
mystery_visible(box) :- sealed(box).
friendship_helped(sleuth, friend) :- friendship(sleuth, friend).

#show clue_repeated/1.
#show mystery_visible/1.
#show friendship_helped/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import by contract

    lines: list[str] = []
    lines.append(asp.fact("place", "toy_library"))
    lines.append(asp.fact("character", "sleuth"))
    lines.append(asp.fact("character", "friend"))
    lines.append(asp.fact("character", "culprit"))
    lines.append(asp.fact("thing", "box"))
    lines.append(asp.fact("thing", "wordcard"))
    lines.append(asp.fact("thing", "sealstamp"))
    lines.append(asp.fact("sealed", "box"))
    lines.append(asp.fact("copied", "wordcard", 3))
    lines.append(asp.fact("friendship", "sleuth", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    program = asp_program("#show clue_repeated/1. #show mystery_visible/1. #show friendship_helped/2.")
    model = asp.one_model(program)
    atoms = {
        "clue_repeated": set(asp.atoms(model, "clue_repeated")),
        "mystery_visible": set(asp.atoms(model, "mystery_visible")),
        "friendship_helped": set(asp.atoms(model, "friendship_helped")),
    }
    expected = {
        "clue_repeated": {("wordcard",)},
        "mystery_visible": {("box",)},
        "friendship_helped": {("sleuth", "friend")},
    }
    if atoms == expected:
        print("OK: ASP parity check passed.")
        return 0
    print("MISMATCH:")
    print("got:", atoms)
    print("expected:", expected)
    return 1


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Toy-library whodunit storyworld.")
    ap.add_argument("--place", choices=PLACES.keys(), default="toy_library")
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
    sleuth_name, sleuth_gender, sleuth_trait = rng.choice(SLEUTHS)
    friend_name, friend_gender, friend_trait = rng.choice(FRIENDS)
    culprit = rng.choice(list(CULPRITS.keys()))
    if sleuth_name == friend_name:
        friend_name, friend_gender, friend_trait = random.choice([f for f in FRIENDS if f[0] != sleuth_name])
    return StoryParams(
        place=args.place,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        sleuth_trait=sleuth_trait,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
        culprit=culprit,
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


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(
        place="toy_library",
        sleuth_name="Mina",
        sleuth_gender="girl",
        sleuth_trait="curious",
        friend_name="Pip",
        friend_gender="boy",
        friend_trait="kind",
        culprit="copy_paste_mouse",
    ),
    StoryParams(
        place="toy_library",
        sleuth_name="Toby",
        sleuth_gender="boy",
        sleuth_trait="careful",
        friend_name="Luna",
        friend_gender="girl",
        friend_trait="gentle",
        culprit="stamp_owl",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show clue_repeated/1. #show mystery_visible/1. #show friendship_helped/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show clue_repeated/1. #show mystery_visible/1. #show friendship_helped/2."))
        print("ASP atoms:")
        for pred in ["clue_repeated", "mystery_visible", "friendship_helped"]:
            print(pred, asp.atoms(model, pred))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.sleuth_name} and {p.friend_name} in the toy library"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
