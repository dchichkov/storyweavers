#!/usr/bin/env python3
"""
storyworlds/worlds/hiney_foreshadowing_misunderstanding_twist_detective_story.py
================================================================================

A tiny detective-story world built from the seed word "hiney" with a gentle
foreshadowing / misunderstanding / twist structure.

Core premise:
- A child detective notices a strange clue.
- Early details foreshadow the real answer.
- The detective makes a reasonable but wrong guess.
- A twist reveals the truth, and the mystery is solved kindly.

The world is classical and state-driven: characters, clues, and places all have
physical meters and emotional memes, and the prose is narrated from the live
simulation rather than from a fixed template.
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
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
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


@dataclass
class Setting:
    place: str = "the little neighborhood"
    indoors: bool = False
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    sign: str
    at: str
    weight: str
    foreshadow: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    likely_trace: str
    true_trace: str
    twist_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def meter_get(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme_get(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def bump_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter_get(e, key) + amt


def bump_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme_get(e, key) + amt


def tell(setting: Setting, clue: Clue, suspect: Suspect, hero_name: str, helper_name: str) -> World:
    world = World(setting)

    detective = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl",
        label=hero_name,
        meters={"curiosity": 0.0, "confidence": 0.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="boy",
        label=helper_name,
        meters={"care": 0.0},
        memes={"worry": 0.0},
    ))
    suspect_ent = world.add(Entity(
        id=suspect.id,
        kind="character",
        type=suspect.type,
        label=suspect.label,
        phrase=suspect.label,
        meters={"stain": 0.0, "nervous": 0.0},
        memes={"worry": 0.0},
    ))
    clue_ent = world.add(Entity(
        id=clue.id,
        type="thing",
        label=clue.label,
        phrase=clue.label,
        meters={"notice": 0.0},
        hidden=True,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=suspect_ent,
        clue=clue_ent,
        setting=setting,
        clue_cfg=clue,
        suspect_cfg=suspect,
    )

    world.say(f"{detective.id} was a small detective who loved solving mysteries in {setting.place}.")
    world.say(f"One morning, {detective.id} and {helper.id} were walking past the fence when they spotted {clue.sign}.")
    bump_meter(detective, "curiosity", 1)
    bump_meme(detective, "curiosity", 1)
    world.say(clue.foreshadow)

    world.para()
    world.say(f"{detective.id} bent down and studied the clue. It looked strange, almost like a {clue.label}.")
    world.say(f"{helper.id} whispered, 'Maybe someone sneaky did it.'")
    bump_meter(helper, "care", 1)
    bump_meme(helper, "worry", 1)

    if clue.id == "muddy_bench":
        suspect_ent.meters["stain"] += 1
        suspect_ent.memes["worry"] += 1
        world.say(f"A muddy trail led toward {suspect.label}, and that made the guess feel almost certain.")
        world.say(f"{detective.id} thought the culprit was {suspect.label} at first.")
        bump_meter(detective, "confidence", 1)
    else:
        world.say(f"The clue made {detective.id} sure the answer was close, but not quite clear yet.")

    world.para()
    world.say(f"{detective.id} followed the trail and found {suspect.alibi}.")
    world.say(f"That was the misunderstanding: {suspect.label} looked suspicious, but the clue was pointing somewhere else.")

    world.para()
    world.say(suspect.twist_line)
    world.say(f"Then the twist clicked into place: {suspect.true_trace}.")
    suspect_ent.meters["stain"] += 1
    suspect_ent.memes["worry"] += 1
    detective.meters["confidence"] += 1
    detective.memes["curiosity"] += 1

    world.para()
    world.say(f"{detective.id} smiled and explained the mystery kindly. {suspect.label} was not the troublemaker at all.")
    world.say(f"By the end, the clue made sense, the worry faded, and {detective.id} had solved the case with a careful brain and a warm heart.")

    return world


SETTING_REGISTRY: dict[str, Setting] = {
    "neighborhood": Setting(place="the little neighborhood", indoors=False, affordances={"detect"}),
    "schoolyard": Setting(place="the schoolyard", indoors=False, affordances={"detect"}),
    "backyard": Setting(place="the backyard", indoors=False, affordances={"detect"}),
}

CLUE_REGISTRY: dict[str, Clue] = {
    "muddy_bench": Clue(
        id="muddy_bench",
        label="mud on a bench",
        sign="a muddy smudge shaped like a little hiney print",
        at="the bench",
        weight="muddy and round",
        foreshadow="At the very edge of the bench, there was a tiny round print. It looked like a hiney mark, but it also had one little feather stuck in it.",
    ),
    "cookie_crumbs": Clue(
        id="cookie_crumbs",
        label="cookie crumbs",
        sign="a trail of crumbs by the steps",
        at="the steps",
        weight="crumbly and sweet",
        foreshadow="One crumb trail went straight along the path, and one crumb trail turned under the bush like it was trying to hide.",
    ),
    "paint_spot": Clue(
        id="paint_spot",
        label="blue paint",
        sign="a blue splatter on the gate",
        at="the gate",
        weight="bright and splashy",
        foreshadow="A blue dot sat on the gate rail, and there was a matching dot on the swing rope, as if somebody had brushed past in a hurry.",
    ),
}

SUSPECT_REGISTRY: dict[str, Suspect] = {
    "duck": Suspect(
        id="duck",
        label="Mister Quill the duck",
        type="duck",
        alibi="Mister Quill was wobbling beside the pond and pecking at crumbs by the water",
        likely_trace="the muddy print matched his soggy waddle",
        true_trace="Mister Quill had only walked through the yard after the real mischief was already done",
        twist_line="Mister Quill shook his feathers and pointed with his beak toward the flower pot.",
    ),
    "cat": Suspect(
        id="cat",
        label="Mrs. Mallow the cat",
        type="cat",
        alibi="Mrs. Mallow was curled on a porch chair, washing her paws with sleepy care",
        likely_trace="her little paw prints seemed like they could have made the crumbs",
        true_trace="Mrs. Mallow had not touched the cookies at all",
        twist_line="Mrs. Mallow blinked slowly and looked under the table, where something shiny was hiding.",
    ),
    "squirrel": Suspect(
        id="squirrel",
        label="Nibbles the squirrel",
        type="squirrel",
        alibi="Nibbles was on the fence, pretending to be innocent while chewing a seed shell",
        likely_trace="the quick little track looked as if it could have scattered the paint",
        true_trace="Nibbles had only watched the mess from the fence",
        twist_line="Nibbles flicked his tail toward the open toolbox, as if he already knew the answer.",
    ),
}

CURATED = [
    ("backyard", "muddy_bench", "duck", "Penny", "Milo"),
    ("schoolyard", "cookie_crumbs", "cat", "Lena", "Theo"),
    ("neighborhood", "paint_spot", "squirrel", "Ruby", "Owen"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small detective story world with foreshadowing, misunderstanding, and a twist."
    )
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--clue", choices=CLUE_REGISTRY)
    ap.add_argument("--suspect", choices=SUSPECT_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def reasonableness(setting: str, clue: str, suspect: str) -> bool:
    return setting in SETTING_REGISTRY and clue in CLUE_REGISTRY and suspect in SUSPECT_REGISTRY


def resolve_params(args: argparse.Namespace, rng: random.Random):
    if args.setting and args.clue and args.suspect and not reasonableness(args.setting, args.clue, args.suspect):
        raise StoryError("The chosen detective pieces do not fit this small mystery world.")
    settings = [args.setting] if args.setting else list(SETTING_REGISTRY)
    clues = [args.clue] if args.clue else list(CLUE_REGISTRY)
    suspects = [args.suspect] if args.suspect else list(SUSPECT_REGISTRY)
    choices = [(s, c, p) for s in settings for c in clues for p in suspects]
    if not choices:
        raise StoryError("No valid mystery combination is available.")
    setting, clue, suspect = rng.choice(choices)
    name = args.name or rng.choice(["Penny", "Ruby", "Lena", "Maya", "Iris"])
    helper = args.helper or rng.choice(["Milo", "Theo", "Owen", "Jules", "Ben"])
    return StoryParams(setting=setting, clue=clue, suspect=suspect, name=name, helper=helper, seed=args.seed)


@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    name: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for children that includes the word "hiney" and a clue that feels like foreshadowing.',
        f"Tell a gentle mystery where {f['detective'].id} notices {f['clue_cfg'].sign} and first suspects {f['suspect_cfg'].label}.",
        "Make the story include a misunderstanding, a twist, and a kind ending where the answer is explained clearly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    clue: Clue = f["clue_cfg"]
    qa = [
        QAItem(
            question=f"Who solved the mystery in {f['setting'].place}?",
            answer=f"{detective.id} solved the mystery with help from {helper.id}.",
        ),
        QAItem(
            question=f"What clue foreshadowed the answer?",
            answer=f"The clue was {clue.sign}, which hinted that something small and muddy had happened before the detective knew the truth.",
        ),
        QAItem(
            question=f"Who did {detective.id} misunderstand at first?",
            answer=f"{detective.id} first misunderstood {suspect.label} and thought {suspect.label} might have caused the mess.",
        ),
        QAItem(
            question=f"What word from the story helped make the clue feel funny and strange?",
            answer="The word hiney made the muddy print feel funny, but it still helped the detective notice an important detail.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective?",
            answer="A detective is a person who looks carefully for clues and tries to solve a mystery.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a little hint early on about what will matter later.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they are wrong at first.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise change that reveals the real answer in a new way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
clue(C) :- clue_fact(C).
suspect(P) :- suspect_fact(P).

related(S, C, P) :- setting(S), clue(C), suspect(P).
valid(S, C, P) :- related(S, C, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTING_REGISTRY:
        lines.append(asp.fact("setting_fact", s))
    for c in CLUE_REGISTRY:
        lines.append(asp.fact("clue_fact", c))
    for p in SUSPECT_REGISTRY:
        lines.append(asp.fact("suspect_fact", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, c, p) for s in SETTING_REGISTRY for c in CLUE_REGISTRY for p in SUSPECT_REGISTRY if reasonableness(s, c, p)}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTING_REGISTRY[params.setting]
    clue = CLUE_REGISTRY[params.clue]
    suspect = SUSPECT_REGISTRY[params.suspect]
    world = tell(setting, clue, suspect, params.name, params.helper)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} valid combinations:")
        for s, c, p in vals:
            print(f"  {s} / {c} / {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for i, (s, c, p, name, helper) in enumerate(CURATED):
            params = StoryParams(setting=s, clue=c, suspect=p, name=name, helper=helper, seed=base_seed + i)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
