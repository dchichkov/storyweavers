#!/usr/bin/env python3
"""
A small storyworld: a pirate tale at the quarry edge, where a stubborn heart
learns a lesson through repetition and transformation.

The seed image:
- A young pirate works near the quarry edge.
- There is a mound of stones and a heavy heart: pride, worry, or stubbornness.
- Repetition matters: the same mistake is tried more than once.
- Lesson learned and transformation close the tale.

This world simulates a tiny causal arc rather than swapping nouns into a fixed
paragraph. The state tracks a physical quarry scene and emotional memories.
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
# Core world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pirate", "lad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTING = {
    "place": "the quarry edge",
}

ROLES = {
    "captain": {
        "type": "pirate",
        "label": "captain",
        "phrase": "a young pirate captain",
        "pronoun_name": "captain",
    },
    "deckhand": {
        "type": "pirate",
        "label": "deckhand",
        "phrase": "a small deckhand pirate",
        "pronoun_name": "deckhand",
    },
}

HELPERS = {
    "parrot": {
        "label": "parrot",
        "phrase": "a bright parrot",
        "kind": "animal",
    },
    "mate": {
        "label": "mate",
        "phrase": "a loyal mate",
        "kind": "character",
    },
    "lantern": {
        "label": "lantern",
        "phrase": "a brass lantern",
        "kind": "thing",
    },
}


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _repetition_rule(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("repeat_try", 0) >= THRESHOLD and hero.memes.get("stuck", 0) >= THRESHOLD:
        sig = ("repeat_warning",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
            out.append("The same rough plan had failed twice, and the pirate's heart felt heavier.")
    return out


def _lesson_rule(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes.get("frustration", 0) >= THRESHOLD and hero.memes.get("care", 0) >= THRESHOLD:
        sig = ("lesson_learned",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["lesson"] = hero.memes.get("lesson", 0) + 1
            hero.memes["pride"] = max(0.0, hero.memes.get("pride", 0.0) - 1.0)
            out.append("The pirate learned that stubbornness could not move a stone mound.")
    return out


def _transformation_rule(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    mound = world.get("mound")
    if hero.memes.get("lesson", 0) >= THRESHOLD and mound.meters.get("shifted", 0) < THRESHOLD:
        sig = ("transformation",)
        if sig not in world.fired:
            world.fired.add(sig)
            mound.meters["shifted"] = 1.0
            hero.memes["hope"] = hero.memes.get("hope", 0) + 1
            out.append("Once the pirate changed the plan, the stone mound began to move at last.")
    return out


RULES = [_repetition_rule, _lesson_rule, _transformation_rule]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> World:
    world = World(place=SETTING["place"])
    role = ROLES[params.role]
    helper = HELPERS[params.helper]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=role["type"],
        label=role["label"],
        phrase=role["phrase"],
        memes={"pride": 1.0, "curiosity": 1.0, "care": 0.0},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind=helper["kind"],
        type=helper["kind"] if helper["kind"] != "character" else "pirate",
        label=helper["label"],
        phrase=helper["phrase"],
    ))
    mound = world.add(Entity(
        id="mound",
        kind="thing",
        type="stone mound",
        label="mound",
        phrase="a tall mound of quarry stones",
        meters={"weight": 3.0, "shifted": 0.0},
    ))
    heart = world.add(Entity(
        id="heart",
        kind="thing",
        type="heart",
        label="heart",
        phrase="a heavy heart",
        meters={"weight": 1.0},
        memes={"worry": 1.0, "stubborn": 1.0},
    ))

    world.facts.update(hero=hero, helper=helper_ent, mound=mound, heart=heart)
    return world


def tell(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    mound = world.get("mound")
    heart = world.get("heart")

    world.say(
        f"At the quarry edge, {hero.phrase} watched {mound.phrase} beside {heart.phrase}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to prove {hero.pronoun('possessive')} strength, "
        f"so {hero.pronoun()} tried to push the stones by {hero.pronoun('possessive')} self."
    )

    hero.memes["repeat_try"] = hero.memes.get("repeat_try", 0) + 1
    hero.memes["stuck"] = hero.memes.get("stuck", 0) + 1
    world.say(
        f"But the mound did not budge, and the heart only thumped harder."
    )

    world.para()
    world.say(
        f"{helper.phrase.capitalize()} came near and pointed at the narrow path around the rocks."
    )
    world.say(
        f"\"One push is not the same as a wise push,\" {helper.pronoun()} said."
    )
    hero.memes["care"] = hero.memes.get("care", 0) + 1

    # Repetition: try the wrong way again, then the right way.
    hero.memes["repeat_try"] = hero.memes.get("repeat_try", 0) + 1
    world.say(
        f"So {hero.pronoun()} tried again, slower this time, but the mound stayed firm."
    )
    hero.memes["stuck"] = hero.memes.get("stuck", 0) + 1

    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then {hero.pronoun()} stopped straining and worked with {helper.pronoun('object')}, "
        f"moving one stone at a time."
    )
    heart.meters["weight"] = 0.0
    heart.memes["worry"] = 0.0
    hero.memes["pride"] = max(0.0, hero.memes.get("pride", 0.0) - 0.5)
    hero.memes["care"] += 1.0
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    mound.meters["shifted"] = 1.0

    world.say(
        f"At last the mound gave way, and the heavy heart felt light enough for a grin."
    )
    world.say(
        f"The pirate had learned the lesson: a careful crew could move what pride could not."
    )

    world.facts["resolved"] = True
    world.facts["lesson"] = True
    world.facts["transformed"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        'Write a pirate tale for a small child at the quarry edge, with a mound, a heart, repetition, and a lesson learned.',
        'Tell a short story where a young pirate tries the same plan twice, then changes and transforms the problem with help.',
        'Write a gentle pirate story in which a stubborn heart becomes brave and careful at the quarry edge.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    mound = world.get("mound")
    heart = world.get("heart")
    return [
        QAItem(
            question="Where does the story happen?",
            answer=f"It happens at the quarry edge, where {mound.label} stones and a heavy {heart.label} are part of the day.",
        ),
        QAItem(
            question=f"What did {hero.pronoun()} try first?",
            answer=f"{hero.pronoun().capitalize()} tried to push the stone mound by {hero.pronoun('possessive')} self, but it did not move.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun()} need {helper.pronoun('object')}?",
            answer=f"{helper.phrase.capitalize()} helped because the pirate needed a wiser plan, not just another hard push.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson was that stubbornness can fail, but careful teamwork can make a hard thing move.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="By the end, the mound had shifted and the heavy heart felt lighter, so the pirate was changed too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quarry?",
            answer="A quarry is a place where stone is dug from the ground.",
        ),
        QAItem(
            question="What is a mound?",
            answer="A mound is a heap or pile of things, like stones or dirt, built up above the ground.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding something important after an experience, so you can do better next time.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation is a change from one state to another, like a problem becoming solved or a person becoming wiser.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing the same action again and again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"{ent.id}: {ent.type} {', '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation / params
# ---------------------------------------------------------------------------

NAME_POOL = ["Ari", "Mina", "Sail", "Nico", "Rae", "Tom", "Luca", "Jules"]
ROLE_POOL = ["captain", "deckhand"]
HELPER_POOL = ["parrot", "mate", "lantern"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale at the quarry edge.")
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLE_POOL)
    ap.add_argument("--helper", choices=HELPER_POOL)
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
    role = args.role or rng.choice(ROLE_POOL)
    helper = args.helper or rng.choice(HELPER_POOL)
    name = args.name or rng.choice(NAME_POOL)
    return StoryParams(name=name, role=role, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts emitted:
% hero(Name), helper(Kind), place(quarry_edge), mound, heart.
% We keep the ASP twin minimal but meaningful: it mirrors the story-world's
% three-step arc of repetition, lesson learned, and transformation.

repeat_twice :- hero_try(push), hero_try(push).
lesson_learned :- repeat_twice, helper_present.
transformed :- lesson_learned, mound_moves.

#show repeat_twice/0.
#show lesson_learned/0.
#show transformed/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "quarry_edge"),
            asp.fact("mound"),
            asp.fact("heart"),
            asp.fact("hero", "pirate"),
            asp.fact("helper_present"),
            asp.fact("hero_try", "push"),
            asp.fact("hero_try", "push"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program())
    shown = {str(sym) for sym in model}
    expected = {"repeat_twice", "lesson_learned", "transformed"}
    if expected.issubset(shown):
        print("OK: ASP parity checks passed.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected symbols.")
    print("shown:", sorted(shown))
    return 1


# ---------------------------------------------------------------------------
# Curated variants
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(name="Ari", role="captain", helper="mate"),
    StoryParams(name="Mina", role="deckhand", helper="parrot"),
    StoryParams(name="Rae", role="captain", helper="lantern"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as e:
            raise SystemExit(f"ASP unavailable: {e}")
        model = asp.one_model(asp_program())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.name}: {p.role} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
