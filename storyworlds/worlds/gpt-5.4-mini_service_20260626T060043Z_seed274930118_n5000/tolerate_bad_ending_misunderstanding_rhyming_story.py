#!/usr/bin/env python3
"""
A standalone Storyweavers world for a rhyming-story domain with a
misunderstanding, a tolerated annoyance, and a bittersweet bad ending.

Premise:
- A child and helper are preparing a tiny rhyming show.
- A note gets misunderstood, causing the wrong prop to be brought.
- The hero chooses to tolerate the confusion and keep going.
- The ending leaves one object ruined, but the friendship stays warm.

The prose aims to feel rhythmic and child-facing without turning into a frozen
template. World state drives the story beats.
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoors: bool = True


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    mess: str
    risk: str
    zone: set[str]
    splashed_by: str


@dataclass
class Helper:
    id: str
    label: str
    fix_label: str
    fix_phrase: str
    helps_with: set[str]


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


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_type: str
    prop: str
    seed: Optional[int] = None


SETTINGS = {
    "studio": Setting(place="the little studio", indoors=True),
    "library_corner": Setting(place="the library corner", indoors=True),
    "bedroom": Setting(place="the bedroom stage", indoors=True),
}

HERO_NAMES = ["Mia", "Leo", "Nina", "Toby", "Zoe", "Finn", "Ruby", "Owen"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "friend"]

PROPS = {
    "bell": Prop(
        id="bell",
        label="bell",
        phrase="a shiny little bell",
        mess="clang",
        risk="loud",
        zone={"sound"},
        splashed_by="ringing",
    ),
    "cake": Prop(
        id="cake",
        label="cake",
        phrase="a crumbly cake prop",
        mess="crumbles",
        risk="crumbly",
        zone={"table"},
        splashed_by="bumping",
    ),
    "painted_hat": Prop(
        id="painted_hat",
        label="hat",
        phrase="a painted paper hat",
        mess="smears",
        risk="smeary",
        zone={"head"},
        splashed_by="rain",
    ),
}

HELPERS = {
    "mother": Helper("mother", "mom", "gentle scarf", "a gentle scarf", {"loud", "crumbly", "smeary"}),
    "father": Helper("father", "dad", "steady vest", "a steady vest", {"loud", "crumbly", "smeary"}),
    "friend": Helper("friend", "friend", "bright ribbon", "a bright ribbon", {"loud", "crumbly", "smeary"}),
}


ASP_RULES = r"""
good_story(P, H, T) :- place(P), hero_type(H), helper_type(T).
misunderstanding(P) :- prop(P).
tolerable(P) :- prop(P), fix_available(P).
bad_ending(P) :- misunderstanding(P), not fixed(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for ht in HERO_TYPES:
        lines.append(asp.fact("hero_type", ht))
    for ht in HELPER_TYPES:
        lines.append(asp.fact("helper_type", ht))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("risk", pid, prop.risk))
        for z in sorted(prop.zone):
            lines.append(asp.fact("zone", pid, z))
        lines.append(asp.fact("fix_available", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def rhyme_line(hero: Entity, prop: Prop, helper: Helper, beat: str) -> str:
    if beat == "start":
        return (
            f"{hero.id} came to the stage with a sing-song grin, "
            f"to make a small rhyme and begin, begin, begin."
        )
    if beat == "misunderstanding":
        return (
            f"But the note got mixed, like a flip-flop rhyme, "
            f"and {helper.label} brought {helper.fix_phrase} at the wrong time."
        )
    if beat == "tolerate":
        return (
            f"{hero.id} wanted to fuss and to pout and to cry, "
            f"but {hero.pronoun()} chose to tolerate and try."
        )
    if beat == "ending":
        return (
            f"So the rhyme went on, though the prop went wrong, "
            f"and the little stage ended with one sad song."
        )
    return ""


def setup_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.prop not in PROPS:
        raise StoryError("Unknown prop.")
    if params.hero_type not in HERO_TYPES:
        raise StoryError("Unknown hero type.")
    if params.helper_type not in HELPERS:
        raise StoryError("Unknown helper type.")

    world = World(SETTINGS[params.place])
    hero = world.add(
        Entity(
            id=params.hero_name,
            kind="character",
            type=params.hero_type,
            meters={"patience": 0.0, "mess": 0.0},
            memes={"joy": 1.0, "confusion": 0.0, "tolerance": 0.0, "disappointment": 0.0, "love": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=params.helper_type,
            label=HELPERS[params.helper_type].label,
            meters={"work": 0.0},
            memes={"care": 1.0, "confusion": 0.0},
        )
    )
    prop = world.add(
        Entity(
            id="prop",
            type="thing",
            label=PROPS[params.prop].label,
            phrase=PROPS[params.prop].phrase,
            caretaker=helper.id,
            meters={"clean": 1.0, "ruined": 0.0},
        )
    )
    world.facts.update(hero=hero, helper=helper, prop=prop, prop_cfg=PROPS[params.prop])
    return world


def propagate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    prop: Entity = world.facts["prop"]
    helper: Entity = world.facts["helper"]

    if hero.memes["confusion"] >= THRESHOLD and ("confused", hero.id) not in world.fired:
        world.fired.add(("confused", hero.id))
        hero.memes["tolerance"] += 1.0

    if hero.meters["mess"] >= THRESHOLD and prop.meters["clean"] >= THRESHOLD and ("ruin", prop.id) not in world.fired:
        world.fired.add(("ruin", prop.id))
        prop.meters["clean"] = 0.0
        prop.meters["ruined"] = 1.0
        helper.meters["work"] += 1.0


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    prop: Entity = world.facts["prop"]
    prop_cfg: Prop = world.facts["prop_cfg"]

    world.say(rhyme_line(hero, prop_cfg, world.get(helper.id), "start"))
    world.say(
        f"In {world.setting.place}, {hero.id} wanted to make a rhyme so bright, "
        f"with a tap-tap beat and a twinkle of light."
    )
    world.para()
    world.say(
        f"{helper.label.capitalize()} read a note in a hurry and guessed it wrong, "
        f"so {helper.label} brought {prop.phrase} instead of the right song."
    )
    hero.memes["confusion"] += 1.0
    world.say(
        f"{hero.id} blinked at the mix-up, because the note had been small, "
        f"and the wrong prop sat there like a wobble on a wall."
    )
    world.para()
    world.say(rhyme_line(hero, prop_cfg, helper, "tolerate"))
    hero.memes["tolerance"] += 1.0
    hero.meters["mess"] += 1.0
    world.say(
        f"{hero.id} kept the show going with a nod and a grin, "
        f"so the rhyme could still ring out and spin, spin, spin."
    )
    propagate(world)
    world.para()
    if prop.meters["ruined"] >= THRESHOLD:
        world.say(
            f"The prop did not survive; it ended all bent and torn, "
            f"and the stage looked a little bit worn."
        )
        hero.memes["disappointment"] += 1.0
        helper.memes["care"] += 1.0
        world.say(
            f"But {helper.label} sat beside {hero.id} and said, 'We can be sad, "
            f"and still be kind,' so the pair held on with a gentle mind."
        )
    world.say(rhyme_line(hero, prop_cfg, helper, "ending"))

    world.facts["ending_bad"] = prop.meters["ruined"] >= THRESHOLD
    world.facts["misunderstanding"] = hero.memes["confusion"] >= THRESHOLD
    world.facts["tolerated"] = hero.memes["tolerance"] >= THRESHOLD


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    prop: Entity = world.facts["prop"]
    return [
        f"Write a short rhyming story about {hero.id}, {helper.label}, and {prop.label}.",
        f"Tell a gentle rhyme story where {hero.id} tolerates a misunderstanding during a small show.",
        f"Make a child-friendly rhyming tale with a bad ending for the prop but a kind ending for the people.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    prop: Entity = world.facts["prop"]
    prop_cfg: Prop = world.facts["prop_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} want to make at the start of the story?",
            answer=f"{hero.id} wanted to make a small rhyme and put on a tiny show in {world.setting.place}.",
        ),
        QAItem(
            question=f"What misunderstanding happened with {helper.label}?",
            answer=f"{helper.label} misunderstood the note and brought {prop.phrase} at the wrong time.",
        ),
        QAItem(
            question=f"How did {hero.id} respond to the misunderstanding?",
            answer=f"{hero.id} chose to tolerate the mix-up and kept the rhyme going instead of stopping the show.",
        ),
        QAItem(
            question=f"What was the bad ending for the prop?",
            answer=f"The {prop_cfg.label} ended bent and torn, so the prop did not survive the show.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {helper.label}?",
            answer=f"They stayed kind to each other, even though the prop was ruined, and the ending felt sad but gentle.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tolerate mean?",
            answer="To tolerate something means to put up with it calmly, even if it is annoying or not what you wanted.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what was said or meant.",
        ),
        QAItem(
            question="What is a rhyming story?",
            answer="A rhyming story is a story that uses words with matching sounds to make the lines feel musical and playful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({a for a, *_ in world.fired})}")
    return "\n".join(lines)


def ASP_verify() -> int:
    import asp

    clingo = asp.one_model(asp_program("#show bad_ending/1. #show misunderstanding/1. #show tolerable/1."))
    atoms = set((sym.name, tuple(str(a) for a in sym.arguments)) for sym in clingo)
    if atoms:
        print("OK: ASP program produced a model.")
        return 0
    print("MISMATCH: ASP program produced no model.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world with misunderstanding and a bad ending.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--prop", choices=sorted(PROPS))
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
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    prop = args.prop or rng.choice(list(PROPS))
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, helper_type=helper_type, prop=prop)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
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
    StoryParams(place="studio", hero_name="Mia", hero_type="girl", helper_type="mother", prop="bell"),
    StoryParams(place="library_corner", hero_name="Leo", hero_type="boy", helper_type="friend", prop="cake"),
    StoryParams(place="bedroom", hero_name="Nina", hero_type="girl", helper_type="father", prop="painted_hat"),
]


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show bad_ending/1. #show misunderstanding/1. #show tolerable/1."))
    return sorted(set((sym.name, tuple(a.name if a.type != a.type.String else a.string for a in sym.arguments)) for sym in model))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/1. #show misunderstanding/1. #show tolerable/1."))
        return
    if args.verify:
        sys.exit(ASP_verify())
    if args.asp:
        print(asp_program("#show bad_ending/1. #show misunderstanding/1. #show tolerable/1."))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.prop} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
