#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50/exam_businessman_commission_rhyme_animal_story.py
===============================================================================================================

A small Animal-Story-style world about an animal who has an exam, a businessman
who wants a commission, and a rhyming choice between rushing for money and
studying with care.

Seed words:
- exam
- businessman
- commission

Style:
- Animal Story

Feature:
- Rhyme

The premise is simple: a clever little animal prepares for an exam, meets a
businessman who offers a commission for quick work, and must decide whether to
chase the coin or finish the lesson. The story is built from simulated world
state, not from a frozen paragraph with swapped nouns.

This file is standalone and uses only the standard library plus the shared
storyworld result containers. ASP support is included as an inline twin.

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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they" if self.kind == "character" else "it"


@dataclass
class Setting:
    id: str
    place: str
    rhyme_line: str
    school: str
    market: str
    exam_subject: str
    reward: str


@dataclass
class Offer:
    id: str
    label: str
    quick_job: str
    commission_name: str
    rush_rhyme: str
    safe_rhyme: str
    legal: bool = True


@dataclass
class StoryParams:
    setting: str
    animal: str
    businessman: str
    offer: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "schoolyard": Setting(
        id="schoolyard",
        place="under the schoolyard tree",
        rhyme_line="The bell went ring, the leaves went sing.",
        school="the little school",
        market="the corner market",
        exam_subject="reading",
        reward="a gold star",
    ),
    "farm": Setting(
        id="farm",
        place="beside the hay barn",
        rhyme_line="The hay went swish, the clouds went wish.",
        school="the barn school",
        market="the muddy lane",
        exam_subject="counting",
        reward="a warm pat on the back",
    ),
    "harbor": Setting(
        id="harbor",
        place="near the dock by the sea",
        rhyme_line="The tide went sway, the gulls cried hey.",
        school="the seaside school",
        market="the pier market",
        exam_subject="spelling",
        reward="a bright ribbon",
    ),
}

ANIMALS = {
    "rabbit": ("rabbit", "bunny", "small", "quick", "hop"),
    "fox": ("fox", "fox", "red", "smart", "sly"),
    "bear": ("bear", "bear", "brown", "slow", "steady"),
    "mouse": ("mouse", "mouse", "tiny", "nimble", "peep"),
}

OFFERS = {
    "coin_run": Offer(
        id="coin_run",
        label="the coin run",
        quick_job="carry bundles to the market",
        commission_name="a commission",
        rush_rhyme="If you hurry, you get more flurry.",
        safe_rhyme="If you study first, your brain feels nourished.",
    ),
    "poster_run": Offer(
        id="poster_run",
        label="the poster run",
        quick_job="deliver shiny posters",
        commission_name="a commission",
        rush_rhyme="If you race, you may lose your place.",
        safe_rhyme="If you read the page, you can pass the stage.",
    ),
    "parcel_run": Offer(
        id="parcel_run",
        label="the parcel run",
        quick_job="push a parcel cart",
        commission_name="a commission",
        rush_rhyme="If you dash, the cart may splash.",
        safe_rhyme="If you stay steady, you will be ready.",
    ),
}

BUSINESSMAN_NAMES = ["Mr. Pine", "Mr. Reed", "Mr. Wren", "Mr. Clover"]
ANIMAL_NAMES = ["Nib", "Pip", "Milo", "Tara", "Lulu", "Bram", "Zizi", "Roo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story about an exam and a commission, with rhyme.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--businessman", choices=BUSINESSMAN_NAMES)
    ap.add_argument("--offer", choices=OFFERS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    animal = args.animal or rng.choice(list(ANIMALS))
    businessman = args.businessman or rng.choice(BUSINESSMAN_NAMES)
    offer = args.offer or rng.choice(list(OFFERS))
    return StoryParams(setting=setting, animal=animal, businessman=businessman, offer=offer)


def asp_facts() -> str:
    import asp

    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for oid, offer in OFFERS.items():
        lines.append(asp.fact("offer", oid))
        if offer.legal:
            lines.append(asp.fact("legal", oid))
    lines.append(asp.fact("chance_to_study", 1))
    lines.append(asp.fact("chance_to_work", 1))
    return "\n".join(lines)


ASP_RULES = r"""
chosen(S,A,O) :- setting(S), animal(A), offer(O).
legal_choice(O) :- offer(O), legal(O).
#show chosen/3.
#show legal_choice/1.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show chosen/3."))
    return sorted(set(asp.atoms(model, "chosen")))


def asp_verify() -> int:
    python_set = {(s, a, o) for s in SETTINGS for a in ANIMALS for o in OFFERS}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python ({len(python_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def make_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    setting = SETTINGS[params.setting]
    animal_word, animal_kind, color, speed, sound = ANIMALS[params.animal]
    offer = OFFERS[params.offer]

    w = World()
    child = w.add(Entity(id="child", kind="character", type=animal_kind, label=animal_word, role="student"))
    businessman = w.add(Entity(id="businessman", kind="character", type="man", label=params.businessman, role="seller"))
    school = w.add(Entity(id="school", kind="place", label=setting.school))
    market = w.add(Entity(id="market", kind="place", label=setting.market))

    child.memes["hope"] = 1.0
    child.memes["worry"] = 1.0
    child.meters["prepared"] = 0.0
    businessman.memes["pride"] = 1.0
    businessman.attrs["offer"] = offer.id

    w.facts.update(
        setting=setting,
        animal=animal_word,
        businessman=params.businessman,
        offer=offer,
        exam_subject=setting.exam_subject,
        reward=setting.reward,
        animal_kind=animal_kind,
        color=color,
        speed=speed,
        sound=sound,
        place=setting.place,
    )

    w.say(
        f"At {setting.place}, a little {animal_word} had an {setting.exam_subject} exam to meet."
    )
    w.say(
        f"{setting.rhyme_line} The {animal_word} held a book with care, "
        f"and hoped to shine fair and square."
    )
    w.para()
    w.say(
        f"{params.businessman} came by with {offer.commission_name} and a quick little grin."
    )
    w.say(
        f'"Come make {offer.label} for me," said the businessman, "and the coin will roll in."'
    )
    w.say(
        f'The offer promised {offer.quick_job}, and the path sounded neat and thin.'
    )

    study_first = rng.choice([True, True, False])
    if study_first:
        child.memes["focus"] = 1.0
        child.meters["prepared"] = 1.0
        w.para()
        w.say(
            f'The {animal_word} shook their head and kept to the page, because study first is the wisest way.'
        )
        w.say(
            f'"If I rush for the money, I may miss the exam," the little one sang. '
            f'"I will learn, then earn, and keep my worries away."'
        )
        w.para()
        w.say(
            f'After the test, the answers came clear and bright, and the {animal_word} passed with delight.'
        )
        w.say(
            f'Only then did they help with the {offer.label}, so the commission felt light.'
        )
        w.say(
            f"The businessman paid fairly, and the little one skipped home in the evening light."
        )
        outcome = "studied"
    else:
        child.memes["tempted"] = 1.0
        w.para()
        w.say(
            f'The {animal_word} almost went with the businessman, drawn by the coin and the shine.'
        )
        w.say(
            f'"A commission now? A lesson later?" they wondered. "That may not be fine."'
        )
        w.say(
            f'Then they remembered the exam and their schoolbook line, and chose to stay in line.'
        )
        w.para()
        w.say(
            f"They studied at once, then took the exam with a grin, and passed just in time."
        )
        w.say(
            f"Afterward, the businessman got help with the job, and everyone left in rhyme."
        )
        outcome = "almost_wooed"

    w.facts["outcome"] = outcome
    return w


def generation_prompts(world: World) -> list[str]:
    s: Setting = world.facts["setting"]  # type: ignore[assignment]
    o: Offer = world.facts["offer"]  # type: ignore[assignment]
    animal = world.facts["animal"]
    businessman = world.facts["businessman"]
    return [
        f"Write an Animal Story rhyme about a little {animal} who has an {s.exam_subject} exam and meets {businessman} with {o.commission_name}.",
        f"Tell a child-friendly story where the {animal} must choose between studying for an exam and taking {o.label}, and the ending rhymes.",
        f"Make a short rhyme story in an Animal Story style: the {animal}, the businessman, an exam, and a wise choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    s: Setting = world.facts["setting"]  # type: ignore[assignment]
    o: Offer = world.facts["offer"]  # type: ignore[assignment]
    animal = world.facts["animal"]
    businessman = world.facts["businessman"]
    return [
        QAItem(
            question=f"Who had the exam in the story?",
            answer=f"The little {animal} had the exam at {s.school}.",
        ),
        QAItem(
            question=f"What did {businessman} offer?",
            answer=f"{businessman} offered {o.commission_name} and asked the {animal} to do {o.quick_job}.",
        ),
        QAItem(
            question="What did the animal choose to do first?",
            answer="The animal chose to study first, so the exam could go well.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the exam going well and the commission handled after the lesson.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    s: Setting = world.facts["setting"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What is an exam?",
            answer="An exam is a test that asks you to show what you know.",
        ),
        QAItem(
            question="What is a businessman?",
            answer="A businessman is a grown-up who works with buying, selling, or making business deals.",
        ),
        QAItem(
            question="What is a commission?",
            answer="A commission is a job or payment arrangement where someone is asked to do a task for money.",
        ),
        QAItem(
            question=f"Why did the animal need to study for the {s.exam_subject} exam?",
            answer=f"The animal needed to study so the answers would be ready for the {s.exam_subject} exam.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        lines.append(f"  {ent.id}: role={ent.role} meters={ent.meters} memes={ent.memes} attrs={ent.attrs}")
    lines.append(f"  facts={ {k: v for k, v in world.facts.items() if k in ('setting','animal','businessman','offer','outcome')} }")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
    StoryParams(setting="schoolyard", animal="rabbit", businessman="Mr. Pine", offer="coin_run"),
    StoryParams(setting="farm", animal="fox", businessman="Mr. Reed", offer="poster_run"),
    StoryParams(setting="harbor", animal="mouse", businessman="Mr. Wren", offer="parcel_run"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show chosen/3.\n#show legal_choice/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
