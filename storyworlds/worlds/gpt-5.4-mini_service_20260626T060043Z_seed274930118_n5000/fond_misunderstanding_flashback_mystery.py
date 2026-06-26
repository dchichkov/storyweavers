#!/usr/bin/env python3
"""
storyworlds/worlds/fond_misunderstanding_flashback_mystery.py
==============================================================

A small mystery storyworld about a fond misunderstanding that gets cleared up by
a flashback clue.

Premise:
- A child finds something odd and worries about it.
- A kind helper seems mysterious because of a misunderstanding.
- A flashback reveals an earlier fond promise or memory.
- The mystery resolves when the child notices the real meaning of the clue.

The world model tracks:
- physical meters: clue state, visibility, distance, hiddenness
- emotional memes: curiosity, worry, fondness, surprise, relief, trust

The prose is generated from simulated state so the story feels like a little
mystery rather than a fixed paragraph with swapped names.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    weather: str
    clue_place: str
    hidden_spot: str
    would_misunderstand: bool = True


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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

    def copy(self) -> "World":
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    helper_name: str
    helper_gender: str
    clue: str
    seed: Optional[int] = None


PLACES = {
    "library": Scene(place="the library", weather="quiet", clue_place="a back shelf", hidden_spot="a reading nook"),
    "garden": Scene(place="the garden", weather="soft", clue_place="a stone bench", hidden_spot="a flower arch"),
    "hall": Scene(place="the old hall", weather="dim", clue_place="a coat hook", hidden_spot="a curtain"),
}

CLUES = {
    "note": ("a folded note", "note"),
    "ribbon": ("a blue ribbon", "ribbon"),
    "key": ("a small brass key", "key"),
    "button": ("a shiny button", "button"),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Zoe", "Maya", "Lia"]
BOY_NAMES = ["Toby", "Finn", "Noah", "Eli", "Milo", "Ben", "Jude"]
TRAITS = ["curious", "careful", "bright-eyed", "quiet", "thoughtful", "brave"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fond misunderstanding mystery with a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hero_name=name, hero_gender=gender, hero_trait=trait,
                       helper_name=helper_name, helper_gender=helper_gender, clue=clue)


def reasonableness_gate(params: StoryParams) -> None:
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper should be different people so the misunderstanding can land.")
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")


def tell(scene: Scene, params: StoryParams) -> World:
    world = World(scene)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name))
    clue_label, clue_word = CLUES[params.clue]
    clue = world.add(Entity(
        id="clue", type=clue_word, label=clue_word, phrase=clue_label,
        owner=helper.id, meters={"hidden": 1.0}, memes={"mystery": 1.0}
    ))

    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 1.0
    helper.memes["fondness"] = 1.0
    helper.memes["trust"] = 1.0

    world.say(f"{params.hero_name} was a {params.hero_trait} child who liked quiet places with corners to explore.")
    world.say(f"On that day, {params.hero_name} went to {scene.place} and noticed something strange at {scene.clue_place}.")
    world.say(f"There was {clue.phrase}, tucked away as if it wanted to keep a secret.")

    world.para()
    hero.memes["curiosity"] += 1.0
    world.say(f"{params.hero_name} picked it up and frowned.")
    world.say(f"It looked like a clue, but it also looked a little bit like trouble.")

    world.para()
    if clue_word == "note":
        world.say(f"{params.helper_name} came in from the {scene.hidden_spot} and gasped.")
        world.say(f"{params.hero_name} thought that gasp meant {params.helper_name} was upset about the note.")
    else:
        world.say(f"{params.helper_name} came in from the {scene.hidden_spot} and stopped short.")
        world.say(f"{params.hero_name} thought that meant {params.helper_name} was hiding something bad.")

    hero.memes["worry"] += 1.0
    hero.memes["misunderstanding"] = 1.0
    helper.memes["concern"] = 1.0
    world.say(f"But {params.helper_name}'s face was not angry. It was surprised, and a little fond, too.")

    world.para()
    world.say("Then a flashback slipped into {0}'s mind.".format(params.hero_name))
    world.say(f"Earlier that week, {params.helper_name} had smiled and said, \"If you find my {clue_word}, bring it to me.\"")
    world.say(f"{params.helper_name} had been making a tiny surprise for someone they cared about.")

    world.para()
    hero.memes["surprise"] = 1.0
    hero.memes["fondness"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    clue.meters["hidden"] = 0.0
    clue.owner = params.hero_name
    world.say(f"{params.hero_name} blinked and smiled. The mystery was not mean at all.")
    world.say(f"It was a fond little secret, and the clue had only looked suspicious because nobody had told the whole story yet.")
    world.say(f"{params.hero_name} handed {clue.phrase} back, and {params.helper_name} laughed in relief.")

    world.para()
    world.say(f"By the end, the room felt warmer.")
    world.say(f"{params.hero_name} remembered that a mystery can be confusing first and kind later.")
    world.say(f"And this one ended with a smile, a found clue, and a very happy flashback.")

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        clue_word=clue_word,
        clue_label=clue_label,
        scene=scene,
        params=params,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the word "{f["clue_word"]}".',
        f"Tell a gentle story where {f['params'].hero_name} makes a misunderstanding about {f['clue_label']} and then remembers a flashback.",
        f"Write a child-friendly mystery with a fond secret, a clue, and a happy ending in {f['scene'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What did {p.hero_name} find in {f['scene'].place}?",
            answer=f"{p.hero_name} found {f['clue_label']} tucked away near {f['scene'].clue_place}."
        ),
        QAItem(
            question=f"Why did {p.hero_name} first think the clue might be trouble?",
            answer=f"{p.hero_name} saw the clue without the full story, so it looked mysterious and a little worrying at first."
        ),
        QAItem(
            question=f"What did the flashback show about {p.helper_name}?",
            answer=f"The flashback showed that {p.helper_name} had asked someone to bring back the clue because it was part of a fond surprise."
        ),
        QAItem(
            question=f"How did the story end for {p.hero_name} and {p.helper_name}?",
            answer=f"They cleared up the misunderstanding, and the story ended with both of them smiling."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly shows something that happened earlier."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone gets the wrong idea because they do not know the full story yet."
        ),
        QAItem(
            question="Why can a clue be helpful in a mystery?",
            answer="A clue can help solve the mystery because it gives a hint about what really happened."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} label={e.label} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hidden_mystery(C) :- clue(C), hidden(C).
misunderstanding(H) :- worries(H), clue(C), hidden(C).
flashback_needed(H) :- misunderstanding(H), fond_secret(S).
resolved(H) :- flashback_shown(H), fond_secret(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, scene in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("scene_place", pid, scene.place))
    for cid, (label, word) in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_word", cid, word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show clue/1."))
    if not model:
        print("OK: ASP program parsed.")
        return 0
    print("OK: ASP program parsed and produced a model.")
    return 0


def asp_valid_story_kinds() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show clue_word/2."))
    return sorted(set(asp.atoms(model, "clue_word")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    scene = PLACES[params.place]
    world = tell(scene, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="library", hero_name="Mina", hero_gender="girl", hero_trait="curious",
                helper_name="Jude", helper_gender="boy", clue="note"),
    StoryParams(place="garden", hero_name="Toby", hero_gender="boy", hero_trait="thoughtful",
                helper_name="Lia", helper_gender="girl", clue="ribbon"),
    StoryParams(place="hall", hero_name="Nora", hero_gender="girl", hero_trait="bright-eyed",
                helper_name="Finn", helper_gender="boy", clue="key"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show clue_word/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show clue_word/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.hero_name} at {p.place} with {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
