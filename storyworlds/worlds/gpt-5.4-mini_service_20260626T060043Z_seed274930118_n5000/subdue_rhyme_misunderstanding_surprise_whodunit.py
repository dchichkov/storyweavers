#!/usr/bin/env python3
"""
Standalone Storyworld: a small whodunit with rhyme, misunderstanding, surprise,
and a gentle subduing of the culprit's scurry.

Premise:
- A child detective notices something missing in a small setting.
- Clues appear as rhymes, but a misunderstanding sends the detective in the
  wrong direction.
- A surprise reveal shows the real culprit and how they were subdued calmly.

The world model tracks physical meters and emotional memes, and the prose is
driven by state changes rather than a fixed template.
"""

from __future__ import annotations

import argparse
import copy
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("missing", "found", "caught", "sealed"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "relief", "surprise", "understanding", "confusion", "fear", "pride"):
            self.memes.setdefault(k, 0.0)

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
    features: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    missing_item: str
    missing_phrase: str
    clue_rhyme: str
    false_lead: str
    true_culprit: str
    true_culprit_kind: str
    surprise: str
    way_hidden: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "kitchen": Setting("the kitchen", {"table", "cupboard", "jar"}),
    "classroom": Setting("the classroom", {"desk", "shelf", "chalkboard"}),
    "playroom": Setting("the playroom", {"toy box", "rug", "window"}),
}

MYSTERIES = {
    "cookie": Mystery(
        missing_item="cookie",
        missing_phrase="a plate of tiny sugar cookies",
        clue_rhyme="When crumbs are near, the answer is clear.",
        false_lead="the wind by the window",
        true_culprit="the sleepy cat",
        true_culprit_kind="cat",
        surprise="The cat was napping inside the basket, crumbs on its whiskers.",
        way_hidden="under a dish towel",
    ),
    "bell": Mystery(
        missing_item="bell",
        missing_phrase="a little silver bell",
        clue_rhyme="Where things chime, look by rhyme.",
        false_lead="the hallway echo",
        true_culprit="the shiny magpie",
        true_culprit_kind="bird",
        surprise="The magpie had tucked the bell into a nest of ribbon scraps.",
        way_hidden="in a ribbon nest",
    ),
    "paintbrush": Mystery(
        missing_item="paintbrush",
        missing_phrase="a blue paintbrush",
        clue_rhyme="Wet paint, faint complaint.",
        false_lead="the dripping sink",
        true_culprit="the eager puppy",
        true_culprit_kind="dog",
        surprise="The puppy had dragged the brush under the easel to chew the end.",
        way_hidden="behind the easel",
    ),
}

NAMES = {
    "girl": ["Mia", "Luna", "Ivy", "Nora", "Zoe"],
    "boy": ["Leo", "Finn", "Max", "Theo", "Eli"],
}
HELPERS = {
    "girl": ["June", "Pia", "Maya"],
    "boy": ["Ben", "Owen", "Sam"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with rhyme, misunderstanding, and surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def is_reasonable(setting: Setting, mystery: Mystery) -> bool:
    return mystery.missing_item in {"cookie", "bell", "paintbrush"} and len(setting.features) >= 3


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p, s in SETTINGS.items() for m in MYSTERIES if is_reasonable(s, MYSTERIES[m])]


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the setting {place} does not support a convincing small whodunit for {mystery}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery and not is_reasonable(SETTINGS[args.place], MYSTERIES[args.mystery]):
        raise StoryError(explain_rejection(args.place, args.mystery))
    combos = valid_combos()
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(NAMES[gender])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper_name = args.helper_name or rng.choice(HELPERS[helper_gender])
    return StoryParams(place=place, mystery=mystery, detective_name=detective_name, detective_type=gender, helper_name=helper_name, helper_type=helper_gender)


def rhyme_clue(m: Mystery) -> str:
    return m.clue_rhyme


def tell(setting: Setting, mystery: Mystery, detective_name: str, detective_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    det = world.add(Entity(id=detective_name, kind="character", type=detective_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    item = world.add(Entity(id="missing", type=mystery.missing_item, label=mystery.missing_item, phrase=mystery.missing_phrase, owner=det.id))
    culprit = world.add(Entity(id="culprit", kind="character", type=mystery.true_culprit_kind, label=mystery.true_culprit))
    culprit.memes["surprise"] += 0
    item.meters["missing"] = 1.0
    world.facts.update(det=det, helper=helper, item=item, culprit=culprit, mystery=mystery)

    world.say(f"{det.id} was a small detective with bright eyes and a careful step.")
    world.say(f"At {setting.place}, {det.id} noticed that {mystery.missing_phrase} had gone missing.")
    world.say(f"{det.id} did not shout. {det.pronoun().capitalize()} only looked around and said, \"Someone left a clue.\"")
    world.say(f"{helper.id} joined {det.id} and frowned at the empty spot.")
    world.para()
    world.say(f"Near the table, they found a rhyme written in crumb dust: \"{rhyme_clue(mystery)}\"")
    det.memes["curiosity"] += 1
    helper.memes["confusion"] += 1
    world.say(f"{det.id} thought the words meant {mystery.false_lead}, so {det.pronoun()} peered there first.")
    world.say(f"But that was a misunderstanding; the whisper of the room was not the real clue.")
    helper.memes["confusion"] += 1
    world.para()
    world.say(f"Then came a surprise. A tiny sound rustled by {mystery.way_hidden}.")
    culprit.meters["caught"] += 1
    culprit.memes["fear"] += 1
    det.memes["surprise"] += 1
    world.say(mystery.surprise)
    world.say(f"{det.id} stayed calm and softly blocked the way, so the {mystery.true_culprit_kind} could not dash off.")
    culprit.meters["sealed"] += 1
    world.say(f"{helper.id} gently lifted the towel, and the missing {mystery.missing_item} was there all along.")
    item.meters["found"] = 1.0
    det.memes["understanding"] += 1
    helper.memes["relief"] += 1
    world.say(f"In the end, {det.id} smiled. The case was solved, the mix-up was cleared, and the room felt still again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = f["det"]
    mystery = f["mystery"]
    return [
        f"Write a short whodunit story for a child detective named {det.id} in {world.setting.place} about a missing {mystery.missing_item}.",
        f"Tell a gentle mystery that uses a rhyme clue, a misunderstanding, and a surprise reveal.",
        f"Write a simple detective story where the missing {mystery.missing_item} is found after someone is calmly subdued.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["det"]
    helper = f["helper"]
    mystery = f["mystery"]
    culprit = f["culprit"]
    return [
        QAItem(
            question=f"What kind of story is this one about {det.id} and {helper.id}?",
            answer=f"It is a small whodunit. {det.id} investigates a missing {mystery.missing_item}, follows a rhyme, and solves the mystery in the end.",
        ),
        QAItem(
            question=f"What clue did {det.id} find near the table?",
            answer=f"{det.id} found a rhyme: \"{mystery.clue_rhyme}\" It pointed toward the answer, even though it first caused a misunderstanding.",
        ),
        QAItem(
            question=f"Why did {det.id} look in the wrong place first?",
            answer=f"{det.id} thought the clue meant {mystery.false_lead}, so {det.pronoun()} checked that spot before realizing the rhyme meant something else.",
        ),
        QAItem(
            question=f"What was the surprise at the end of the case?",
            answer=f"The surprise was that {mystery.surprise.lower()} The real culprit was {culprit.label}, and the missing {mystery.missing_item} was found nearby.",
        ),
        QAItem(
            question=f"How was the culprit subdued?",
            answer=f"{det.id} stayed calm and blocked the way, so the {culprit.type} could not run off. That gentle stop subdued the trouble without any harm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a rhyme?", answer="A rhyme is when words sound alike at the end, like cake and lake."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone gets the meaning wrong at first."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that makes people pause and notice."),
        QAItem(question="What does subdued mean?", answer="Subdued means gently stopped or calmed so something cannot keep causing trouble."),
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- fact_setting(S).
mystery(M) :- fact_mystery(M).

valid_story(S,M) :- fact_setting(S), fact_mystery(M), supported(S,M).

supported(S,M) :- fact_feature(S,table), fact_feature(S,cupboard), fact_feature(S,jar), fact_mystery(M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s, setting in SETTINGS.items():
        lines.append(asp.fact("fact_setting", s))
        for feat in sorted(setting.features):
            lines.append(asp.fact("fact_feature", s, feat))
    for m in MYSTERIES:
        lines.append(asp.fact("fact_mystery", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.detective_name, params.detective_type, params.helper_name, params.helper_type)
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
    StoryParams(place="kitchen", mystery="cookie", detective_name="Mia", detective_type="girl", helper_name="Ben", helper_type="boy"),
    StoryParams(place="classroom", mystery="bell", detective_name="Leo", detective_type="boy", helper_name="June", helper_type="girl"),
    StoryParams(place="playroom", mystery="paintbrush", detective_name="Nora", detective_type="girl", helper_name="Sam", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
