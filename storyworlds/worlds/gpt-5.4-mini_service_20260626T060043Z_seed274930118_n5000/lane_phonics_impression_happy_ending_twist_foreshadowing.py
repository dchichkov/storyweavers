#!/usr/bin/env python3
"""
storyworlds/worlds/lane_phonics_impression_happy_ending_twist_foreshadowing.py
===============================================================================

A tiny fable-like story world about a lane, a phonics lesson, and the impression
that careful listening leaves behind.

Premise:
- A young reader wants to carry bright word cards along a village lane.
- A teacher warns that a noisy shortcut will jumble the sounds.
- The world tracks physical distance, sound scraps, and emotional states.

Turn:
- A twist reveals the noisy helper was trying to protect the lesson, not spoil it.

Resolution:
- The characters slow down, sort the sounds, and finish with a happy ending:
  the child reads clearly, and the lane becomes the place where the lesson is
  remembered.

Narrative instruments:
- Foreshadowing: a small clue suggests the shortcut may not be what it seems.
- Twist: the apparent troublemaker has a good reason.
- Happy ending: the lesson succeeds and the impression is a good one.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "teacher"}
        male = {"boy", "man", "father", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Lane:
    name: str
    village: str
    quiet: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class PhonicsLesson:
    word: str
    sound: str
    letters: str
    cards: list[str]
    clue: str
    noise: str
    useful: str
    reveal: str
    ending_image: str


@dataclass
class StoryParams:
    lane: str
    lesson: str
    child_name: str
    child_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, lane: Lane) -> None:
        self.lane = lane
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        other = World(self.lane)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


LANES = {
    "village": Lane(name="the village lane", village="village", affords={"walk", "listen", "teach"}),
    "orchard": Lane(name="the orchard lane", village="orchard", affords={"walk", "listen", "teach"}),
    "brook": Lane(name="the brook lane", village="brook", affords={"walk", "listen", "teach"}),
}

LESSONS = {
    "bright": PhonicsLesson(
        word="bright",
        sound="br",
        letters="b and r",
        cards=["b", "r", "i", "gh", "t"],
        clue="a tiny trail of glitter dust near the gate",
        noise="a loud clatter from the cart",
        useful="a soft pause before the last sound",
        reveal="the clatter had been the helper nudging the cards back into order",
        ending_image="the bright cards shone neatly in a small fan on the bench",
    ),
    "stone": PhonicsLesson(
        word="stone",
        sound="st",
        letters="s and t",
        cards=["s", "t", "o", "n", "e"],
        clue="two little footprints side by side on the dust",
        noise="a shuffle from behind the hedge",
        useful="a steady breath between the first sounds",
        reveal="the shuffle had been the helper carrying the dropped cards home",
        ending_image="the stone cards rested in a tidy row like stepping-stones",
    ),
    "grape": PhonicsLesson(
        word="grape",
        sound="gr",
        letters="g and r",
        cards=["g", "r", "a", "p", "e"],
        clue="a purple stain on the helper's sleeve",
        noise="a rustle near the grapevine",
        useful="the mouth shape for the first two sounds",
        reveal="the rustle had been the helper hiding the cards from the wind",
        ending_image="the grape cards sat safe beside a basket of fruit and leaves",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Ada", "Pia"]
BOY_NAMES = ["Timo", "Bram", "Noel", "Evan", "Otis", "Arlo"]


def valid_combos() -> list[tuple[str, str]]:
    return [(lane_id, lesson_id) for lane_id in LANES for lesson_id in LESSONS]


def reasonableness_gate(lane_id: str, lesson_id: str) -> None:
    if lane_id not in LANES:
        raise StoryError("Unknown lane.")
    if lesson_id not in LESSONS:
        raise StoryError("Unknown phonics lesson.")


ASP_RULES = r"""
lane(L) :- lane_def(L).
lesson(X) :- lesson_def(X).
compatible(L, X) :- lane(L), lesson(X).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lane_id in LANES:
        lines.append(asp.fact("lane_def", lane_id))
    for lesson_id in LESSONS:
        lines.append(asp.fact("lesson_def", lesson_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like lane and phonics story world.")
    ap.add_argument("--lane", choices=LANES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["fox", "crow", "rabbit"])
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
    if args.lane and args.lesson:
        reasonableness_gate(args.lane, args.lesson)
    combos = [c for c in combos if (args.lane is None or c[0] == args.lane) and (args.lesson is None or c[1] == args.lesson)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    lane_id, lesson_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["fox", "crow", "rabbit"])
    return StoryParams(lane=lane_id, lesson=lesson_id, child_name=name, child_type=gender, helper_type=helper)


def _article(word: str) -> str:
    return "an" if word[0].lower() in "aeiou" else "a"


def tell(world: World, child: Entity, helper: Entity, lesson: PhonicsLesson) -> None:
    child.memes["curiosity"] = 1
    child.memes["joy"] = 1
    helper.memes["mystery"] = 1

    world.say(
        f"{child.id} was a little {child.type} who loved learning the sounds of words."
    )
    world.say(
        f"On {world.lane.name}, {child.id} and {child.pronoun('possessive')} teacher met to read {lesson.word}."
    )
    world.say(
        f"The teacher laid out cards for {lesson.letters}, and {child.id} smiled at the neat little row."
    )
    world.say(
        f"Still, {lesson.clue} made {child.id} pause. It was a small foreshadowing, like a whisper before rain."
    )
    world.para()
    world.say(
        f"{child.id} wanted to say the sounds at once, but a strange {lesson.noise} came from the lane."
    )
    helper.meters["nearby"] = 1
    helper.memes["suspicion"] = 1
    world.say(
        f"{child.id} thought the {helper.type} was being troublesome."
    )
    world.say(
        f"Then the helper spoke softly: 'Slow sounds make strong words.'"
    )
    world.say(
        f"The twist was kind, not mean: {lesson.reveal}."
    )
    world.para()
    child.memes["relief"] = 1
    child.memes["confidence"] = 1
    world.say(
        f"{child.id} took {lesson.useful} and said the sounds again, one by one."
    )
    world.say(
        f"This time the word came out clear, and the lesson stayed in {child.id}'s mind like a lantern on a path."
    )
    world.say(
        f"By the end, {lesson.ending_image}, and everyone on the lane laughed in a happy ending."
    )
    world.facts.update(child=child, helper=helper, lesson=lesson, lane=world.lane)


def generate_world(params: StoryParams) -> World:
    lane = LANES[params.lane]
    lesson = LESSONS[params.lesson]
    world = World(lane)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    helper = world.add(Entity(id=params.helper_type, kind="character", type=params.helper_type))
    teacher = world.add(Entity(id="teacher", kind="character", type="teacher", label="the teacher"))
    world.facts["teacher"] = teacher
    tell(world, child, helper, lesson)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    lesson = f["lesson"]
    helper = f["helper"]
    return [
        f"Write a short fable for children about a child on {world.lane.name} learning the word '{lesson.word}'.",
        f"Tell a gentle story in which {child.id} hears {lesson.sound} sounds, meets a {helper.type}, and learns to read carefully.",
        f"Write a happy-ending story with foreshadowing and a twist about phonics on a lane.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    lesson = f["lesson"]
    lane = f["lane"]
    return [
        QAItem(
            question=f"Who learned about the word '{lesson.word}' on the lane?",
            answer=f"{child.id}, a little {child.type}, learned it with the teacher on {lane.name}.",
        ),
        QAItem(
            question=f"What did the clue on the lane foreshadow?",
            answer=f"It foreshadowed that the noisy moment would not be trouble after all, because the helper had a good reason.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the {helper.type} seemed troublesome at first, but was actually helping keep the phonics cards safe and tidy.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {child.id} said the sounds clearly, remembered the lesson, and the cards stayed neat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    lesson = world.facts["lesson"]
    return [
        QAItem(
            question="What is phonics?",
            answer="Phonics is a way of learning to read by matching letters with the sounds they make.",
        ),
        QAItem(
            question="What is a lane?",
            answer="A lane is a small road or path, often quieter than a big street.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue that hints that something important will happen later.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes how you understand what was happening before.",
        ),
        QAItem(
            question=f"Why is the word '{lesson.word}' a good phonics word?",
            answer=f"It is a good phonics word because its sounds can be heard clearly when you say {lesson.letters}.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(lane="village", lesson="bright", child_name="Mina", child_type="girl", helper_type="fox"),
    StoryParams(lane="orchard", lesson="stone", child_name="Bram", child_type="boy", helper_type="crow"),
    StoryParams(lane="brook", lesson="grape", child_name="Ivy", child_type="girl", helper_type="rabbit"),
]


def asp_verify_world() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify_world())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible lane/lesson combos:\n")
        for lane_id, lesson_id in combos:
            print(f"  {lane_id:8} {lesson_id}")
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
            header = f"### {p.child_name}: {p.lesson} on {p.lane}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
