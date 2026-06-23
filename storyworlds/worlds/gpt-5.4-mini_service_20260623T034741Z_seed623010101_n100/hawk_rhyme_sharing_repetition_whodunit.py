#!/usr/bin/env python3
"""
storyworlds/worlds/hawk_rhyme_sharing_repetition_whodunit.py
=============================================================

A small standalone storyworld for a kid-friendly whodunit about a hawk,
sharing, repetition, and rhyme.

Premise:
- Two children share a snack or shiny treasure in a simple outdoor setting.
- A hawk is the only plausible culprit when something goes missing.
- The children repeat clues, share observations, and solve the mystery together.
- The ending proves what changed: the missing item is found, the hawk is seen,
  and the children choose a safer, shared way to keep their things.

This script follows the Storyweavers storyworld contract:
- stdlib only
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily in ASP helpers
- provides StoryParams, build_parser, resolve_params, generate, emit, main
- supports -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and an inline ASP twin
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

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
class Setting:
    place: str
    indoors: bool = False
    sound: str = ""
    afford: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    owner: str = ""
    plural: bool = False
    shimmer: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Bird:
    id: str
    label: str
    phrase: str
    call: str
    steals: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    treasure: str
    bird: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "orchard": Setting("the orchard", indoors=False, sound="rustle", afford={"share", "spot"}),
    "pond": Setting("the pond", indoors=False, sound="splash", afford={"share", "spot"}),
    "hill": Setting("the hill", indoors=False, sound="wind", afford={"share", "spot"}),
}

TREASURES = {
    "berries": Treasure("berries", "berries", "a little bowl of berries", "snack", shimmer="red and sweet", tags={"share", "snack"}),
    "shells": Treasure("shells", "shells", "a small pile of shiny shells", "shiny", plural=True, shimmer="bright and pale", tags={"share", "shiny"}),
    "buttons": Treasure("buttons", "buttons", "a tin of bright buttons", "shiny", plural=True, shimmer="round and colorful", tags={"share", "shiny"}),
}

BIRDS = {
    "hawk": Bird("hawk", "hawk", "a hawk", "keek", steals={"shiny", "snack"}, tags={"hawk", "bird"}),
}

NAMES = ["Mia", "Noah", "Lily", "Ben", "Ava", "Leo", "Zoe", "Sam"]
GENDERS = ["girl", "boy"]
HELPERS = ["grandma", "grandpa", "mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id, setting in SETTINGS.items():
        for treasure_id, treasure in TREASURES.items():
            for bird_id, bird in BIRDS.items():
                if bird_id == "hawk" and setting.afford and treasure.type in bird.steals:
                    out.append((setting_id, treasure_id, bird_id))
    return out


def explain_rejection(setting: Setting, treasure: Treasure, bird: Bird) -> str:
    return (
        f"(No story: this setup does not feel like a real mystery. "
        f"The {bird.label} only makes sense when something {treasure.shimmer or 'interesting'} "
        f"goes missing in an outdoor place like {setting.place}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a hawk mystery with sharing, rhyme, and repetition."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=GENDERS)
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=GENDERS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.bird is None or c[2] == args.bird)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treasure, bird = rng.choice(sorted(combos))
    c1 = args.child1 or rng.choice(NAMES)
    c1g = args.child1_gender or rng.choice(GENDERS)
    c2 = args.child2 or rng.choice([n for n in NAMES if n != c1])
    c2g = args.child2_gender or ("boy" if c1g == "girl" else "girl")
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        setting=setting, treasure=treasure, bird=bird,
        child1=c1, child1_gender=c1g, child2=c2, child2_gender=c2g,
        helper=helper,
    )


def _pair_noun(a: Entity, b: Entity) -> str:
    if a.type == b.type == "girl":
        return "two girls"
    if a.type == b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def tell(setting: Setting, treasure: Treasure, bird: Bird,
         child1: str, child1_gender: str, child2: str, child2_gender: str,
         helper: str) -> World:
    w = World(setting)
    a = w.add(Entity(id=child1, kind="character", type=child1_gender, meters={"distance": 0.0}, memes={"curious": 0.0, "sharing": 0.0}))
    b = w.add(Entity(id=child2, kind="character", type=child2_gender, meters={"distance": 0.0}, memes={"curious": 0.0, "sharing": 0.0}))
    h = w.add(Entity(id=helper, kind="character", type=helper if helper in {"mother", "father"} else "mother", label=f"the {helper}", meters={"distance": 0.0}, memes={"caution": 0.0}))
    t = w.add(Entity(id="treasure", type=treasure.type, label=treasure.label, phrase=treasure.phrase, plural=treasure.plural, meters={"missing": 0.0, "seen": 0.0}, memes={"value": 1.0}, attrs={"shimmer": treasure.shimmer}))
    bird_ent = w.add(Entity(id="hawk", type="bird", label=bird.label, phrase=bird.phrase, meters={"near": 0.0, "gone": 0.0}, memes={"mystery": 0.0}))
    w.facts.update(children=(a, b), helper=h, treasure=t, bird=bird_ent, setting=setting, treasure_cfg=treasure)

    w.say(f"{a.id} and {b.id} came to {setting.place} with {treasure.phrase}.")
    w.say(f"They shared the treat, piece by piece, and said, 'One for you, one for me.'")
    w.say(f"The day sounded like {setting.sound}, and the little bowl gleamed {treasure.shimmer}.")
    w.para()
    w.say(f"Then the mystery began. One bite was there, and then one bite was not there.")
    w.say(f"Again they looked. Again it was gone. 'Who took it? Who took it?' they asked.")
    w.say(f"They searched the grass, the path, and the low branches, but there was no clue yet.")
    w.say(f"A shadow slid over the leaves. Up above, a hawk called, '{bird.call}, {bird.call}.'")
    t.meters["missing"] += 1
    bird_ent.meters["near"] += 1
    bird_ent.memes["mystery"] += 1
    a.memes["curious"] += 1
    b.memes["curious"] += 1
    w.para()
    w.say(f"{helper.capitalize()} came near and pointed at the crumbs.")
    w.say(f"'Look for the beak,' {helper} said. 'Look for the sky. Look, look, look.'")
    a.memes["sharing"] += 1
    b.memes["sharing"] += 1
    w.say(f"So {a.id} and {b.id} shared the last piece, shared the clues, and shared the search.")
    w.say(f"They said, 'Little thief in the blue, little thief in the view, who could it be?'")
    w.say(f"The answer came in a flap and a flash: the hawk had swooped down and snatched the shining treat.")
    bird_ent.meters["gone"] += 1
    t.meters["seen"] += 1
    w.para()
    w.say(f"{a.id} and {b.id} nodded at once. 'Hawk,' they said. 'Hawk took the prize.'")
    w.say(f"They laughed, because the clue was plain now, and the rhyme had led them true.")
    w.say(f"{helper.capitalize()} gave them a new plan: share the snack in a covered basket, and keep the shiny things tucked away.")
    w.say(f"So the children ate together, the hawk flew on, and the mystery ended with a safe little picnic.")
    w.facts["solved"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    a, b = world.facts["children"]
    t = world.facts["treasure_cfg"]
    return [
        f"Write a short whodunit for children where {a.id} and {b.id} share {t.phrase}, and a hawk turns up as the culprit.",
        f"Tell a rhyming mystery with repetition: who took {t.label}, and how do the children solve it together?",
        f"Write a gentle story about sharing, clues, and a hawk, ending with a safer way to keep the treasure."
    ]


def story_qa(world: World) -> list[QAItem]:
    a, b = world.facts["children"]
    helper = world.facts["helper"]
    t = world.facts["treasure"]
    return [
        QAItem(
            question=f"Who were the story's children at {world.facts['setting'].place}?",
            answer=f"The story was about {a.id} and {b.id}. They were the children who shared {t.phrase} and tried to solve the mystery together.",
        ),
        QAItem(
            question="What mystery did they keep asking about?",
            answer=f"They kept asking who took {t.label}. They repeated the question again and again until the clue pointed to the hawk.",
        ),
        QAItem(
            question="How did sharing help them solve the whodunit?",
            answer=f"Sharing helped because {a.id} and {b.id} looked together, thought together, and shared the last clue. That made it easier to notice the hawk and understand what had happened.",
        ),
        QAItem(
            question=f"What did {helper.id} tell them to look for?",
            answer=f"{helper.id.capitalize()} told them to look for the beak and look at the sky. That advice helped them notice the hawk as the answer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hawk?",
            answer="A hawk is a bird that can fly high and swoop down quickly. Hawks have sharp eyes and strong beaks.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use or enjoy part of something too. It is a kind way to play and eat together.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a little piece of information that helps solve a mystery. Clues can be things you see, hear, or notice.",
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery(S,T,B) :- setting(S), treasure(T), bird(B), hawk(B).
solved(B) :- bird(B), hawk(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    for bid in BIRDS:
        lines.append(asp.fact("bird", bid))
        if bid == "hawk":
            lines.append(asp.fact("hawk", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/3."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    rc = 0
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate:")
        print("  only in asp:", sorted(clingo_set - python_set))
        print("  only in python:", sorted(python_set - clingo_set))

    params = resolve_params(argparse.Namespace(
        setting=None, treasure=None, bird=None, child1=None, child1_gender=None,
        child2=None, child2_gender=None, helper=None
    ), random.Random(777))
    try:
        sample = generate(params)
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1 if rc == 0 else rc
    print("OK: generation smoke test succeeded.")
    return rc


def explain_rejection(treasure: Treasure) -> str:
    return (
        f"(No story: the hawk mystery needs something the children can share and "
        f"then notice is missing, like {treasure.phrase}.)"
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.treasure not in TREASURES:
        raise StoryError(f"Unknown treasure: {params.treasure}")
    if params.bird not in BIRDS:
        raise StoryError(f"Unknown bird: {params.bird}")
    world = tell(
        SETTINGS[params.setting], TREASURES[params.treasure], BIRDS[params.bird],
        params.child1, params.child1_gender, params.child2, params.child2_gender,
        params.helper,
    )
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.bird is None or c[2] == args.bird)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treasure, bird = rng.choice(sorted(combos))
    c1 = args.child1 or rng.choice(NAMES)
    c1g = args.child1_gender or rng.choice(GENDERS)
    c2 = args.child2 or rng.choice([n for n in NAMES if n != c1])
    c2g = args.child2_gender or rng.choice([g for g in GENDERS if g != c1g] or GENDERS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        setting=setting, treasure=treasure, bird=bird,
        child1=c1, child1_gender=c1g, child2=c2, child2_gender=c2g,
        helper=helper,
    )


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(setting=s, treasure=t, bird=b, child1="Mia", child1_gender="girl",
                    child2="Noah", child2_gender="boy", helper="mother")
        for s, t, b in valid_combos()
    ]


def build_story_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery/3.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} mystery combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [build_story_from_params(p) for p in valid_story_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.child1} & {p.child2} at {p.setting} (hawk whodunit)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
