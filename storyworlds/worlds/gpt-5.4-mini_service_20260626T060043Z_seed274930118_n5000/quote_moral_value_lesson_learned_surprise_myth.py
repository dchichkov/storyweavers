#!/usr/bin/env python3
"""
A standalone storyworld for a small myth-like tale with a quote, a surprise,
and a moral value lesson learned.

The domain:
- A young seeker, a guide, a sacred token, and a hidden test.
- The seeker wants a gift or place of honor.
- A surprise reveals a truer need.
- A quote from the guide gives the lesson.
- The ending shows the moral value learned and the changed world state.

This file follows the Storyweavers contract and can run without clingo unless
ASP mode is requested.
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
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "goddess", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "god", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    epithet: str
    feature: str


@dataclass
class Trial:
    id: str
    name: str
    want: str
    surprise: str
    quote: str
    lesson: str
    moral: str
    value: str


@dataclass
class Token:
    id: str
    label: str
    phrase: str
    meaning: str
    value: str


@dataclass
class StoryParams:
    place: str
    trial: str
    token: str
    seeker_name: str
    seeker_type: str
    guide_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


PLACES = {
    "hill": Place("the high hill", "wind-crowned", "a stone altar"),
    "river": Place("the silver river", "moon-bright", "a glassy ford"),
    "grove": Place("the old grove", "leaf-shadowed", "a root-woven circle"),
}

TRIALS = {
    "pride": Trial(
        id="pride",
        name="pride",
        want="claim the first blessing",
        surprise="the blessing is hidden in the hands of the one who shared food",
        quote="A crown grows heavier when it is carried for the self alone.",
        lesson="honor grows best when it is shared",
        moral="Pride shrinks the heart, but humility makes room for wisdom.",
        value="humility",
    ),
    "greed": Trial(
        id="greed",
        name="greed",
        want="keep every shining gift",
        surprise="the brightest gift turns out to be a lantern for the whole village",
        quote="A full fist cannot welcome a blessing.",
        lesson="a gift is meant to be used for others",
        moral="Greed makes a person small, but generosity makes a person large.",
        value="generosity",
    ),
    "fear": Trial(
        id="fear",
        name="fear",
        want="turn away from the dark path",
        surprise="the dark path is only a tunnel to a safe spring",
        quote="The brave step is not the one without fear; it is the one that moves anyway.",
        lesson="courage is walking forward with a trembling heart",
        moral="Fear fades when courage is chosen.",
        value="courage",
    ),
}

TOKENS = {
    "fire_seed": Token("fire_seed", "fire seed", "a warm fire seed", "a promise of new light", "hope"),
    "owl_feather": Token("owl_feather", "owl feather", "a silver owl feather", "quiet wisdom", "wisdom"),
    "river_pearl": Token("river_pearl", "river pearl", "a pale river pearl", "shared abundance", "generosity"),
}

SEEKER_TYPES = ["girl", "boy"]
GUIDE_TYPES = ["elder", "priest", "queen", "king"]
NAMES = ["Ari", "Mira", "Tavi", "Niko", "Lena", "Suri", "Oren", "Kian"]


def aspirational_opening(world: World, seeker: Entity, trial: Trial, token: Token) -> None:
    world.say(
        f"Long ago, {seeker.id} walked to {world.place.name}, where "
        f"{world.place.epithet} stones looked like they had been waiting for a story."
    )
    world.say(
        f"{seeker.id} hoped to {trial.want}, and everyone said {token.phrase} would answer a brave heart."
    )


def build_turn(world: World, seeker: Entity, guide: Entity, trial: Trial, token: Token) -> None:
    seeker.memes["desire"] = seeker.memes.get("desire", 0) + 1
    seeker.memes["restless"] = seeker.memes.get("restless", 0) + 1
    world.para()
    world.say(
        f"At the altar, {seeker.id} reached for {token.phrase}, but the ground gave a soft whisper."
    )
    world.say(
        f"That was the surprise: the token was not waiting to be taken, but to be understood."
    )
    world.say(
        f"{guide.id} smiled and said, \"{trial.quote}\""
    )
    seeker.memes["wonder"] = seeker.memes.get("wonder", 0) + 1
    guide.memes["wisdom"] = guide.memes.get("wisdom", 0) + 1


def resolve(world: World, seeker: Entity, guide: Entity, trial: Trial, token: Token) -> None:
    world.para()
    seeker.memes["humility" if trial.value == "humility" else trial.value] = (
        seeker.memes.get(trial.value, 0) + 1
    )
    seeker.memes["joy"] = seeker.memes.get("joy", 0) + 1
    world.say(
        f"{seeker.id} lowered {seeker.pronoun('possessive')} hands and listened."
    )
    world.say(
        f"Then {seeker.id} used the lesson learned: {trial.lesson}."
    )
    world.say(
        f"When {seeker.id} did that, the token glowed with {token.meaning}, and the people nearby shared the light."
    )
    world.say(
        f"By sunset, the moral value of {trial.value} had changed {seeker.id}, and the whole place felt gentler."
    )


def tell(world: World, seeker: Entity, guide: Entity, trial: Trial, token: Token) -> World:
    world.facts.update(seeker=seeker, guide=guide, trial=trial, token=token)
    aspirational_opening(world, seeker, trial, token)
    build_turn(world, seeker, guide, trial, token)
    resolve(world, seeker, guide, trial, token)
    return world


def story_questions(world: World) -> list[QAItem]:
    f = world.facts
    seeker: Entity = f["seeker"]
    guide: Entity = f["guide"]
    trial: Trial = f["trial"]
    token: Token = f["token"]
    return [
        QAItem(
            question=f"Where did {seeker.id} go in the story?",
            answer=f"{seeker.id} went to {world.place.name}, where the stones and air felt old and sacred.",
        ),
        QAItem(
            question=f"What did {seeker.id} want at first?",
            answer=f"{seeker.id} wanted to {trial.want}. That wish seemed simple at first, but the place had a harder lesson.",
        ),
        QAItem(
            question=f"What surprising thing happened at the altar?",
            answer=f"The surprise was that {token.phrase} was not meant to be grabbed. It was there to teach {seeker.id} something deeper.",
        ),
        QAItem(
            question=f"What quote did {guide.id} say?",
            answer=f"{guide.id} said, \"{trial.quote}\"",
        ),
        QAItem(
            question=f"What lesson was learned?",
            answer=f"The lesson learned was that {trial.lesson}.",
        ),
        QAItem(
            question=f"What moral value changed {seeker.id}?",
            answer=f"The moral value of {trial.value} changed {seeker.id}, and {seeker.id} became wiser and gentler.",
        ),
    ]


def world_questions(world: World) -> list[QAItem]:
    f = world.facts
    trial: Trial = f["trial"]
    token: Token = f["token"]
    return [
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a kind of good choice people try to live by, like honesty, courage, humility, or generosity.",
        ),
        QAItem(
            question="What does a lesson learned mean?",
            answer="A lesson learned is the new understanding a person carries after something changes their mind or heart.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what the character thought would happen.",
        ),
        QAItem(
            question=f"What does {token.label} stand for in this myth?",
            answer=f"It stands for {token.meaning}, which helps the story point toward {trial.value}.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    trial: Trial = f["trial"]
    token: Token = f["token"]
    seeker: Entity = f["seeker"]
    return [
        f'Write a short myth for children that includes the word "quote" and the idea of a surprise at {world.place.name}.',
        f"Tell a child-friendly myth about {seeker.id} who wants to {trial.want} and learns a moral value.",
        f"Write a story with a magical quote, a lesson learned, and {token.phrase} as the hidden sign.",
    ]


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    seeker = world.add(Entity(id=params.seeker_name, kind="character", type=params.seeker_type))
    guide = world.add(Entity(id="Guide", kind="character", type=params.guide_type, label="the guide"))
    trial = TRIALS[params.trial]
    token = TOKENS[params.token]
    tell(world, seeker, guide, trial, token)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for trial in TRIALS:
            for token in TOKENS:
                combos.append((place, trial, token))
    return combos


def explain_invalid() -> str:
    return "(No story: the requested choices do not make a fitting myth.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a small myth with a quote, surprise, and moral lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--name")
    ap.add_argument("--seeker-type", choices=SEEKER_TYPES)
    ap.add_argument("--guide-type", choices=GUIDE_TYPES)
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
    trial = args.trial or rng.choice(list(TRIALS))
    token = args.token or rng.choice(list(TOKENS))
    seeker_type = args.seeker_type or rng.choice(SEEKER_TYPES)
    guide_type = args.guide_type or rng.choice(GUIDE_TYPES)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, trial=trial, token=token, seeker_name=name, seeker_type=seeker_type, guide_type=guide_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_questions(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    parts = ["== Story questions =="]
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
trial(T) :- trial_id(T).
token(K) :- token_id(K).

valid(P,T,K) :- place(P), trial(T), token(K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("setting", p))
    for t in TRIALS:
        lines.append(asp.fact("trial_id", t))
    for k in TOKENS:
        lines.append(asp.fact("token_id", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [
            generate(StoryParams(place=p, trial=t, token=k, seeker_name="Ari", seeker_type="girl", guide_type="elder"))
            for p, t, k in valid_combos()
        ]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
