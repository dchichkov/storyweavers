#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/avatar_romantic_bias_misunderstanding_lesson_learned_rhyming.py
================================================================================================

A standalone storyworld for a small rhyming tale about an avatar, a romantic
misunderstanding, and a lesson learned.

The world models a tiny social scene:
- an avatar with physical state in meters and emotional state in memes,
- a romantic mix-up caused by a biased assumption,
- a misunderstanding that can be corrected by a clear message,
- a lesson learned ending that changes the emotional state and the final image.

The prose aims to feel like a short rhyming story, but still be driven by state:
what the avatar sees, assumes, says, and learns determines the ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

# Make shared containers importable when run directly.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Interest:
    id: str
    verb: str
    gerund: str
    clue: str
    romantic_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    interest: str
    avatar_name: str
    avatar_type: str
    admirer_name: str
    admirer_type: str
    bias: str
    seed: Optional[int] = None


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
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "garden": Setting("the garden", "soft and bright", {"talk", "meet"}),
    "cafe": Setting("the cafe", "warm and small", {"talk", "meet", "note"}),
    "bridge": Setting("the bridge", "windy and wide", {"talk", "meet"}),
}

INTERESTS = {
    "letter": Interest(
        id="letter",
        verb="write a little note",
        gerund="writing little notes",
        clue="a folded note",
        romantic_hint="a kind message",
        tags={"note", "romantic"},
    ),
    "song": Interest(
        id="song",
        verb="sing a sweet song",
        gerund="singing sweet songs",
        clue="a soft tune",
        romantic_hint="a warm rhyme",
        tags={"music", "romantic"},
    ),
    "flower": Interest(
        id="flower",
        verb="pick a flower",
        gerund="picking flowers",
        clue="a bright bloom",
        romantic_hint="a gentle gift",
        tags={"garden", "romantic"},
    ),
}

BIAS_WORDS = {
    "shy": "The avatar thought shyness meant no caring at all.",
    "busy": "The avatar thought a busy look meant a cold heart.",
    "quiet": "The avatar thought quiet faces never felt romance.",
}

GREETINGS = {
    "girl": "smiled",
    "boy": "smiled",
    "person": "smiled",
}


def rhyming_close(word: str) -> str:
    return {
        "letter": "better",
        "song": "long",
        "flower": "glow-er",
    }.get(word, "bright")


def predict_misunderstanding(world: World, avatar: Entity, admirer: Entity, interest: Interest) -> bool:
    sim = world.copy()
    sim.facts["bias"] = world.facts["bias"]
    return True if sim.facts["bias"] in BIAS_WORDS else False


def tell(setting: Setting, interest: Interest, avatar_name: str, avatar_type: str,
         admirer_name: str, admirer_type: str, bias: str) -> World:
    world = World(setting)
    avatar = world.add(Entity(
        id=avatar_name,
        kind="character",
        type=avatar_type,
        label="avatar",
        traits=["bright", "curious"],
        memes={"bias": 0.0, "worry": 0.0, "love": 0.0, "lesson": 0.0},
    ))
    admirer = world.add(Entity(
        id=admirer_name,
        kind="character",
        type=admirer_type,
        label="friend",
        traits=["kind", "quiet"],
        memes={"love": 1.0, "hope": 1.0},
    ))
    world.facts.update(avatar=avatar, admirer=admirer, interest=interest, bias=bias)

    # Act 1: setup.
    world.say(f"{avatar.id} was a little avatar in {setting.place}, where the air felt {setting.mood}.")
    world.say(f"{avatar.pronoun().capitalize()} loved to {interest.verb}, and {admirer.id} had a {interest.clue} that could sing right.")
    world.say(f"But {avatar.id} saw a small sign of {bias} and forgot to look twice.")
    world.para()

    # Act 2: misunderstanding.
    world.facts["misunderstanding"] = predict_misunderstanding(world, avatar, admirer, interest)
    avatar.memes["bias"] += 1.0
    avatar.memes["worry"] += 1.0
    admirer.memes["hurt"] = admirer.memes.get("hurt", 0.0) + 1.0
    world.say(f"The {bias} thought was quick as a blink, and it made the moment feel thick.")
    world.say(f"{avatar.id} guessed that {admirer.id} meant no sweet word, no spark, no hint.")
    world.say(f"So {avatar.id} turned away in a tiny huff, and the day felt rough.")
    world.para()

    # Act 3: lesson learned.
    avatar.memes["bias"] = 0.0
    avatar.memes["worry"] = 0.0
    avatar.memes["lesson"] += 1.0
    admirer.memes["hurt"] = 0.0
    admirer.memes["love"] += 1.0
    world.facts["lesson_learned"] = True
    world.say(f"Then {avatar.id} paused and read the clue more true.")
    world.say(f"{admirer.id} had meant {interest.romantic_hint}, not the cold guess that grew.")
    world.say(f"{avatar.id} apologized with a grin, and the soft mood came back in.")
    world.say(f"At last they shared {interest.gerund}, and the ending rhymed just right: {rhyming_close(interest.id)} and bright.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    avatar = f["avatar"]
    admirer = f["admirer"]
    interest = f["interest"]
    bias = f["bias"]
    return [
        f"Write a short rhyming story about {avatar.id}, an avatar who makes a {bias} misunderstanding about {admirer.id}.",
        f"Tell a gentle rhyme where {avatar.id} learns a lesson after confusing {admirer.id}'s kind gesture during {interest.verb}.",
        f"Write a child-friendly romantic story in rhyme that ends with an apology and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    avatar = f["avatar"]
    admirer = f["admirer"]
    interest = f["interest"]
    bias = f["bias"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {avatar.id}, a small avatar, and {admirer.id}, who had a kind romantic feeling to share.",
        ),
        QAItem(
            question=f"What did {avatar.id} want to do?",
            answer=f"{avatar.id} wanted to {interest.verb}. That was the sweet plan at {world.setting.place}.",
        ),
        QAItem(
            question=f"What caused the misunderstanding?",
            answer=f"The misunderstanding came from a {bias} bias. {avatar.id} guessed too fast and got the clue wrong.",
        ),
        QAItem(
            question=f"What lesson did {avatar.id} learn?",
            answer=f"{avatar.id} learned to look again before deciding what someone means. The lesson was to be kinder and more careful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avatar?",
            answer="An avatar is a character that can stand in for a person in a story or a game.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the meaning wrong before they check carefully.",
        ),
        QAItem(
            question="What does bias mean?",
            answer="Bias means a quick unfair idea that can make someone judge too soon.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="It means you understand something new and do better next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Story questions =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} {e.type:8} meters={meters} memes={memes}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(A) :- bias(A), avatar(A), not clarified(A).
lesson_learned(A) :- misunderstanding(A), apologized(A), checked_again(A).
happy_end(A) :- lesson_learned(A), romance(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in INTERESTS:
        lines.append(asp.fact("interest", iid))
    for b in BIAS_WORDS:
        lines.append(asp.fact("bias", b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/1. #show lesson_learned/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    if atoms:
        print("OK: ASP program grounded and solved.")
        return 0
    print("MISMATCH: no atoms returned.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about avatar, romantic bias, misunderstanding, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--interest", choices=INTERESTS)
    ap.add_argument("--avatar-name")
    ap.add_argument("--avatar-type", choices=["girl", "boy", "person"], default="person")
    ap.add_argument("--admirer-name")
    ap.add_argument("--admirer-type", choices=["girl", "boy", "person"], default="person")
    ap.add_argument("--bias", choices=BIAS_WORDS)
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
    place = args.place or rng.choice(list(SETTINGS))
    interest = args.interest or rng.choice(list(INTERESTS))
    bias = args.bias or rng.choice(list(BIAS_WORDS))
    avatar_name = args.avatar_name or rng.choice(["Ari", "Mina", "Noa", "Luz", "Kai"])
    admirer_name = args.admirer_name or rng.choice(["Rue", "Jules", "Pip", "Sam", "Nia"])
    avatar_type = args.avatar_type
    admirer_type = args.admirer_type
    if avatar_name == admirer_name:
        raise StoryError("The avatar and admirer must be different characters.")
    return StoryParams(place=place, interest=interest, avatar_name=avatar_name,
                       avatar_type=avatar_type, admirer_name=admirer_name,
                       admirer_type=admirer_type, bias=bias)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], INTERESTS[params.interest],
                 params.avatar_name, params.avatar_type,
                 params.admirer_name, params.admirer_type, params.bias)
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
        print(asp_program("#show misunderstanding/1. #show lesson_learned/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show misunderstanding/1. #show lesson_learned/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("garden", "flower", "Ari", "person", "Rue", "person", "shy"),
            StoryParams("cafe", "letter", "Mina", "girl", "Jules", "boy", "busy"),
            StoryParams("bridge", "song", "Noa", "boy", "Nia", "girl", "quiet"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
