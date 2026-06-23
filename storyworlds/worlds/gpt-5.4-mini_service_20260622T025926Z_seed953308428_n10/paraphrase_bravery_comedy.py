#!/usr/bin/env python3
"""
storyworlds/worlds/paraphrase_bravery_comedy.py
===============================================

A tiny comedy storyworld about a child who needs bravery to deliver a
paraphrased line without getting tangled in their own words.

Seed tale:
---
Nina had to tell a story to the class, but she was nervous. Her teacher asked
her to paraphrase the main idea in one sentence. Nina took a deep breath, stood
up, and bravely tried again. She mixed up a few words, made the class giggle,
then found a funny, clear way to say it. The teacher smiled and said the brave
part was trying, not sounding perfect.
---

The world model tracks:
- a child with bravery, nerves, and joy
- a small object or prop used in the explanation
- a teacher who can prompt a paraphrase
- a simple comedy turn where a mistaken paraphrase becomes a confident one

The prose is state-driven: the child starts nervous, attempts the paraphrase,
the attempt may become a comic stumble, and bravery increases once the child
finishes speaking anyway.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    noise: str
    prop: str
    prop_phrase: str
    prop_use: str
    lesson: str
    comic_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    hero_name: str
    hero_gender: str
    teacher_name: str
    prop: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        clone = World(self.scene)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            role=v.role, attrs=dict(v.attrs), tags=set(v.tags),
            meters=defaultdict(float, v.meters), memes=defaultdict(float, v.memes),
            plural=v.plural,
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_laughter(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    class_ = world.entities.get("class")
    if not hero or not class_:
        return out
    if hero.meters["stumble"] >= THRESHOLD and ("laugh" not in world.fired):
        world.fired.add(("laugh",))
        class_.memes["amusement"] += 1
        hero.memes["embarrassment"] += 1
        out.append("The class giggled.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    teacher = world.entities.get("teacher")
    if not hero or not teacher:
        return out
    if hero.memes["attempted"] >= THRESHOLD and ("brave_up",) not in world.fired:
        world.fired.add(("brave_up",))
        hero.memes["bravery"] += 1
        teacher.memes["pride"] += 1
        out.append("The brave try counted more than perfect words.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_laughter, _r_bravery):
            got = rule(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SCENES = {
    "classroom": Scene(
        place="the classroom",
        noise="the chalkboard squeaked and desks waited in neat rows",
        prop="book",
        prop_phrase="a small picture book",
        prop_use="page",
        lesson="paraphrase",
        comic_image="the words came out like three marbles in a sock",
        tags={"school", "book", "paraphrase"},
    ),
    "library": Scene(
        place="the library",
        noise="the carpet was soft and the shelves stood tall and quiet",
        prop="poster",
        prop_phrase="a funny poster with a cat on it",
        prop_use="corner",
        lesson="paraphrase",
        comic_image="the sentence bounced off her tongue and landed in a heap",
        tags={"school", "poster", "paraphrase"},
    ),
    "music_room": Scene(
        place="the music room",
        noise="the piano sat shiny and the drum wore a tiny hat",
        prop="drum",
        prop_phrase="a little drum with a red ribbon",
        prop_use="rim",
        lesson="paraphrase",
        comic_image="the brave sentence marched in wearing the wrong shoes",
        tags={"music", "drum", "paraphrase"},
    ),
}

PROPS = {
    "book": {"label": "book", "tags": {"book", "paper"}},
    "poster": {"label": "poster", "tags": {"poster", "paper"}},
    "drum": {"label": "drum", "tags": {"drum", "music"}},
}

GIRL_NAMES = ["Nina", "Maya", "Lily", "Ava", "Zoe", "Mia"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Owen", "Sam"]
TEACHERS = ["Ms. Reed", "Mr. Fox", "Mrs. Lane", "Ms. Pine"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for scene in SCENES:
        for prop in PROPS:
            combos.append((scene, prop))
    return combos


@dataclass
class State:
    hero: Entity
    teacher: Entity
    class_: Entity
    prop: Entity
    scene: Scene


def setup_world(params: StoryParams) -> World:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.prop not in PROPS:
        raise StoryError("Unknown prop.")
    scene = SCENES[params.scene]
    world = World(scene)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender,
                            label=params.hero_name, role="child",
                            attrs={"name": params.hero_name}))
    teacher = world.add(Entity(id="teacher", kind="character", type="teacher",
                               label=params.teacher_name, role="teacher"))
    class_ = world.add(Entity(id="class", kind="group", type="group",
                              label="the class", role="audience", plural=True))
    prop_cfg = PROPS[params.prop]
    prop = world.add(Entity(id="prop", kind="thing", type="thing",
                            label=prop_cfg["label"], phrase=scene.prop_phrase,
                            tags=set(prop_cfg["tags"])))
    hero.memes["nerves"] = 2.0
    hero.memes["bravery"] = 1.0
    teacher.memes["patience"] = 1.0
    world.facts.update(scene=scene, hero=hero, teacher=teacher, class_=class_, prop=prop)
    return world


def tell(world: World) -> None:
    hero = world.get("hero")
    teacher = world.get("teacher")
    class_ = world.get("class")
    prop = world.get("prop")
    scene = world.scene

    world.say(
        f"{hero.label} was in {scene.place}, where {scene.noise}. "
        f"{teacher.label} pointed to {prop.phrase} and asked for a paraphrase."
    )
    world.say(
        f"{hero.label} took a breath and looked at the {prop.label}. "
        f"{hero.pronoun().capitalize()} wanted to be brave, but the sentence kept wiggling."
    )

    world.para()
    hero.memes["attempted"] += 1
    hero.meters["stumble"] += 1
    world.say(
        f"{hero.label} tried anyway. {scene.comic_image}, and {class_.label} snorted with laughter."
    )
    propagate(world, narrate=True)

    world.para()
    hero.meters["stumble"] = 0.0
    hero.memes["bravery"] += 1
    hero.memes["joy"] += 1
    teacher.memes["pride"] += 1
    world.say(
        f"Then {hero.label} straightened up and tried again. "
        f"{hero.label} gave a clear paraphrase, and this time the meaning landed neatly."
    )
    world.say(
        f"{teacher.label} smiled and said the brave part was speaking up, not sounding perfect."
    )
    world.say(
        f"{hero.label} grinned at the end, standing tall beside the {prop.label}."
    )

    world.facts.update(resolved=True, comic=scene.comic_image, lesson=scene.lesson)


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    teacher: Entity = f["teacher"]
    prop: Entity = f["prop"]
    scene: Scene = f["scene"]
    return [
        f'Write a funny story for a young child about {hero.label} in {scene.place} who must say a paraphrase about {prop.label}.',
        f"Tell a comedy story where {teacher.label} asks {hero.label} to paraphrase an idea, and brave practice makes the class laugh kindly.",
        f'Write a short school story using the word "paraphrase" where a nervous child becomes brave and finishes the sentence anyway.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    teacher: Entity = f["teacher"]
    prop: Entity = f["prop"]
    scene: Scene = f["scene"]
    return [
        QAItem(
            question=f"Who had to paraphrase in {scene.place}?",
            answer=f"{hero.label} had to paraphrase for {teacher.label}. {hero.label} was nervous at first, but {hero.label} kept trying.",
        ),
        QAItem(
            question=f"Why did the class laugh when {hero.label} tried the first paraphrase?",
            answer=f"{scene.comic_image.capitalize()}. The class laughed because the first try sounded silly, but it was still brave to try.",
        ),
        QAItem(
            question=f"What helped {hero.label} finish the paraphrase at the end?",
            answer=f"Bravery helped {hero.label} finish. After the comic stumble, {hero.label} took another breath and said the idea clearly beside the {prop.label}.",
        ),
        QAItem(
            question=f"What did {teacher.label} think mattered most?",
            answer=f"{teacher.label} thought the brave part mattered most. {teacher.label} cared more about trying again than about getting every word perfect.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene: Scene = f["scene"]
    out = [
        QAItem(
            question="What does paraphrase mean?",
            answer="To paraphrase means to say the same idea in different words. It helps you explain something clearly without copying it exactly.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel nervous. A brave person can take a breath and keep going anyway.",
        ),
    ]
    if "school" in scene.tags:
        out.append(QAItem(
            question="Why do teachers ask for paraphrases?",
            answer="Teachers ask for paraphrases to see if a child understands the idea. It also helps children practice explaining the idea in their own words.",
        ))
    if "music" in scene.tags:
        out.append(QAItem(
            question="Why can a music room feel funny for speaking practice?",
            answer="A music room can feel funny because it already has rhythms and odd sounds. That can make a brave sentence seem even sillier in a playful way.",
        ))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_attempted :- hero_meme(attempted, V), V >= 1.
comic_laugh :- hero_meter(stumble, V), V >= 1.
bravery_grows :- hero_meme(attempted, V), V >= 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for name in GIRL_NAMES + BOY_NAMES + TEACHERS:
        lines.append(asp.fact("name", name))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/2."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    # Minimal parity/smoke gate: verify generation, JSON, QA, and ASP access.
    rc = 0
    try:
        sample = generate(resolve_params(argparse.Namespace(
            scene=None, hero_name=None, hero_gender=None, teacher_name=None, prop=None,
            n=1, seed=None, all=False, trace=False, qa=False, json=False,
            asp=False, verify=False, show_asp=False
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1
    try:
        import asp
        _ = asp_program("#show scene/1.")
    except Exception as e:
        print(f"ASP FAIL: {e}")
        rc = 1

    # Run multiple deterministic generations and ensure distinct QA/stories.
    seeds = [1, 2, 3]
    stories = []
    qa_blobs = []
    for s in seeds:
        args = build_parser().parse_args(["--seed", str(s)])
        params = resolve_params(args, random.Random(s))
        sample = generate(params)
        stories.append(sample.story)
        qa_blobs.append(format_qa(sample))
    if len(set(stories)) < 2:
        print("SMOKE FAIL: stories are not varying enough.")
        rc = 1
    if len(set(qa_blobs)) < 2:
        print("SMOKE FAIL: QA is not varying enough.")
        rc = 1

    # Exercise the remaining requested entry paths.
    try:
        args = build_parser().parse_args(["-n", "3", "--seed", "777", "--qa"])
        for i in range(3):
            params = resolve_params(args, random.Random(777 + i))
            sample = generate(params)
            if not sample.prompts or not sample.story_qa or not sample.world_qa:
                raise RuntimeError("missing QA content")
        _ = json.dumps([generate(resolve_params(build_parser().parse_args([]), random.Random(9))).to_dict()])
    except Exception as e:
        print(f"SMOKE FAIL: {e}")
        return 1

    print("OK: smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A funny storyworld about bravely paraphrasing.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--teacher-name", choices=TEACHERS)
    ap.add_argument("--prop", choices=PROPS)
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
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.prop is None or c[1] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, prop = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    teacher_name = args.teacher_name or rng.choice(TEACHERS)
    return StoryParams(
        scene=scene,
        hero_name=hero_name,
        hero_gender=hero_gender,
        teacher_name=teacher_name,
        prop=prop,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.prop not in PROPS:
        raise StoryError("Invalid params.")
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(scene="classroom", hero_name="Nina", hero_gender="girl", teacher_name="Ms. Reed", prop="book", seed=1),
    StoryParams(scene="library", hero_name="Ben", hero_gender="boy", teacher_name="Mr. Fox", prop="poster", seed=2),
    StoryParams(scene="music_room", hero_name="Maya", hero_gender="girl", teacher_name="Mrs. Lane", prop="drum", seed=3),
]


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
        print(asp_program("#show combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP combos are intentionally simple in this world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
