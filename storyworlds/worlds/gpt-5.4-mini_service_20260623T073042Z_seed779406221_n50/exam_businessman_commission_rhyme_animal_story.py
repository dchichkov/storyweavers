#!/usr/bin/env python3
"""
storyworlds/worlds/exam_businessman_commission_rhyme_animal_story.py
===================================================================

A small standalone storyworld in an Animal Story style.

Premise:
- An animal businessman commissions a rhyme for an exam-day show.
- The helper worries about making the rhyme good enough.
- The businessman checks the work, tension rises if the rhyme is too plain.
- A final revision turns the commission into a charming, memorable rhyme.

This world keeps the prose child-facing and concrete, while the simulated state
tracks both physical bits (meters) and emotions (memes). It also includes a
Python reasonableness gate plus an inline ASP twin.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "rooster"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class Scene:
    place: str
    exam: str
    commission: str
    rhyme_topic: str
    risk: str
    help_item: str
    help_label: str


@dataclass
class StoryParams:
    place: str
    businessman: str
    helper: str
    exam_style: str
    commission_kind: str
    seed: Optional[int] = None


PLACES = {
    "market": Scene(
        place="the market",
        exam="a speaking exam",
        commission="commission",
        rhyme_topic="a bright rhyme",
        risk="plain and dull",
        help_item="a bell",
        help_label="little bell chime",
    ),
    "school": Scene(
        place="the school hall",
        exam="an exam recital",
        commission="commission",
        rhyme_topic="a cheerful rhyme",
        risk="too stiff",
        help_item="a drum",
        help_label="soft drum beat",
    ),
    "fair": Scene(
        place="the town fair",
        exam="a talent exam",
        commission="commission",
        rhyme_topic="a funny rhyme",
        risk="too short",
        help_item="a tambourine",
        help_label="tiny tambourine jingle",
    ),
}

BUSINESSMEN = {
    "fox": Entity(id="fox", kind="character", type="fox", label="Mr. Fox"),
    "bear": Entity(id="bear", kind="character", type="bear", label="Mr. Bear"),
    "hare": Entity(id="hare", kind="character", type="hare", label="Mr. Hare"),
}

HELPERS = {
    "mouse": Entity(id="mouse", kind="character", type="mouse", label="Mina Mouse"),
    "duck": Entity(id="duck", kind="character", type="duck", label="Dora Duck"),
    "cat": Entity(id="cat", kind="character", type="cat", label="Cleo Cat"),
}

EXAMS = {
    "speech": "speech exam",
    "song": "song exam",
    "recite": "recite exam",
}

COMMISSION_KINDS = {
    "rhyme": "rhyme",
    "jingle": "jingle",
    "poem": "poem",
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (place, biz, helper, exam)
        for place in PLACES
        for biz in BUSINESSMEN
        for helper in HELPERS
        for exam in EXAMS
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story style: an exam, a businessman, and a rhyme commission.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--businessman", choices=BUSINESSMEN)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--exam-style", choices=EXAMS)
    ap.add_argument("--commission-kind", choices=COMMISSION_KINDS)
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
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.businessman is None or c[1] == args.businessman)
        and (args.helper is None or c[2] == args.helper)
        and (args.exam_style is None or c[3] == args.exam_style)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, biz, helper, exam = rng.choice(sorted(combos))
    if args.commission_kind and args.commission_kind != "rhyme":
        raise StoryError("(This world only supports rhyme commissions.)")
    return StoryParams(
        place=place,
        businessman=biz,
        helper=helper,
        exam_style=exam,
        commission_kind="rhyme",
    )


def story_label(entity: Entity) -> str:
    return entity.label_word


def tell(scene: Scene, biz: Entity, helper: Entity, exam_style: str) -> World:
    w = World()
    biz = w.add(Entity(**biz.__dict__))
    helper = w.add(Entity(**helper.__dict__))
    exam = w.add(Entity(id="exam", kind="thing", type="exam", label=EXAMS[exam_style]))
    w.add(Entity(id="work", kind="thing", type="thing", label="the rhyme page"))
    w.facts["scene"] = scene
    w.facts["biz"] = biz
    w.facts["helper"] = helper
    w.facts["exam"] = exam

    for e in (biz, helper, exam):
        e.meters.setdefault("ready", 0.0)
        e.meters.setdefault("plain", 0.0)
        e.meters.setdefault("bright", 0.0)
        e.memes.setdefault("pride", 0.0)
        e.memes.setdefault("worry", 0.0)
        e.memes.setdefault("joy", 0.0)
        e.memes.setdefault("confidence", 0.0)

    biz.meters["ready"] = 1.0
    helper.memes["worry"] = 1.0
    helper.memes["confidence"] = 0.5

    w.say(f"At {scene.place}, {biz.label} had a {scene.commission} for {scene.exam}.")
    w.say(f"{biz.label} wanted {scene.rhyme_topic} that would not sound {scene.risk}.")
    w.para()
    w.say(f"{helper.label} wrote under a tree and hummed a soft line.")
    helper.meters["plain"] += 1.0
    helper.memes["worry"] += 0.5
    if helper.meters["plain"] >= THRESHOLD:
        w.say(f"But the first verse felt a little {scene.risk}.")
    w.para()
    w.say(f"{biz.label} frowned and tapped the page with a hoof.")
    biz.memes["pride"] += 0.5
    if helper.memes["worry"] >= THRESHOLD:
        w.say(f"{helper.label} looked down, then tried again with a brighter tune.")
    helper.meters["bright"] += 1.0
    helper.memes["confidence"] += 1.0
    w.say(f"This time, the rhyme rang with {scene.help_label}.")
    w.para()
    biz.memes["joy"] += 1.0
    w.say(f"{biz.label} smiled, paid the coin, and carried the rhyme to {scene.exam}.")
    w.say(f"At the exam, the rhyme shone sweet and light, and every ear felt right.")
    w.facts["resolved"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene: Scene = f["scene"]
    biz: Entity = f["biz"]
    helper: Entity = f["helper"]
    return [
        f"Write a short Animal Story about {biz.label} making a {scene.commission} for {scene.exam} at {scene.place}.",
        f"Tell a gentle story where {helper.label} helps {biz.label} with a {COMMISSION_KINDS['rhyme']} so the exam goes well.",
        f"Write a child-friendly rhyme story that includes the words exam, businessman, and commission.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scene: Scene = f["scene"]
    biz: Entity = f["biz"]
    helper: Entity = f["helper"]
    exam: Entity = f["exam"]
    return [
        QAItem(
            question=f"Who asked for the rhyme commission at {scene.place}?",
            answer=f"{biz.label} did. {biz.label} was the businessman and wanted a rhyme for {exam.label}.",
        ),
        QAItem(
            question=f"Who helped make the rhyme better?",
            answer=f"{helper.label} helped. {helper.label} kept trying until the rhyme sounded bright and ready.",
        ),
        QAItem(
            question=f"What was the story's exam?",
            answer=f"It was {exam.label}, and the rhyme was meant to shine at that exam.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{biz.label} paid for the commission, and the rhyme sounded sweet and clever at the exam.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a commission?", answer="A commission is a job someone asks another person to do for them."),
        QAItem(question="What is an exam?", answer="An exam is a test or performance where someone shows what they can do."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a set of words that sound musical or match at the end."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} label={e.label}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,B,H,E) :- place(P), businessman(B), helper(H), exam(E).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for b in BUSINESSMEN:
        lines.append(asp.fact("businessman", b))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for e in EXAMS:
        lines.append(asp.fact("exam", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    scene = PLACES[params.place]
    biz = BUSINESSMEN[params.businessman]
    helper = HELPERS[params.helper]
    world = tell(scene, biz, helper, params.exam_style)
    story = (
        f"At {scene.place}, {biz.label} had a {scene.commission} for {scene.exam}. "
        f"{helper.label} wrote a rhyme that began plain, then grew bright. "
        f"In the end, the rhyme rang with a soft tune, and the exam went well."
    )
    return StorySample(
        params=params,
        story=world.render() or story,
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("market", "fox", "mouse", "speech"),
            StoryParams("school", "bear", "duck", "song"),
            StoryParams("fair", "hare", "cat", "recite"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
