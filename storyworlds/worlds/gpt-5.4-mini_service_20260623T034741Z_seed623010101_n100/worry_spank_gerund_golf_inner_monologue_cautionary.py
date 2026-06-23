#!/usr/bin/env python3
"""
storyworlds/worlds/worry_spank_gerund_golf_inner_monologue_cautionary.py
=========================================================================

A standalone storyworld: a tiny whodunit at a miniature golf course, told with
inner monologue, cautionary tension, and a transformation at the end.

Seed premise:
- Words: worry, spanking (spank-gerund), golf
- Features: Inner Monologue, Cautionary, Transformation
- Style: Whodunit

A child detective notices a missing golf ball, worries over the clue trail,
thinks through suspects in private, and learns the true culprit was a harmless
accident that gets transformed into an honest fix.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


@dataclass
class StoryParams:
    place: str = "mini_golf"
    clue: str = "scorecard"
    culprit: str = "wind"
    child_name: str = "Maya"
    child_gender: str = "girl"
    helper_name: str = "Jo"
    helper_gender: str = "boy"
    adult_name: str = "Auntie"
    adult_gender: str = "woman"
    seed: Optional[int] = None


PLACES = {
    "mini_golf": "the little golf course",
    "clubhouse": "the clubhouse by the golf course",
    "practice_green": "the practice green",
}

CLUES = {
    "scorecard": "a scorecard",
    "ball_marker": "a tiny ball marker",
    "tee": "a yellow tee",
}

CULPRITS = {
    "wind": "the wind",
    "cart_bump": "a cart bump",
    "borrowed_pocket": "a borrowed pocket",
}

GIRL_NAMES = ["Maya", "Nina", "Ruby", "Ivy", "Lena"]
BOY_NAMES = ["Jo", "Toby", "Finn", "Arlo", "Ben"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_panic(world: World) -> list[str]:
    child = world.get("child")
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return []
    if world.facts.get("clue_missing"):
        child.memes["panic"] = 1.0
        return ["__panic__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for rule in RULES:
        sents = rule.apply(world)
        out.extend(sents)
    if narrate:
        for s in out:
            if s != "__panic__":
                world.say(s)
    return [s for s in out if s != "__panic__"]


RULES = [Rule("panic", _r_panic)]


def story_setup(world: World) -> None:
    child = world.add(Entity(id="child", kind="character", type=world.facts["child_gender"], label=world.facts["child_name"]))
    helper = world.add(Entity(id="helper", kind="character", type=world.facts["helper_gender"], label=world.facts["helper_name"]))
    adult = world.add(Entity(id="adult", kind="character", type=world.facts["adult_gender"], label=world.facts["adult_name"]))
    clue = world.add(Entity(id="clue", type="thing", label=CLUES[world.facts["clue"]], phrase=CLUES[world.facts["clue"]]))
    culprit = world.add(Entity(id="culprit", type="thing", label=CULPRITS[world.facts["culprit"]], phrase=CULPRITS[world.facts["culprit"]]))
    for ent in (child, helper, adult, clue, culprit):
        ent.meters.setdefault("seen", 0.0)
        ent.memes.setdefault("worry", 0.0)
        ent.memes.setdefault("curiosity", 0.0)
        ent.memes.setdefault("relief", 0.0)
    child.memes["worry"] = 1.0
    child.memes["curiosity"] = 1.0
    helper.memes["curiosity"] = 1.0
    world.facts.update(child=child, helper=helper, adult=adult, clue_ent=clue, culprit_ent=culprit)


def tell_world(params: StoryParams) -> World:
    world = World(setting=PLACES[params.place])
    world.facts.update(
        place=params.place,
        clue=params.clue,
        culprit=params.culprit,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_name=params.adult_name,
        adult_gender=params.adult_gender,
        clue_missing=True,
    )
    story_setup(world)
    child = world.get("child")
    helper = world.get("helper")
    adult = world.get("adult")
    clue = world.get("clue")
    culprit = world.get("culprit")

    world.say(
        f"{child.label} and {helper.label} were at {world.setting}, where every hole looked like a tiny puzzle."
    )
    world.say(
        f"{child.label} loved golf, but today {clue.label} was missing from the starter table."
    )
    world.say(
        f"{child.label} kept a private thought to {child.pronoun('possessive')}self: "
        f"why would anyone take {clue.label} from a game that needed it?"
    )

    world.para()
    child.memes["worry"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"{helper.label} noticed a clue trail near the cup, and {child.label} noticed {culprit.label} by the grass."
    )
    world.say(
        f'{child.label} wondered, "Was it a thief, or just an accident?"'
    )
    world.say(
        f'{child.label} also thought of the loud spanking sound from the cart door, and that made the clue feel stranger.'
    )

    world.para()
    propagate(world, narrate=False)
    culprit.meters["seen"] = 1.0
    child.memes["worry"] += 1
    world.say(
        f"{adult.label} came over and looked carefully, not angry, only attentive."
    )
    world.say(
        f'Then {adult.label} smiled. "{clue.label.capitalize()} slid into the cart pocket when the cart bumped the rail."'
    )
    world.say(
        f"{helper.label} found it, and the mystery changed shape: nobody had stolen anything."
    )

    world.para()
    child.memes["worry"] = 0.0
    child.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    world.say(
        f"{child.label} felt the worry leave like a cloud breaking apart."
    )
    world.say(
        f"{adult.label} handed back the {clue.label}, and the little golf game could begin again."
    )
    world.say(
        f"By the last hole, the clue sat safely on the table, and the day had turned from suspicion into play."
    )

    world.facts.update(resolved=True, clue_found=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly whodunit at a golf course that includes the words "worry" and "golf".',
        f"Tell a small mystery where {f['child_name']} worries about a missing {CLUES[f['clue']]}, thinks privately, and learns the truth.",
        f'Write a cautionary story about a golf game where a strange "spanking" sound turns out to be an accident, not a crime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.get("child")
    helper = world.get("helper")
    adult = world.get("adult")
    clue = world.get("clue")
    culprit = world.get("culprit")
    return [
        QAItem(
            question=f"What kind of game were {child.label} and {helper.label} playing?",
            answer=f"They were playing golf at {world.setting}. The little course made the day feel like a mystery with holes to inspect.",
        ),
        QAItem(
            question=f"Why did {child.label} start to worry about {clue.label}?",
            answer=f"{clue.label.capitalize()} was missing from the starter table, so {child.label} wondered what had happened to it. That made {child.label} think like a detective instead of just a player.",
        ),
        QAItem(
            question=f"What did {child.label} think the strange clue might mean?",
            answer=f"{child.label} first wondered if it was a thief or just an accident. The private thought kept the story tense until the truth arrived.",
        ),
        QAItem(
            question=f"What was the real reason {clue.label} disappeared?",
            answer=f"{clue.label.capitalize()} slid into the cart pocket when the cart bumped the rail. It was an accident, not a theft.",
        ),
        QAItem(
            question=f"How did the story change at the end?",
            answer=f"The worry turned into relief, and the mystery turned into an ordinary game again. By the last hole, the clue was back on the table and the children were playing safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is golf?",
            answer="Golf is a game where players try to move a ball into a hole with as few hits as possible. It is often played on a course with grass and small targets.",
        ),
        QAItem(
            question="What does it mean to worry?",
            answer="To worry means to feel uneasy about something and keep thinking about what might go wrong. A worried person may look carefully for answers.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps solve a mystery. Clues can be objects, tracks, sounds, or anything that points to the truth.",
        ),
        QAItem(
            question="Why should children not touch a golf cart without help?",
            answer="A golf cart can move fast or bump things, so children should stay safe and let grown-ups handle it. Being careful keeps everyone from getting hurt.",
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means something changes into a new state. In this story, worry changes into relief and a strange clue becomes a simple accident.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
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
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id}: {ent.type} {ent.label} {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, u) for p in PLACES for c in CLUES for u in CULPRITS]


def explain_rejection(place: str, clue: str, culprit: str) -> str:
    return f"(No story: {place}, {clue}, and {culprit} do not make a meaningful mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit at a golf course.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--adult")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.culprit is None or c[2] == args.culprit)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, culprit = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    adult_gender = rng.choice(["woman", "man"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    adult_name = args.adult or rng.choice(["Auntie", "Uncle", "Mama", "Papa"])
    if helper_name == child_name:
        helper_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    return StoryParams(
        place=place, clue=clue, culprit=culprit,
        child_name=child_name, child_gender=child_gender,
        helper_name=helper_name, helper_gender=helper_gender,
        adult_name=adult_name, adult_gender=adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.culprit not in CULPRITS:
        raise StoryError("Invalid params for this storyworld.")
    world = tell_world(params)
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


ASP_RULES = r"""
combo(P,C,U) :- place(P), clue(C), culprit(U).
resolved :- clue_found.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for u in CULPRITS:
        lines.append(asp.fact("culprit", u))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP combo set differs from Python.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"MISMATCH: smoke test failed: {exc}")
    if ok:
        print("OK: ASP parity and smoke test passed.")
        return 0
    return 1


CURATED = [
    StoryParams(
        place="mini_golf", clue="scorecard", culprit="wind",
        child_name="Maya", child_gender="girl",
        helper_name="Jo", helper_gender="boy",
        adult_name="Auntie", adult_gender="woman",
    ),
    StoryParams(
        place="clubhouse", clue="ball_marker", culprit="cart_bump",
        child_name="Ruby", child_gender="girl",
        helper_name="Ben", helper_gender="boy",
        adult_name="Uncle", adult_gender="man",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
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
            header = f"### {p.child_name}: {p.place} / {p.clue} / {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
