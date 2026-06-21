#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jargon_bin_moral_value_mystery_to_solve.py
===========================================================================

A small fairy-tale storyworld about a child, a mysterious bin, strange jargon,
and a moral choice that unlocks the answer.

Premise
-------
A kind child finds a locked bin with puzzling jargon painted on it. The child
must decide whether to hide the bin, ignore it, or ask for help. The mystery is
solved by noticing what was tucked inside, and the ending proves a moral value:
truthfulness, kindness, or care for shared things.

Seed words: jargon, bin
Style: Fairy Tale
Features: Moral Value, Mystery to Solve
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"mystery": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "virtue": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Mystery:
    id: str
    label: str
    clue: str
    reveal: str
    jargon: str
    secret: str
    moral: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    place: str
    atmosphere: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    moral: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    ruler_name: str
    ruler_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "castle": Setting("castle", "the castle yard", "moonlit and hush-quiet", {"fairy", "mystery"}),
    "forest": Setting("forest", "the silver forest", "deep and twinkling", {"fairy", "mystery"}),
    "village": Setting("village", "the little village square", "busy by day, whisper-quiet by dusk", {"fairy", "mystery"}),
}

MYSTERIES = {
    "bin": Mystery(
        id="bin",
        label="bin",
        clue="a curious bin with painted jargon",
        reveal="the village lost key was tucked under the lid",
        jargon="Only the kind may open what is shared.",
        secret="the key was hidden to test honesty",
        moral="honesty",
        risk="hiding the bin would keep everyone guessing",
        tags={"bin", "jargon", "key", "honesty"},
    ),
    "lantern": Mystery(
        id="lantern",
        label="lantern",
        clue="a lantern with glowing jargon",
        reveal="a missing lantern glass was wrapped in cloth nearby",
        jargon="To mend what is broken, first tell the truth.",
        secret="the glass cracked during a careless game",
        moral="care",
        risk="blaming another would leave the lantern broken",
        tags={"lantern", "jargon", "glass", "care"},
    ),
    "muffin": Mystery(
        id="muffin",
        label="muffin tin",
        clue="a muffin tin with curly jargon",
        reveal="the baker's recipe card was hiding in the flour sack",
        jargon="Share the sweet thing, and the sweet thing is found.",
        secret="the recipe card was borrowed for a surprise feast",
        moral="kindness",
        risk="keeping the card secret would spoil the feast",
        tags={"muffin", "jargon", "recipe", "kindness"},
    ),
}

MORALS = {
    "honesty": "honesty is a bright lantern in the dark",
    "care": "care is how a small fix becomes a safe one",
    "kindness": "kindness helps everyone share the feast",
}

GIRL_NAMES = ["Luna", "Mina", "Elsa", "Pippa", "Iris", "Nora"]
BOY_NAMES = ["Arin", "Bram", "Crisp", "Dorian", "Evan", "Felix"]
HELPER_NAMES = ["Tilda", "Rowan", "Gwen", "Milo", "Hazel", "Otto"]
RULER_NAMES = ["Queen Mira", "King Cedric", "Queen Selene", "King Alder"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale mystery about jargon, a bin, and a moral choice.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--ruler")
    ap.add_argument("--ruler-gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, mo) for s in SETTINGS for m in MYSTERIES for mo in MORALS]


ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).
moral(Mo) :- moral_fact(Mo).
valid(S, M, Mo) :- setting(S), mystery(M), moral(Mo).
outcome(honesty) :- chosen_moral(honesty).
outcome(care) :- chosen_moral(care).
outcome(kindness) :- chosen_moral(kindness).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    for mo in MORALS:
        lines.append(asp.fact("moral_fact", mo))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python disagree.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def _pick(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.moral and args.moral not in MORALS:
        raise StoryError("Unknown moral.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.moral is None or c[2] == args.moral)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, moral = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or _pick(rng, GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    helper_name = args.helper or _pick(rng, HELPER_NAMES)
    ruler_gender = args.ruler_gender or rng.choice(["girl", "boy"])
    ruler_name = args.ruler or rng.choice(RULER_NAMES)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        moral=moral,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        ruler_name=ruler_name,
        ruler_gender=ruler_gender,
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    ruler = world.add(Entity(id=params.ruler_name, kind="character", type=params.ruler_gender, role="ruler", label="the ruler"))

    child.memes["curiosity"] += 1
    child.meters["mystery"] += 1
    world.facts["mystery"] = mystery
    world.facts["setting"] = setting
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["ruler"] = ruler

    world.say(
        f"Once in {setting.place}, under {setting.atmosphere}, {child.id} found {mystery.clue}. "
        f"The bin wore the oddest jargon: \"{mystery.jargon}\""
    )
    world.say(
        f"{child.id} blinked. \"What does that mean?\" {child.pronoun()} asked {helper.id}, "
        f"who hurried over like a friend in a storybook."
    )

    world.para()
    child.memes["doubt"] += 1
    world.say(
        f"{helper.id} peered at the bin and guessed it was a mystery to solve. "
        f"{helper.id} said the best path was not to hide it, but to tell {ruler.label_word if ruler.label else 'the ruler'}."
    )
    world.say(
        f"{child.id} carried the bin to {ruler.id} and spoke the truth, even though the answer might change what came next."
    )

    world.para()
    if mystery.moral == "honesty":
        child.memes["virtue"] += 1
        world.say(
            f"{ruler.id} lifted the lid and laughed softly. {mystery.reveal}. "
            f"\"{mystery.secret.capitalize()}\" {ruler.pronoun()} said, proud of the honest child."
        )
        world.say(
            f"The room felt lighter at once. {child.id} had chosen {mystery.moral}, and the bin was no longer a puzzle."
        )
    elif mystery.moral == "care":
        child.memes["virtue"] += 1
        world.say(
            f"{ruler.id} checked the bin carefully and found the truth: {mystery.reveal}. "
            f"By being careful and speaking plainly, {child.id} kept trouble from growing."
        )
        world.say(
            f"The mystery ended with a gentle repair, and everyone knew {MORALS['care']}."
        )
    else:
        child.memes["virtue"] += 1
        world.say(
            f"{ruler.id} opened the bin and found {mystery.reveal}. "
            f"The missing thing was returned, and a feast could begin at last."
        )
        world.say(
            f"{child.id} had chosen kindness, and the little world became warmer for it."
        )

    world.facts["outcome"] = mystery.moral
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    child: Entity = f["child"]
    return [
        f'Write a fairy-tale mystery for a 3-to-5-year-old that includes the words "jargon" and "bin".',
        f"Tell a story set in {setting.place} where {child.id} discovers a mysterious bin and solves the puzzle by telling the truth.",
        f"Write a child-friendly tale with a strange bin, a secret clue, and a moral ending about {mystery.moral}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    ruler: Entity = f["ruler"]
    answers = [
        QAItem(
            question="What did the child find?",
            answer=f"{child.id} found a mysterious bin with strange jargon painted on it. The bin was the first clue in the puzzle.",
        ),
        QAItem(
            question="Who helped solve the mystery?",
            answer=f"{helper.id} helped {child.id} think calmly and bring the bin to {ruler.id}. That made the truth easy to uncover.",
        ),
        QAItem(
            question="What moral value did the story teach?",
            answer=f"It taught {mystery.moral}. The ending showed that telling the truth and doing the kind thing solved the mystery well.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{ruler.id} opened the bin and the hidden thing was revealed. After that, everyone understood the odd jargon and the puzzle was finished.",
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question="What is jargon?",
            answer="Jargon is special or strange language that can sound hard to understand at first. In stories, it can make a clue feel mysterious.",
        ),
        QAItem(
            question="What is a bin?",
            answer="A bin is a container that can hold things inside it. In a mystery, a bin can hide a clue until someone opens it.",
        ),
        QAItem(
            question=f"Why is {mystery.moral} a good moral value?",
            answer=f"{mystery.moral.capitalize()} helps people do the right thing even when the answer is hidden. It makes the ending kinder and wiser.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="castle",
        mystery="bin",
        moral="honesty",
        child_name="Luna",
        child_gender="girl",
        helper_name="Tilda",
        helper_gender="girl",
        ruler_name="Queen Mira",
        ruler_gender="girl",
    ),
    StoryParams(
        setting="forest",
        mystery="lantern",
        moral="care",
        child_name="Arin",
        child_gender="boy",
        helper_name="Otto",
        helper_gender="boy",
        ruler_name="King Cedric",
        ruler_gender="boy",
    ),
    StoryParams(
        setting="village",
        mystery="muffin",
        moral="kindness",
        child_name="Mina",
        child_gender="girl",
        helper_name="Rowan",
        helper_gender="boy",
        ruler_name="Queen Selene",
        ruler_gender="girl",
    ),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.moral not in MORALS:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
