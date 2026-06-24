#!/usr/bin/env python3
"""
Story world: a slow fable with a flashback, a mystery to solve, and a gentle transformation.

A small animal hero notices that something important has gone missing.
A memory from earlier in the day reveals the answer, and the hero changes
from hesitant to wise by the end.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    place: Optional[str] = None
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"tortoise", "hedgehog", "mouse", "rabbit", "fox", "owl"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    sound: str


@dataclass
class Mystery:
    id: str
    missing: str
    stolen_from: str
    place: str
    clue_kind: str
    flashback_place: str
    flashback_detail: str
    reveal: str
    transformation: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.story_bits: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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
        w = World(self.setting, self.mystery)
        w.entities = {k: Entity(**{**vars(v), "meters": dict(v.meters), "memes": dict(v.memes), "traits": list(v.traits)}) for k, v in self.entities.items()}
        w.facts = dict(self.facts)
        w.story_bits = list(self.story_bits)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(
        place="the meadow",
        detail="The grass was soft, and a narrow path curled past the reed pond.",
        sound="the wind whispered through the grass",
    ),
    "orchard": Setting(
        place="the orchard",
        detail="The apple trees stood in rows, and a wooden gate watched the lane.",
        sound="the leaves tapped like small hands",
    ),
    "riverbank": Setting(
        place="the riverbank",
        detail="The water moved slowly, and stones glinted beside the reeds.",
        sound="the river hummed against the bank",
    ),
}

MYSTERIES = {
    "honey": Mystery(
        id="honey",
        missing="honey cake",
        stolen_from="Grandmother Mole",
        place="the blue stone",
        clue_kind="sticky pawprints",
        flashback_place="the plum tree",
        flashback_detail="a little slice of honey cake beside a fallen leaf",
        reveal="The honey on the leaf had smudged onto the thief's paw.",
        transformation="the shy hero learned to speak up gently and ask questions.",
    ),
    "bell": Mystery(
        id="bell",
        missing="silver bell",
        stolen_from="Old Oak",
        place="the bridge",
        clue_kind="a bright ringing mark",
        flashback_place="the river reeds",
        flashback_detail="a shining bell ribbon caught on a reed",
        reveal="The ribbon had snagged, so the bell had not been stolen at all.",
        transformation="the careful hero learned that a mystery can have a simple answer.",
    ),
    "seed": Mystery(
        id="seed",
        missing="gold seed",
        stolen_from="the garden keeper",
        place="the stone path",
        clue_kind="small scratch marks",
        flashback_place="the warm compost heap",
        flashback_detail="a sparrow pecking near the seed basket",
        reveal="The sparrow had carried the seed to its nest by mistake.",
        transformation="the slow hero learned that patience can uncover the truth.",
    ),
}

HEROES = {
    "tortoise": Entity(id="Timo", kind="character", type="tortoise", label="Timo", traits=["slow", "careful"]),
    "mouse": Entity(id="Mina", kind="character", type="mouse", label="Mina", traits=["small", "eager"]),
    "hedgehog": Entity(id="Hugo", kind="character", type="hedgehog", label="Hugo", traits=["quiet", "steady"]),
}

HELPERS = {
    "owl": Entity(id="Orin", kind="character", type="owl", label="Orin", traits=["wise"]),
    "rabbit": Entity(id="Pippa", kind="character", type="rabbit", label="Pippa", traits=["quick"]),
    "fox": Entity(id="Fern", kind="character", type="fox", label="Fern", traits=["watchful"]),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story needs one setting, one mystery, and a helper.
valid_story(S, M, H) :- setting(S), mystery(M), hero(H), allowed(H, M, S).

% The mystery is solvable when the clue can appear in the setting and the
% flashback place is also part of the same world.
solvable(M, S) :- mystery(M), setting(S), clue_in(S, M), flashback_in(S, M).

% The story is reasonable when the hero is slow or careful, because this world
% tells a fable about patience and attention.
reasonable(H) :- hero(H), slow(H).
reasonable(H) :- hero(H), careful(H).

allowed(H, M, S) :- reasonable(H), solvable(M, S).
#show valid_story/3.
#show solvable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_in", m.place, mid))
        lines.append(asp.fact("flashback_in", m.flashback_place, mid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero", hid))
        for t in h.traits:
            if t in {"slow", "careful"}:
                lines.append(asp.fact(t, hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for h in HEROES:
                if h == "tortoise":
                    out.append((s, m, h))
    return out


def explain_rejection() -> str:
    return "(No story: this world is built for a slow, patient hero. Try the tortoise.)"


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(setting: Setting, mystery: Mystery, hero: Entity, helper: Entity) -> World:
    world = World(setting, mystery)
    hero = world.add(Entity(**{**vars(hero), "meters": {}, "memes": {"curiosity": 1.0, "worry": 1.0}}))
    helper = world.add(Entity(**{**vars(helper), "meters": {}, "memes": {}}))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=mystery.clue_kind,
        phrase=mystery.clue_kind,
        place=mystery.place,
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type="treasure",
        label=mystery.missing,
        phrase=mystery.missing,
        owner=mystery.stolen_from,
    ))

    # Beginning
    world.say(f"Once, in {setting.place}, there lived a slow little {hero.type} named {hero.label}.")
    world.say(f"{hero.label} liked quiet paths and careful steps, and {setting.sound} always helped {hero.pronoun('object')} think.")
    world.say(f"One morning, {mystery.stolen_from} noticed that the {mystery.missing} was gone.")
    world.say(f"{hero.label} wanted to help, because {hero.pronoun('subject')} believed even slow feet could find a missing thing.")

    world.para()

    # Middle with mystery and flashback
    hero.memes["search"] = 1.0
    world.say(f"{hero.label} searched {setting.place} very slowly, looking at every stone and reed.")
    world.say(f"At {mystery.place}, {hero.label} found {mystery.clue_kind}.")
    world.say(f"That clue made {hero.label} pause and remember an earlier moment in a flashback.")
    world.say(f"In the flashback, {hero.label} had passed {mystery.flashback_place} and seen {mystery.flashback_detail}.")
    world.say(f"{mystery.reveal}")

    world.para()

    # Resolution / transformation
    hero.memes["certainty"] = 1.0
    hero.memes["confidence"] = 1.0
    world.say(f"{helper.label} listened carefully and helped {hero.label} follow the clue back to the real answer.")
    world.say(f"They found that the {mystery.missing} had not vanished in a bad way at all; it had only gone where it did not belong.")
    world.say(f"{hero.label} returned the {mystery.missing} and spoke kindly to the bird who had carried it off by mistake.")
    world.say(f"By the end, {mystery.transformation}")
    world.say(f"The little {hero.type} was still slow, but now {hero.pronoun('subject')} knew slow thinking could be brave thinking.")

    world.facts.update(
        setting=setting,
        mystery=mystery,
        hero=hero,
        helper=helper,
        clue=clue,
        missing=missing,
        flashback_place=mystery.flashback_place,
        reveal=mystery.reveal,
        transformed=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child about a slow animal who solves a mystery with a flashback.',
        f"Tell a gentle story in {f['setting'].place} where {f['hero'].label} finds a clue, remembers something from earlier, and learns a lesson.",
        f'Write a simple fable about "{f["mystery"].missing}" that ends with a quiet transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a slow little {hero.type} who tries to solve a mystery in {f['setting'].place}.",
        ),
        QAItem(
            question=f"What was missing?",
            answer=f"The missing thing was the {mystery.missing}. It belonged to {mystery.stolen_from}.",
        ),
        QAItem(
            question=f"What clue did {hero.label} find?",
            answer=f"{hero.label} found {mystery.clue_kind} near {mystery.place}, and that clue helped point the way.",
        ),
        QAItem(
            question=f"What did the flashback show?",
            answer=f"The flashback showed {mystery.flashback_detail} at {mystery.flashback_place}, which helped explain the mystery.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"{hero.label} and {helper.label} solved it together, and the missing {mystery.missing} was returned safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    return [
        QAItem(
            question="Why can being slow be helpful?",
            answer="Being slow can be helpful because it gives you time to look carefully, notice clues, and make wise choices.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened earlier, so the reader can understand the present better.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling or unknown that characters try to figure out.",
        ),
        QAItem(
            question="What can change in a transformation tale?",
            answer="In a transformation tale, a character can change in the way they think, feel, or act after learning an important lesson.",
        ),
        QAItem(
            question=f"What kind of animal is {hero.label}?",
            answer=f"{hero.label} is a tortoise, and tortoises are known for moving slowly and steadily.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slow fable with a flashback and a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.hero and args.hero != "tortoise":
        raise StoryError(explain_rejection())
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.hero:
        combos = [c for c in combos if c[2] == args.hero]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, hero = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting=setting, mystery=mystery, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], HEROES[params.hero], HELPERS[params.helper])
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} compatible (setting, mystery, hero) combos:\n")
        for s, m, h in triples:
            print(f"  {s:10} {m:10} {h:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for s in SETTINGS:
            for m in MYSTERIES:
                params = StoryParams(setting=s, mystery=m, hero="tortoise", helper="owl", seed=base_seed)
                samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
