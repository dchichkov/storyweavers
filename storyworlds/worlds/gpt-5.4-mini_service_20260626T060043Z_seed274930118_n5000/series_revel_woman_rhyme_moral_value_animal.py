#!/usr/bin/env python3
"""
storyworlds/worlds/series_revel_woman_rhyme_moral_value_animal.py
==================================================================

A small animal-story world about a woman, a repeating series, a joyful revel,
and a gentle moral turn. The simulated premise is: a woman leads a tiny rhyme
series for animals in the meadow; one night the revel gets noisy, a small
problem appears, and the animals learn a moral value that changes how the story
ends.

The world is intentionally constraint-checked:
- the series must be something the setting can host
- the revel must be safe for the animals
- the moral turn must be grounded in the simulated state
- invalid choices raise StoryError with a clear reason

This script follows the storyworld contract:
- self-contained stdlib script under storyworlds/worlds/
- eagerly imports storyworlds/results.py
- lazily imports storyworlds/asp.py only in ASP helpers
- exposes StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "woman":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"girl", "boy", "child"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the meadow"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Series:
    id: str
    title: str
    activity: str
    sound: str
    repeat: str
    turns: int
    value: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    type: str
    label: str
    role: str
    flaw: str
    need: str
    meter: str
    problem: str


@dataclass
class Moral:
    id: str
    label: str
    prompt: str
    turn: str
    reward: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"song", "game"}),
    "barn": Setting(place="the barn loft", indoor=True, affords={"song", "game"}),
    "orchard": Setting(place="the orchard", affords={"song"}),
}

SERIES = {
    "rhyme_circle": Series(
        id="rhyme_circle",
        title="the rhyme circle",
        activity="sing little rhymes",
        sound="soft rhyme",
        repeat="every week",
        turns=3,
        value="sharing",
        keyword="rhyme",
        tags={"rhyme", "series"},
    ),
    "revel_song": Series(
        id="revel_song",
        title="the revel song",
        activity="dance and sing",
        sound="bright chorus",
        repeat="at sunset",
        turns=2,
        value="joy",
        keyword="revel",
        tags={"revel", "song"},
    ),
}

ANIMALS = {
    "rabbit": Animal("rabbit", "rabbit", "little rabbit", "listener", "stole berries", "wait for a turn", "greed", "shared berries"),
    "fox": Animal("fox", "fox", "small fox", "helper", "spoke too loudly", "use a quiet voice", "noise", "soft voice"),
    "bear": Animal("bear", "bear", "gentle bear", "singer", "kept the drum", "pass the drum", "taking", "shared drum"),
    "mouse": Animal("mouse", "mouse", "tiny mouse", "dancer", "hid the ribbon", "bring back the ribbon", "hiding", "returned ribbon"),
}

MORALS = {
    "share": Moral("share", "share", "everyone gets a turn", "the animals wait and pass things along", "the circle feels fair", {"sharing"}),
    "honest": Moral("honest", "honest", "it is better to tell the truth", "the animal who erred admits it", "the mood grows kind again", {"truth"}),
    "gentle": Moral("gentle", "gentle", "soft words keep a group calm", "voices drop and paws slow down", "the revel becomes sweet instead of wild", {"voice"}),
}

WOMAN_NAMES = ["Mira", "Nina", "Lena", "Ada", "Ivy", "Rose"]
ANIMAL_NAMES = ["Pip", "Milo", "Tansy", "Poppy", "Bram", "Fern"]
TRAITS = ["kind", "patient", "cheerful", "bright", "calm"]


def kind_reasonable(series: Series, moral: Moral, setting: Setting) -> bool:
    if "rhyme" in series.tags and "song" not in setting.affords:
        return False
    if series.id == "revel_song" and setting.indoor:
        return True
    return True


def explain_rejection(series: Series, moral: Moral) -> str:
    return f"(No story: the {series.title} and the moral {moral.label} do not fit this setting together.)"


@dataclass
class StoryParams:
    setting: str
    series: str
    animal: str
    moral: str
    woman: str
    animal_name: str
    trait: str
    seed: Optional[int] = None


@dataclass
class StoryWorld:
    world: World
    woman: Entity
    animal: Entity
    series: Series
    moral: Moral
    setting: Setting


def build_story_world(params: StoryParams) -> StoryWorld:
    setting = SETTINGS[params.setting]
    series = SERIES[params.series]
    animal_cfg = ANIMALS[params.animal]
    moral = MORALS[params.moral]
    world = World(setting)

    woman = world.add(Entity(id=params.woman, kind="character", type="woman", label="the woman"))
    animal = world.add(Entity(
        id=params.animal_name,
        kind="character",
        type=animal_cfg.type,
        label=animal_cfg.label,
        meters={animal_cfg.meter: 0.0},
        memes={},
    ))
    world.facts.update(
        setting=setting, series=series, animal_cfg=animal_cfg, moral=moral, woman=woman, animal=animal
    )
    return StoryWorld(world=world, woman=woman, animal=animal, series=series, moral=moral, setting=setting)


def do_series(sw: StoryWorld) -> None:
    w = sw.world
    woman, animal, series, moral = sw.woman, sw.animal, sw.series, sw.moral

    w.say(
        f"{woman.id} was a {w.facts.get('trait', 'kind')} woman who loved to lead {series.title} {series.repeat}."
    )
    w.say(
        f"In {w.setting.place}, she invited {animal.label} and the other animals to {series.activity}."
    )
    w.say(
        f"The little group liked the {series.sound}, and the evening began to feel like a happy {series.keyword}."
    )
    w.para()

    if series.id == "revel_song":
        animal.meters["noise"] = 1.0
        animal.memes["excitement"] = 1.0
        w.say(
            f"But the revel grew so loud that {animal.label} forgot to listen and started to hop ahead of the circle."
        )
        animal.memes["restless"] = 1.0
        woman.memes["worry"] = 1.0
        w.say(
            f"{woman.id} lifted a gentle hand and said that loud fun was good, but the group still needed room to breathe."
        )
    else:
        animal.meters["greed"] = 1.0
        animal.memes["want"] = 1.0
        w.say(
            f"Then {animal.label} kept a ribbon and tried to skip ahead, so the next animal had no turn."
        )
        woman.memes["worry"] = 1.0
        w.say(
            f"{woman.id} noticed the circle wobble and asked everyone to pause and look at the missing turn."
        )

    w.para()
    animal.memes["shame"] = 1.0
    if moral.id == "share":
        animal.memes["care"] = 1.0
        w.say(
            f"{animal.label} looked down, shared the missing thing, and waited while the others went first."
        )
    elif moral.id == "honest":
        animal.memes["honest"] = 1.0
        w.say(
            f"{animal.label} told the truth at once, and that honest word made the group calm again."
        )
    else:
        animal.memes["calm"] = 1.0
        w.say(
            f"{woman.id} spoke softly, and soon {animal.label} lowered the paws and matched the slow rhythm."
        )

    w.say(
        f"By the end, the {series.title} felt better than before: the animals had a clearer way to be together, and {woman.id} smiled at the warm little circle."
    )
    w.facts["resolved"] = True


def generation_prompts(sw: StoryWorld) -> list[str]:
    f = sw.world.facts
    series = f["series"]
    moral = f["moral"]
    animal = f["animal"]
    woman = f["woman"]
    return [
        f'Write a short animal story about a woman leading {series.title} with a moral value like {moral.label}.',
        f"Tell a gentle story where {woman.id} helps {animal.label} and the animals move from noisy revelry to a better choice.",
        f'Write a tiny story in an animal-story style that includes a rhyme series and ends with a clear moral turn.',
    ]


def story_qa(sw: StoryWorld) -> list[QAItem]:
    f = sw.world.facts
    animal_cfg: Animal = f["animal_cfg"]
    series: Series = f["series"]
    moral: Moral = f["moral"]
    woman: Entity = f["woman"]
    animal: Entity = f["animal"]

    return [
        QAItem(
            question=f"Who led the {series.title} in {sw.setting.place}?",
            answer=f"{woman.id} led the {series.title} in {sw.setting.place}, and {animal.label} joined the animals there.",
        ),
        QAItem(
            question=f"What did {animal.label} need to learn during the story?",
            answer=f"{animal.label} needed to learn to {animal_cfg.need}, because the first choice was causing trouble in the circle.",
        ),
        QAItem(
            question=f"What moral value did the woman guide the animals toward?",
            answer=f"The story moved toward being {moral.label}: {moral.prompt}. That change made the revel feel kinder at the end.",
        ),
        QAItem(
            question=f"How did the problem change by the end of the series?",
            answer=f"At first {animal.label} caused a small problem, but by the end the group had settled into a better way, and the animals could stay together happily.",
        ),
    ]


def world_knowledge_qa(sw: StoryWorld) -> list[QAItem]:
    f = sw.world.facts
    series: Series = f["series"]
    moral: Moral = f["moral"]
    out = [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a sound pattern where words end in similar sounds, like when little lines of speech fit together in a playful way.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good idea about how to act, such as being kind, honest, or fair.",
        ),
        QAItem(
            question="Why can a repeated series help children?",
            answer="A repeated series can help because it gives a familiar pattern, so children can remember what comes next and feel safe with the story.",
        ),
    ]
    if "rhyme" in series.tags:
        out.append(QAItem(
            question="Why do rhyme circles sound fun?",
            answer="Rhyme circles sound fun because the repeating sounds make the words bounce together like a game.",
        ))
    if moral.id == "share":
        out.append(QAItem(
            question="Why is sharing helpful?",
            answer="Sharing is helpful because it lets everyone have a turn and keeps the group fair.",
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


def dump_trace(sw: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in sw.world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(params: StoryParams) -> StoryWorld:
    sw = build_story_world(params)
    sw.world.facts["trait"] = params.trait
    do_series(sw)
    return sw


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id, setting in SETTINGS.items():
        for series_id, series in SERIES.items():
            for moral_id, moral in MORALS.items():
                if kind_reasonable(series, moral, setting):
                    out.append((setting_id, series_id, moral_id))
    return out


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, series in SERIES.items():
        lines.append(asp.fact("series", sid))
        for t in sorted(series.tags):
            lines.append(asp.fact("tag", sid, t))
        lines.append(asp.fact("turns", sid, series.turns))
    for mid, moral in MORALS.items():
        lines.append(asp.fact("moral", mid))
        for t in sorted(moral.tags):
            lines.append(asp.fact("mtag", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, R, M) :- setting(S), series(R), moral(M), compatible(S, R, M).
compatible(S, R, M) :- affords(S, song), tag(R, rhyme), mtag(M, sharing).
compatible(S, R, M) :- indoor(S), tag(R, revel).
compatible(S, R, M) :- series(R), moral(M), not tag(R, rhyme), not mtag(M, sharing).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    c = set(asp_valid_combos())
    if p == c:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if p - c:
        print("  only in python:", sorted(p - c))
    if c - p:
        print("  only in clingo:", sorted(c - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with rhyme, revel, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--series", choices=SERIES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--woman")
    ap.add_argument("--animal-name")
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
    combos = valid_combos()
    if args.setting and args.series and args.moral:
        if (args.setting, args.series, args.moral) not in combos:
            raise StoryError(explain_rejection(SERIES[args.series], MORALS[args.moral]))
    combos = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.series is None or c[1] == args.series)
        and (args.moral is None or c[2] == args.moral)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, series, moral = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(sorted(ANIMALS))
    woman = args.woman or rng.choice(WOMAN_NAMES)
    animal_name = args.animal_name or rng.choice(ANIMAL_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, series=series, animal=animal, moral=moral, woman=woman, animal_name=animal_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    sw = tell(params)
    return StorySample(
        params=params,
        story=sw.world.render(),
        prompts=generation_prompts(sw),
        story_qa=story_qa(sw),
        world_qa=world_knowledge_qa(sw),
        world=sw,
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
    StoryParams(setting="meadow", series="rhyme_circle", animal="rabbit", moral="share", woman="Mira", animal_name="Pip", trait="kind"),
    StoryParams(setting="barn", series="revel_song", animal="fox", moral="gentle", woman="Ada", animal_name="Milo", trait="patient"),
    StoryParams(setting="orchard", series="rhyme_circle", animal="bear", moral="honest", woman="Lena", animal_name="Bram", trait="calm"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
