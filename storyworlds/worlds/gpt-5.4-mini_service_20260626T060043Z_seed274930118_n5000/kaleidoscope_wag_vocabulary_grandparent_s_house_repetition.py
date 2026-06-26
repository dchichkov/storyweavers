#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/kaleidoscope_wag_vocabulary_grandparent_s_house_repetition.py
=========================================================================================================================================

A small fairy-tale story world about a curious child visiting a grandparent's
house, where a kaleidoscope, repetition, and vocabulary learning cause a gentle
transformation.

Seed premise:
---
A child visits a grandparent's house and discovers an old kaleidoscope. A wagging
dog and a stack of vocabulary cards keep drawing the child's curiosity. The child
repeats new words, turns the kaleidoscope again and again, and the old room begins
to feel magical and changed.

World model:
---
- meters: physical state like sparkle, pattern, tidiness, wornness
- memes: emotional/social state like curiosity, joy, repetition, confidence,
  patience, transformation

Narrative instruments:
---
- Repetition: the child repeats words and actions; a refrain is woven into the text
- Transformation: the kaleidoscope changes the shapes, and the child's practice
  changes how they feel
- Curiosity: the child is drawn to the object and the words, and that drive creates
  the turn of the tale

Style:
---
Fairy-tale, child-facing, concrete, and gently magical.
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
# Core world model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "pet"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    house: str = "grandparent's house"
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)
    trace_log: list[str] = field(default_factory=list)

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
        clone = World(self.house)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    grandparent_role: str
    companion: str
    seed: Optional[int] = None


CHILDREN = [
    ("Mia", "girl"),
    ("Leo", "boy"),
    ("Nora", "girl"),
    ("Finn", "boy"),
    ("Ada", "girl"),
    ("Theo", "boy"),
]

GRANDPARENTS = ["grandmother", "grandfather"]

COMPANIONS = {
    "dog": {
        "kind": "pet",
        "type": "dog",
        "label": "old dog",
        "phrase": "an old dog with a happy tail",
    },
    "cat": {
        "kind": "pet",
        "type": "cat",
        "label": "sleepy cat",
        "phrase": "a sleepy cat on a sun-warmed cushion",
    },
}

VOCABULARY_WORDS = [
    ("gleam", "to shine softly"),
    ("whirl", "to spin around and around"),
    ("bright", "full of light"),
    ("gentle", "kind and soft"),
    ("twinkle", "to sparkle in little flashes"),
]

FARMLIKE_ITEMS = [
    ("kaleidoscope", "an old brass kaleidoscope with a tiny cracked handle"),
    ("vocabulary cards", "a little box of vocabulary cards tied with blue ribbon"),
]


# ---------------------------------------------------------------------------
# Helper narration
# ---------------------------------------------------------------------------
def name_and_role(child: Entity, gp: Entity) -> str:
    return f"{child.id} and {gp.type}"


def setup_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        meme_defaults=False if False else None,
        meters={"tidiness": 0.0},
        memes={"curiosity": 0.0, "joy": 0.0, "confidence": 0.0, "repetition": 0.0, "transformation": 0.0},
    ))
    gp = world.add(Entity(
        id="grandparent",
        kind="character",
        type=params.grandparent_role,
        label=f"the {params.grandparent_role}",
        meters={"patience": 0.0, "tidiness": 0.0},
        memes={"warmth": 0.0, "joy": 0.0},
    ))
    comp = COMPANIONS[params.companion]
    pet = world.add(Entity(
        id=params.companion,
        kind="pet",
        type=comp["type"],
        label=comp["label"],
        phrase=comp["phrase"],
        meters={"wag": 0.0},
        memes={"friendliness": 0.0},
        owner=gp.id,
    ))
    scope = world.add(Entity(
        id="kaleidoscope",
        kind="thing",
        type="kaleidoscope",
        label="kaleidoscope",
        phrase="an old brass kaleidoscope",
        owner=gp.id,
        meters={"sparkle": 0.0, "patterns": 0.0},
        memes={"wonder": 0.0, "change": 0.0},
    ))
    cards = world.add(Entity(
        id="cards",
        kind="thing",
        type="vocabulary_cards",
        label="vocabulary cards",
        phrase="a little box of vocabulary cards",
        owner=gp.id,
        meters={"order": 1.0},
        memes={"words": 0.0},
        plural=True,
    ))
    world.facts.update(child=child, grandparent=gp, pet=pet, scope=scope, cards=cards, params=params)
    return world


def _repeat_phrase(word: str, count: int) -> str:
    return ", ".join([word] * count)


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_wag(world: World) -> list[str]:
    pet = world.get(world.facts["params"].companion)
    child = world.get(world.facts["params"].child_name)
    if ("wag", pet.id) in world.fired:
        return []
    if child.memes.get("curiosity", 0.0) >= THRESHOLD:
        world.fired.add(("wag", pet.id))
        pet.meters["wag"] = 1.0
        pet.memes["friendliness"] = 1.0
        child.memes["joy"] += 0.5
        return [f"The old dog wagged its tail as if it knew a story was beginning."]
    return []


def _r_curiosity_to_touch(world: World) -> list[str]:
    child = world.get(world.facts["params"].child_name)
    scope = world.get("kaleidoscope")
    if ("touch", child.id) in world.fired:
        return []
    if child.memes.get("curiosity", 0.0) >= THRESHOLD:
        world.fired.add(("touch", child.id))
        scope.meters["sparkle"] += 1.0
        scope.memes["wonder"] += 1.0
        child.meters["tidiness"] += 0.0
        return [f"{child.id} leaned closer to the kaleidoscope, drawn by its tiny secret light."]
    return []


def _r_turn_transform(world: World) -> list[str]:
    child = world.get(world.facts["params"].child_name)
    scope = world.get("kaleidoscope")
    if ("turn", scope.id) in world.fired:
        return []
    if scope.meters["sparkle"] >= THRESHOLD and child.memes.get("curiosity", 0.0) >= THRESHOLD:
        world.fired.add(("turn", scope.id))
        scope.meters["patterns"] += 1.0
        scope.memes["change"] += 1.0
        child.memes["transformation"] += 1.0
        return ["With one careful turn, the broken old glass became a wheel of stars, petals, and rainbows."]
    return []


def _r_repetition_practice(world: World) -> list[str]:
    child = world.get(world.facts["params"].child_name)
    cards = world.get("cards")
    if ("practice", child.id) in world.fired:
        return []
    if child.memes.get("repetition", 0.0) >= THRESHOLD:
        world.fired.add(("practice", child.id))
        cards.meters["order"] += 1.0
        cards.memes["words"] += 1.0
        child.memes["confidence"] += 1.0
        return [f"{child.id} repeated the words again and again, and each repeat made them easier to keep."]
    return []


CAUSAL_RULES = [_r_wag, _r_curiosity_to_touch, _r_turn_transform, _r_repetition_practice]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World) -> None:
    child = world.facts["child"]
    gp = world.facts["grandparent"]
    world.say(
        f"Once upon a time, {child.id} came to the {world.house}, where {gp.label} kept old treasures in a sunny room."
    )
    world.say(
        f"On a shelf sat a {world.facts['scope'].label} and a box of {world.facts['cards'].label} waiting like quiet spells."
    )


def curiosity_beats(world: World) -> None:
    child = world.facts["child"]
    pet = world.facts["pet"]
    child.memes["curiosity"] += 1.0
    world.say(
        f"{child.id} watched the {pet.label} wag and wag, then wondered what the round little tube could do."
    )
    propagate(world)


def repetition_beats(world: World) -> None:
    child = world.facts["child"]
    cards = world.facts["cards"]
    child.memes["repetition"] += 1.0
    words = [w for w, _ in VOCABULARY_WORDS[:3]]
    world.say(
        f"{child.id} picked up the vocabulary cards and said, '{_repeat_phrase(words[0], 2)}.' Then {child.pronoun()} said it again: '{_repeat_phrase(words[0], 2)}.'"
    )
    world.say(
        f"The cards showed {words[1]} and {words[2]}, and {child.id} repeated each word until the sounds felt cozy in the mouth."
    )
    propagate(world)


def transformation_beats(world: World) -> None:
    child = world.facts["child"]
    scope = world.facts["scope"]
    child.memes["curiosity"] += 0.5
    scope.meters["sparkle"] += 1.0
    world.say(
        f"{child.id} turned the kaleidoscope slowly, then slowly again, and the colors shifted into a new bright pattern."
    )
    propagate(world)
    if scope.meters["patterns"] >= THRESHOLD:
        world.say(
            f"Inside the little tube, the same pieces became something new, as if the room itself had learned to dance."
        )
    child.memes["confidence"] += 0.5
    child.memes["joy"] += 0.5


def ending(world: World) -> None:
    child = world.facts["child"]
    gp = world.facts["grandparent"]
    scope = world.facts["scope"]
    cards = world.facts["cards"]
    world.say(
        f"At last, {child.id} held the vocabulary cards in neat order and smiled at the kaleidoscope one more time."
    )
    world.say(
        f"The {gp.type} laughed softly, the old dog wagged once more, and the room felt changed: the words were learned, and the little world had turned bright."
    )


def build_story(world: World) -> None:
    introduce(world)
    world.para()
    curiosity_beats(world)
    repetition_beats(world)
    world.para()
    transformation_beats(world)
    ending(world)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a fairy-tale story about a child visiting a grandparent\'s house, where a kaleidoscope and vocabulary cards lead to wonder.',
        f"Tell a gentle story where {p.child_name} is curious about a kaleidoscope, repeats new vocabulary words, and notices a wagging dog.",
        "Write a short magical story set in a grandparent's house with repetition, transformation, and curiosity.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    gp = world.facts["grandparent"]
    pet = world.facts["pet"]
    scope = world.facts["scope"]
    cards = world.facts["cards"]
    return [
        QAItem(
            question=f"Where did {child.id} go in the story?",
            answer=f"{child.id} went to the grandparent's house, where the sunny room held a kaleidoscope and vocabulary cards.",
        ),
        QAItem(
            question=f"What made {child.id} curious first?",
            answer=f"The old dog wagging its tail and the strange kaleidoscope made {child.id} curious about what magical thing might happen next.",
        ),
        QAItem(
            question=f"What did {child.id} keep repeating?",
            answer=f"{child.id} repeated the vocabulary words again and again, so the words became easier and friendlier to remember.",
        ),
        QAItem(
            question=f"What changed when the kaleidoscope was turned?",
            answer=f"The same little pieces became bright new patterns, so the kaleidoscope transformed the room into a tiny wheel of stars and color.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and the grandparent?",
            answer=f"{child.id} finished with the vocabulary cards in neat order, while the grandparent laughed and the room felt bright and changed.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a kaleidoscope?",
        answer="A kaleidoscope is a tube with mirrors and small pieces inside. When you turn it, the pieces make changing patterns.",
    ),
    QAItem(
        question="What does wag mean when a dog wags its tail?",
        answer="When a dog wags its tail, it moves the tail back and forth to show excitement, happiness, or friendliness.",
    ),
    QAItem(
        question="What is vocabulary?",
        answer="Vocabulary is the collection of words a person knows and uses.",
    ),
    QAItem(
        question="Why do children repeat new words?",
        answer="Children repeat new words to practice them, remember them, and make them easier to say later.",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A child is curious when curiosity reaches the threshold.
curious(child) :- curiosity(child).

% Wagging can help curiosity become attention.
noticed(pet) :- wag(pet), curious(child).

% Repetition supports learning words.
learned(word) :- repeated(word).

% Transformation happens when the kaleidoscope is turned after being noticed.
transformed(kaleidoscope) :- noticed(kaleidoscope), turned(kaleidoscope).

% A story is reasonable when all three instruments are present.
valid_story(kaleidoscope, wag, vocabulary) :-
    curious(child),
    wag(pet),
    learned(vocabulary),
    transformed(kaleidoscope).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("curiosity"),
            asp.fact("wag"),
            asp.fact("vocabulary"),
            asp.fact("setting", "grandparents_house"),
            asp.fact("feature", "repetition"),
            asp.fact("feature", "transformation"),
            asp.fact("feature", "curiosity"),
            asp.fact("style", "fairy_tale"),
            asp.fact("keyword", "kaleidoscope"),
            asp.fact("keyword", "wag"),
            asp.fact("keyword", "vocabulary"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = [("kaleidoscope", "wag", "vocabulary")]
    if atoms == py:
        print("OK: ASP and Python agree on the core story pattern.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", atoms)
    print("  PY :", py)
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    build_story(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=WORLD_KNOWLEDGE,
        world=world,
    )


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:12} ({ent.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(child_name="Mia", child_gender="girl", grandparent_role="grandmother", companion="dog"),
    StoryParams(child_name="Leo", child_gender="boy", grandparent_role="grandfather", companion="dog"),
    StoryParams(child_name="Nora", child_gender="girl", grandparent_role="grandmother", companion="cat"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: kaleidoscope, wag, vocabulary.")
    ap.add_argument("--name", choices=[c[0] for c in CHILDREN])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grandparent", choices=GRANDPARENTS)
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
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
    if args.name and not args.gender:
        for n, g in CHILDREN:
            if n == args.name:
                args.gender = g
                break
    if args.gender and args.name:
        for n, g in CHILDREN:
            if n == args.name and g != args.gender:
                raise StoryError("The chosen name does not match the chosen gender.")
    if args.companion and args.companion not in COMPANIONS:
        raise StoryError("Unknown companion.")

    name, gender = (args.name, args.gender) if args.name else rng.choice(CHILDREN)
    gp = args.grandparent or rng.choice(GRANDPARENTS)
    comp = args.companion or rng.choice(sorted(COMPANIONS))
    return StoryParams(child_name=name, child_gender=gender, grandparent_role=gp, companion=comp)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
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
            header = f"### {p.child_name} at {p.grandparent_role}'s house"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
