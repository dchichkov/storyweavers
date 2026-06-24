#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child learning a rhyme, making a
hypothesis, and discovering how a careful guess can become a happy answer.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = True
    time_of_day: str = "afternoon"


@dataclass
class Topic:
    id: str
    object_label: str
    object_phrase: str
    sound: str
    lesson: str
    guess: str
    surprise: str
    rhyme_word: str
    clue_word: str
    final_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    topic: str
    name: str
    age: int
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen_table": Setting(place="the kitchen table", indoor=True, time_of_day="after lunch"),
    "classroom_corner": Setting(place="the classroom reading corner", indoor=True, time_of_day="morning"),
    "living_room_rug": Setting(place="the living room rug", indoor=True, time_of_day="late afternoon"),
}

TOPICS = {
    "bell": Topic(
        id="bell",
        object_label="bell",
        object_phrase="a little silver bell",
        sound="ding",
        lesson="sound can help us notice what is near us",
        guess="the bell was probably in the basket",
        surprise="the bell was tucked inside the blue cup",
        rhyme_word="bell",
        clue_word="swell",
        final_word="well",
        tags={"sound", "rhyme", "guess"},
    ),
    "shell": Topic(
        id="shell",
        object_label="shell",
        object_phrase="a striped shell from the window sill",
        sound="shh",
        lesson="small clues can tell a big story",
        guess="the shell was probably under the cloth",
        surprise="the shell was sitting in the red bowl",
        rhyme_word="shell",
        clue_word="smell",
        final_word="well",
        tags={"clue", "rhyme", "guess"},
    ),
    "pencil": Topic(
        id="pencil",
        object_label="pencil",
        object_phrase="a short yellow pencil",
        sound="scritch",
        lesson="careful thinking can help you find a missing thing",
        guess="the pencil was probably behind the book",
        surprise="the pencil was resting by the cup",
        rhyme_word="pencil",
        clue_word="stencil",
        final_word="still",
        tags={"clue", "rhyme", "guess"},
    ),
}

HELPERS = {
    "mother": ("mother", "mom"),
    "father": ("father", "dad"),
    "sister": ("sister", "big sister"),
    "brother": ("brother", "big brother"),
    "teacher": ("teacher", "teacher"),
}

NAMES = ["Mia", "Noah", "Lily", "Theo", "Nina", "Eli", "Ava", "Milo"]
AGES = [4, 5, 6, 7]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, topic) for place in SETTINGS for topic in TOPICS]


def rhyming_line(topic: Topic, name: str) -> str:
    return f"{name} hummed, “{topic.rhyme_word}, {topic.rhyme_word}, what a fine little sight; maybe the missing thing is hiding just right.”"


def rhyme_clue(topic: Topic) -> str:
    return f"“If it rhymes with {topic.rhyme_word}, it might be nearby,” the helper said."


def hypothesize_line(topic: Topic, name: str) -> str:
    return f"{name} thought, I can hypothesize a place to look first. Maybe the {topic.object_label} is in the wrong spot."


def educate_line(topic: Topic, helper_label: str) -> str:
    return f"{helper_label} explained that a good guess uses clues, not just hope, because {topic.lesson}."


def inner_monologue_line(name: str, topic: Topic) -> str:
    return f"{name} thought, I want to be careful. If I rush, I might miss the clue that makes everything click."


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    topic = TOPICS[params.topic]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mia", "Lily", "Nina", "Ava"} else "boy"))
    helper_key = params.helper
    helper_type, helper_label = HELPERS[helper_key]
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_label))
    obj = world.add(Entity(id="object", kind="thing", type=topic.object_label, label=topic.object_label, phrase=topic.object_phrase, owner=helper.id))

    child.memes["curiosity"] = 1
    child.memes["calm"] = 0.5
    helper.memes["patience"] = 1

    world.say(f"{child.id} was sitting at {setting.place} when {helper.label} brought out {topic.object_phrase}.")
    world.say(f"{child.id} loved the tiny shine of it, and {helper.label} said it was time to educate and play detective for a minute.")
    world.para()
    world.say(rhyming_line(topic, child.id))
    world.say(inner_monologue_line(child.id, topic))
    world.say(f"{child.id} listened to the soft {topic.sound} sound and looked around the room.")
    world.para()
    world.say(educate_line(topic, helper.label))
    world.say(rhyme_clue(topic))
    world.say(f"{child.id} smiled and said, “Then I will hypothesize that it is near the cups, because the clue feels steady.”")
    world.say(hypothesize_line(topic, child.id))

    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["object"] = obj
    world.facts["topic"] = topic
    world.facts["setting"] = setting
    world.facts["guess"] = topic.guess
    world.facts["surprise"] = topic.surprise

    world.para()
    world.say(f"They checked the cups together. The object was not there.")
    child.memes["disappointment"] = 0.5
    child.memes["resolve"] = 1
    world.say(f"{child.id} took a breath and kept thinking, because a good hypothesis can be changed when a clue says so.")
    world.say(f"Then {child.id} noticed a small shine where the light fell across the room.")
    world.say(f"That was the answer: {topic.surprise}.")
    obj.meters["found"] = 1
    child.meters["search_steps"] = 3
    child.memes["joy"] = 1
    helper.memes["pride"] = 1
    world.say(f"{child.id} pointed and laughed, and {helper.label} clapped softly.")
    world.say(f"“Your guess was thoughtful,” {helper.label} said, “and your new clue made it better.”")
    world.say(f"{child.id} tucked the {topic.object_label} back in place and felt smart and calm, like a small bell ringing in a quiet room.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    topic = f["topic"]
    helper = f["helper"]
    return [
        f'Write a slice-of-life story for a young child about "{topic.id}" and a careful guess.',
        f"Tell a gentle story where {child.id} tries to hypothesize where a missing {topic.object_label} is, while {helper.label} helps educate them.",
        f"Write a short story that includes a rhyme about {topic.rhyme_word} and ends with the child finding the {topic.object_label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    topic = f["topic"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who was the story about at {setting.place}?",
            answer=f"It was about {child.id}, who was spending a quiet moment with {helper.label} at {setting.place}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the {topic.object_label}?",
            answer=f"{child.id} wanted to think carefully, make a hypothesis, and find where the {topic.object_label} was hidden.",
        ),
        QAItem(
            question=f"What did {helper.label} teach {child.id} about guessing?",
            answer=f"{helper.label} taught that a good guess should use clues, because {topic.lesson}.",
        ),
        QAItem(
            question=f"What was the child’s first idea about the missing {topic.object_label}?",
            answer=f"{child.id} first guessed that {topic.guess}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} finding the {topic.object_label} in the place that matched the last clue and feeling proud of the careful thinking.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    topic = f["topic"]
    return [
        QAItem(
            question="What does it mean to hypothesize?",
            answer="To hypothesize means to make a thoughtful guess about what is true, often by using clues and then checking them.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bell and well.",
        ),
        QAItem(
            question=f"Why can a clue help find a {topic.object_label}?",
            answer="A clue can point attention to the right place, so the search becomes easier and less random.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
topic( bell ). topic( shell ). topic( pencil ).
place( kitchen_table ). place( classroom_corner ). place( living_room_rug ).

compatible(P, T) :- place(P), topic(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TOPICS:
        lines.append(asp.fact("topic", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(a - b))
    print("  only in python:", sorted(b - a))
    return 1


CURATED = [
    StoryParams(place="kitchen_table", topic="bell", name="Mia", age=5, helper="mother"),
    StoryParams(place="classroom_corner", topic="shell", name="Noah", age=6, helper="teacher"),
    StoryParams(place="living_room_rug", topic="pencil", name="Lily", age=4, helper="sister"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about educate, hypothesize, rhyme, and inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--name")
    ap.add_argument("--age", type=int)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.topic:
        combos = [c for c in combos if c[1] == args.topic]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, topic = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    age = args.age or rng.choice(AGES)
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=place, topic=topic, name=name, age=age, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, topic) combos:\n")
        for place, topic in combos:
            print(f"  {place:18} {topic}")
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
            header = f"### {p.name}: {p.topic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
