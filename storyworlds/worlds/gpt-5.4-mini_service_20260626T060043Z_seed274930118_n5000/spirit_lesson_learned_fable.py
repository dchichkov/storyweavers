#!/usr/bin/env python3
"""
spirit_lesson_learned_fable.py
==============================

A tiny fable-style storyworld about a curious spirit, one small mistake, and a
lesson learned at the end.

The world is intentionally small and constraint-checked: a spirit can meet one
animal friend in one place, try one tempting action, cause one believable
problem, and then fix it through a simple lesson learned.
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

LESSON_MARKERS = {
    "patience",
    "kindness",
    "honesty",
    "sharing",
    "listening",
}

PLACES = {
    "moonlit_grove": "the moonlit grove",
    "quiet_pond": "the quiet pond",
    "stone_path": "the stone path",
    "old_orchard": "the old orchard",
    "hill_top": "the hilltop",
}

ANIMALS = {
    "fox": ("fox", "a clever fox", "fox"),
    "rabbit": ("rabbit", "a small rabbit", "rabbit"),
    "crow": ("crow", "a black crow", "crow"),
    "mouse": ("mouse", "a tiny mouse", "mouse"),
    "turtle": ("turtle", "a slow turtle", "turtle"),
}

TEMPTS = {
    "hide_lantern": {
        "verb": "hide the lantern",
        "gerund": "hiding the lantern",
        "risk": "the path would go dark",
        "repair": "bring the lantern back",
        "lesson": "honesty",
    },
    "scatter_seeds": {
        "verb": "scatter the seeds",
        "gerund": "scattering the seeds",
        "risk": "the little friend would go hungry",
        "repair": "gather the seeds again",
        "lesson": "kindness",
    },
    "rush_ahead": {
        "verb": "rush ahead",
        "gerund": "rushing ahead",
        "risk": "the friend would be left behind",
        "repair": "slow down and wait",
        "lesson": "patience",
    },
    "take_more": {
        "verb": "take more than its share",
        "gerund": "taking more than its share",
        "risk": "there would not be enough left",
        "repair": "give some back",
        "lesson": "sharing",
    },
    "ignore_warning": {
        "verb": "ignore the warning",
        "gerund": "ignoring the warning",
        "risk": "the friend could get into trouble",
        "repair": "listen carefully",
        "lesson": "listening",
    },
}

LESSON_TEXT = {
    "honesty": "It is better to tell the truth than to hide a mistake.",
    "kindness": "A kind act can make a fearful day gentle.",
    "patience": "Slow steps often keep everyone safe.",
    "sharing": "When you share, there is enough for more than one heart.",
    "listening": "Listening first can keep a small problem from growing big.",
}

SPIRIT_TRAITS = ["glowing", "gentle", "restless", "shy", "mischievous", "thoughtful"]
MOODS = ["bright", "curious", "lonely", "proud", "nervous"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "spirit":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"fox", "crow", "turtle"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    spirit_trait: str
    animal_key: str
    temptation_key: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


@dataclass
class StoryParams:
    place: str
    animal: str
    temptation: str
    trait: str
    mood: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-style storyworld about a spirit and a lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--temptation", choices=TEMPTS)
    ap.add_argument("--trait", choices=SPIRIT_TRAITS)
    ap.add_argument("--mood", choices=MOODS)
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


def reasonableness_gate(place: str, animal: str, temptation: str) -> bool:
    if place == "quiet_pond" and temptation == "hide_lantern":
        return False
    if place == "hill_top" and animal == "turtle" and temptation == "rush_ahead":
        return False
    return True


def explain_rejection(place: str, animal: str, temptation: str) -> str:
    return f"(No story: {TEMPTS[temptation]['verb']} does not fit well with {ANIMALS[animal][0]} at {PLACES[place]}.)"


def ASP_RULES() -> str:
    return r"""
valid(P,A,T) :- place(P), animal(A), temptation(T), not blocked(P,A,T).
blocked(quiet_pond,_,hide_lantern).
blocked(hill_top,turtle,rush_ahead).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for t in TEMPTS:
        lines.append(asp.fact("temptation", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, a, t) for p in PLACES for a in ANIMALS for t in TEMPTS if reasonableness_gate(p, a, t)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for p in PLACES:
        if args.place and p != args.place:
            continue
        for a in ANIMALS:
            if args.animal and a != args.animal:
                continue
            for t in TEMPTS:
                if args.temptation and t != args.temptation:
                    continue
                if not reasonableness_gate(p, a, t):
                    continue
                combos.append((p, a, t))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, animal, temptation = rng.choice(sorted(combos))
    trait = args.trait or rng.choice(SPIRIT_TRAITS)
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(place=place, animal=animal, temptation=temptation, trait=trait, mood=mood)


def generate_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    animal_type, animal_phrase, animal_label = ANIMALS[params.animal]
    temptation = TEMPTS[params.temptation]
    w = World(place=place, spirit_trait=params.trait, animal_key=params.animal, temptation_key=params.temptation)
    spirit = w.add(Entity(id="Spirit", kind="spirit", type="spirit", label="spirit"))
    friend = w.add(Entity(id="Friend", kind="animal", type=animal_type, label=animal_label, phrase=animal_phrase))
    spirit.meters["glow"] = 1.0
    spirit.memes["mood"] = 1.0
    friend.memes["trust"] = 1.0

    w.say(f"Long ago, in {place}, there lived a {params.trait} spirit.")
    w.say(f"It felt {params.mood} and watched over the path with a quiet, glowing light.")
    w.say(f"One evening, the spirit met {animal_phrase} and the two began to walk together.")
    w.para()
    w.say(f"The spirit wanted to {temptation['verb']}, because it seemed funny at first.")
    spirit.memes["temptation"] = 1.0
    spirit.meters["mischief"] = 1.0
    w.say(f"But that choice would {temptation['risk']}.")
    friend.memes["worry"] = 1.0
    w.para()
    w.say(f"The animal looked up and waited. The spirit looked again and felt its heart grow still.")
    w.say(f"Then the spirit chose to {temptation['repair']}.")
    spirit.meters["repair"] = 1.0
    spirit.memes["lesson"] = 1.0
    friend.memes["relief"] = 1.0
    w.say(f"At once, the trouble eased, and the path felt kind again.")
    w.para()
    lesson = temptation["lesson"]
    w.say(f"From that day on, the spirit remembered: {LESSON_TEXT[lesson]}")
    w.say(f"And so the little fable ended with a lesson learned.")
    w.facts.update(
        spirit=spirit,
        friend=friend,
        temptation=temptation,
        lesson=lesson,
        place=params.place,
        animal=params.animal,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about a spirit in {f['place']} and a lesson learned.",
        f"Tell a child-friendly story where a {f['spirit'].label} meets a {ANIMALS[f['animal']][1]} and makes a mistake, then fixes it.",
        f"Write a gentle fable that ends with the lesson: {LESSON_TEXT[f['lesson']]}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    t = f["temptation"]
    s = f["spirit"]
    friend = f["friend"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about a spirit and {friend.phrase}. The spirit begins {world.spirit_trait} and a little tempted, but it learns a better way.",
        ),
        QAItem(
            question=f"What did the spirit first want to do in {world.place}?",
            answer=f"The spirit first wanted to {t['verb']}. That seemed fun for a moment, but it would cause trouble for the path and for the friend.",
        ),
        QAItem(
            question="How did the spirit fix the problem?",
            answer=f"The spirit fixed the problem by choosing to {t['repair']}. That made things safe again and showed the spirit the right lesson.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"The lesson was: {LESSON_TEXT[f['lesson']]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    lesson = f["lesson"]
    return [
        QAItem(
            question="What is a spirit in a fable?",
            answer="A spirit is often a magical helper or traveler in a story. In a fable, a spirit can stand for a feeling or a choice.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important from what happened, so you can do better next time.",
        ),
        QAItem(
            question="Why do fables end with a lesson?",
            answer="Fables end with a lesson so the reader can remember the good choice and carry the message into daily life.",
        ),
        QAItem(
            question=f"What does the lesson of {lesson} mean?",
            answer=LESSON_TEXT[lesson],
        ),
    ]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:6}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moonlit_grove", animal="fox", temptation="hide_lantern", trait="mischievous", mood="curious"),
    StoryParams(place="quiet_pond", animal="rabbit", temptation="scatter_seeds", trait="gentle", mood="nervous"),
    StoryParams(place="stone_path", animal="crow", temptation="ignore_warning", trait="thoughtful", mood="proud"),
    StoryParams(place="old_orchard", animal="mouse", temptation="take_more", trait="shy", mood="lonely"),
    StoryParams(place="hill_top", animal="fox", temptation="rush_ahead", trait="glowing", mood="bright"),
]


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combos:")
        for p, a, t in combos:
            print(f"  {p:14} {a:8} {t:16}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.place} / {p.animal} / {p.temptation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
