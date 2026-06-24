#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100/speaker_approximate_basics_lesson_learned_heartwarming.py
==============================================================================================================

A small heartwarming story world about a shy speaker, approximate answers,
and a lesson learned about getting the basics right.

The seed image for this world:
- A child is asked to speak up in front of others.
- The child tries to give approximate answers because exactness feels scary.
- A gentle helper shows that approximate is okay for some things, but the
  basics still matter.
- The child learns a kinder way to speak, and the room feels warmer at the end.

This script models a tiny simulation with physical meters and emotional memes.
It supports the standard storyworld CLI, plus an inline ASP twin for parity
checks and explainable constraints.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    touched_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Topic:
    id: str
    label: str
    keyword: str
    what_it_is: str
    basics: str
    approximate: str
    lesson: str
    challenge: str
    answer_style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    is_speaker: bool = False
    plural: bool = False


@dataclass
class World:
    setting: Setting

    def __post_init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.noise: float = 0.0

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.noise = self.noise
        return w


def _r_nervous_mumble(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.memes.get("nervous", 0.0) < THRESHOLD:
            continue
        if ("mumble", ent.id) in world.fired:
            continue
        world.fired.add(("mumble", ent.id))
        ent.memes["confidence"] = ent.memes.get("confidence", 0.0) - 0.25
        out.append(f"{ent.id} kept speaking softly and tripping over a few words.")
    return out


def _r_honest_help(world: World) -> list[str]:
    out = []
    teacher = world.entities.get("Teacher")
    child = world.entities.get("Child")
    if not teacher or not child:
        return out
    if child.memes.get("confused", 0.0) < THRESHOLD:
        return out
    if ("help", child.id) in world.fired:
        return out
    world.fired.add(("help", child.id))
    child.memes["confidence"] = child.memes.get("confidence", 0.0) + 1
    teacher.memes["warmth"] = teacher.memes.get("warmth", 0.0) + 1
    out.append("The teacher smiled and helped with the first small words.")
    return out


def _r_lesson_learned(world: World) -> list[str]:
    out = []
    child = world.entities.get("Child")
    if not child:
        return out
    if child.memes.get("confidence", 0.0) < 1 or child.memes.get("warmth", 0.0) < 1:
        return out
    if ("lesson", child.id) in world.fired:
        return out
    world.fired.add(("lesson", child.id))
    child.memes["learned"] = 1
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    out.append("The child learned that it was all right to say about when a number was not known exactly.")
    return out


CAUSAL_RULES = [_r_nervous_mumble, _r_honest_help, _r_lesson_learned]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "classroom": Setting(place="the classroom", indoor=True, affords={"speaking", "counting"}),
    "library": Setting(place="the library corner", indoor=True, affords={"speaking", "counting"}),
    "kitchen": Setting(place="the kitchen table", indoor=True, affords={"speaking", "counting"}),
}

TOPICS = {
    "speaker": Topic(
        id="speaker",
        label="speaker",
        keyword="speaker",
        what_it_is="A speaker is someone who talks so others can hear and understand.",
        basics="The basics of speaking are using a clear voice, simple words, and a calm breath.",
        approximate="Approximate means close enough for now, even if it is not exact.",
        lesson="Sometimes the kindest answer is an approximate one, as long as the basics are still clear.",
        challenge="The child worries about saying the wrong number out loud.",
        answer_style="gentle",
        tags={"speaker", "speech"},
    ),
    "approximate": Topic(
        id="approximate",
        label="approximate",
        keyword="about",
        what_it_is="Approximate means near the truth, but not exactly exact.",
        basics="You can be approximate when a little closeness is enough.",
        approximate="About is a useful word when you do not know the exact number.",
        lesson="It is okay to be close when the exact answer is hard.",
        challenge="The child wants to sound right without freezing up.",
        answer_style="soft",
        tags={"approximate", "numbers"},
    ),
    "basics": Topic(
        id="basics",
        label="basics",
        keyword="basics",
        what_it_is="Basics are the simple first things that help you begin well.",
        basics="Basics include listening, saying one idea at a time, and asking for help.",
        approximate="Even when the answer is approximate, the basics still matter.",
        lesson="A warm helper can make the basics feel safe.",
        challenge="The child forgets the first simple steps and gets stuck.",
        answer_style="clear",
        tags={"basics", "learning"},
    ),
}

PROPS = {
    "card": Prop(id="card", label="cue card", phrase="a little cue card", type="card"),
    "mike": Prop(id="mike", label="toy microphone", phrase="a tiny toy microphone", type="microphone", is_speaker=True),
    "blocks": Prop(id="blocks", label="counting blocks", phrase="three small counting blocks", type="blocks", plural=True),
}

NAMES = ["Mina", "Theo", "Luna", "Ivy", "Owen", "Nora"]
ADJ = ["shy", "careful", "kind", "curious", "gentle", "brave"]


@dataclass
class StoryParams:
    place: str
    topic: str
    prop: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about a speaker, approximate answers, and basics learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=ADJ)
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
    out = []
    for place in SETTINGS:
        for topic in TOPICS:
            for prop in PROPS:
                if topic == "speaker" and prop in {"mike", "card"}:
                    out.append((place, topic, prop))
                elif topic == "approximate" and prop in {"card", "blocks"}:
                    out.append((place, topic, prop))
                elif topic == "basics" and prop in {"card", "blocks"}:
                    out.append((place, topic, prop))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.topic is None or c[1] == args.topic)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, topic, prop = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(ADJ)
    return StoryParams(place=place, topic=topic, prop=prop, name=name, trait=trait)


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="Child", kind="character", type="child", label=params.name))
    teacher = world.add(Entity(id="Teacher", kind="character", type="adult", label="the teacher"))
    prop = world.add(Entity(id="Prop", kind="thing", type=PROPS[params.prop].type,
                            label=PROPS[params.prop].label, phrase=PROPS[params.prop].phrase))
    child.memes["nervous"] = 1
    child.memes["confused"] = 1
    teacher.memes["warmth"] = 1
    world.facts.update(child=child, teacher=teacher, prop=prop, params=params, topic=TOPICS[params.topic])
    return world


def tell(world: World, params: StoryParams) -> World:
    child = world.get("Child")
    teacher = world.get("Teacher")
    prop = world.get("Prop")
    topic = TOPICS[params.topic]

    world.say(f"{params.name} was a {params.trait} child who became the speaker whenever it was time to share ideas.")
    world.say(f"At {world.setting.place}, {params.name} held {prop.phrase} and tried to remember the basics.")
    world.say(f"{topic.what_it_is} {topic.basics}")

    world.para()
    world.say(f"Today, the lesson was about {topic.keyword}.")
    world.say(f"{params.name} wanted to help, but {child.pronoun('subject')} felt nervous and kept looking at {prop.label}.")
    world.say(f"{params.name} whispered, 'Is it okay if I only say {topic.approximate.lower()}?'")
    child.memes["confused"] += 0.5
    propagate(world)

    world.para()
    world.say(f"The teacher knelt down beside {params.name} and said that {topic.approximate.lower()} could be a kind answer.")
    world.say(f"Then the teacher showed the basics again, one small step at a time, so the room felt easy instead of scary.")
    teacher.memes["warmth"] += 1
    child.memes["confused"] += 1
    child.memes["nervous"] -= 0.5
    propagate(world)

    world.para()
    if child.memes.get("learned", 0.0) >= THRESHOLD:
        world.say(f"{params.name} took a breath, spoke clearly, and said, 'It's about {prop.label}, and the basics matter.'")
        world.say(f"After that, {params.name} smiled, because {topic.lesson.lower()} The teacher smiled back, and the whole room felt warmer.")
    else:
        world.say(f"{params.name} still needed a little help, but the teacher stayed nearby and promised to practice again tomorrow.")

    world.facts["topic"] = topic
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    topic = world.facts["topic"]
    return [
        f"Write a heartwarming story about a {p.trait} child who speaks up using the word '{topic.keyword}'.",
        f"Tell a gentle story where {p.name} learns that approximate answers can still be kind and helpful.",
        f"Write a simple story about a speaker, approximate ideas, and the basics of a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    topic = world.facts["topic"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a {p.trait} child who tries to be a good speaker during a lesson at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {p.name} want to say about {topic.keyword}?",
            answer=f"{p.name} wanted to give an approximate answer and say something close enough without getting stuck on every exact detail.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=f"{p.name} learned that it is okay to use an approximate answer, but the basics still matter and a calm helper can make speaking feel safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    topic = world.facts["topic"]
    return [
        QAItem(question="What is a speaker?", answer=topic.what_it_is),
        QAItem(question="What does approximate mean?", answer=topic.approximate),
        QAItem(question="What are basics?", answer=topic.basics),
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
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.kind:8}) meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(Place,Topic,Prop) :- place(Place), topic(Topic), prop(Prop),
    ok_pair(Topic,Prop).

ok_pair(speaker,mike).
ok_pair(speaker,card).
ok_pair(approximate,card).
ok_pair(approximate,blocks).
ok_pair(basics,card).
ok_pair(basics,blocks).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in TOPICS:
        lines.append(asp.fact("topic", t))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(ac - py))
    print("  only in python:", sorted(py - ac))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    world = tell(world, params)
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
    StoryParams(place="classroom", topic="speaker", prop="mike", name="Mina", trait="shy"),
    StoryParams(place="library", topic="approximate", prop="card", name="Theo", trait="careful"),
    StoryParams(place="kitchen", topic="basics", prop="blocks", name="Luna", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
