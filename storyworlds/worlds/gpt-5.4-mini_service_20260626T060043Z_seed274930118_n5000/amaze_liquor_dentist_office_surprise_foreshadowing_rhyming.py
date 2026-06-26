#!/usr/bin/env python3
"""
A small rhyming storyworld set in a dentist office.

Premise:
- A child visits a dentist office and expects a scary checkup.
- The office contains a surprising, foreshadowed "liquor" bottle in a locked cabinet.
- That bottle is not for drinking; it is a sealed prop used by the dentist to clean a tiny metal model in a safety demo.
- The child is amazed by the surprise, learns what the office tools do, and leaves feeling braver.

The world uses meters and memes:
- meters track physical states like sparkle, mess, and polish
- memes track feelings like worry, wonder, pride, and trust
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the dentist office"


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    reveal: str
    rhyme_end: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Foreshadow:
    id: str
    clue: str
    payoff: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clues: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.clues = list(self.clues)
        return clone


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def _boost(m: dict[str, float], key: str, amt: float = 1.0) -> None:
    m[key] = m.get(key, 0.0) + amt


def _do_checkup(world: World, child: Entity, dentist: Entity, surprise: Surprise) -> None:
    _boost(child.memes, "worry", -1.0)
    _boost(child.memes, "wonder", 1.0)
    _boost(dentist.meters, "sparkle", 1.0)
    _boost(dentist.memes, "kindness", 1.0)
    world.say(
        f"In the dentist office bright and neat, {child.id} sat still in the checkup seat."
    )
    world.say(
        f"{dentist.id} smiled warm and spoke so sweet, with a voice as light as morning wheat."
    )
    world.say(
        f"Then came a surprise, with a gentle flair: {surprise.phrase} was tucked in there."
    )


def _foreshadow(world: World, child: Entity) -> None:
    world.clues.append("a locked cabinet with a tiny label")
    world.say(
        "Before the big surprise could gleam, a little clue drifted through the dream:"
    )
    world.say(
        "A locked-up cabinet, snug and small, with a label that shimmered on the wall."
    )


def _reveal(world: World, child: Entity, dentist: Entity, surprise: Surprise) -> None:
    _boost(child.memes, "amazed", 2.0)
    _boost(child.memes, "worry", -2.0)
    _boost(child.memes, "pride", 1.0)
    _boost(dentist.meters, "sparkle", 1.0)
    world.say(
        f"{dentist.id} opened the door with a careful sway, and revealed the {surprise.label} in a safe, neat way."
    )
    world.say(
        f"{surprise.reveal} '{surprise.phrase}' meant the same, but the office kept it locked away from the child to tame."
    )
    world.say(
        f"'{surprise.label.capitalize()} can surprise,' {dentist.id} said with a grin, 'but not every bottle is for drinking within.'"
    )


def _demo(world: World, child: Entity, dentist: Entity, surprise: Surprise) -> None:
    helper = world.get("mirror")
    _boost(helper.meters, "polish", 1.0)
    _boost(child.memes, "trust", 1.0)
    world.say(
        f"{dentist.id} used the shiny mirror to show how it spun, and the little metal model began to run."
    )
    world.say(
        f"The {surprise.label} was only a prop in the back-room show; it helped keep the metal nice and slow."
    )
    world.say(
        f"Then {child.id} laughed, for the lesson was clear: safe tools can help, and brave hearts cheer."
    )


def tell(world: World, child_name: str, dentist_name: str, surprise: Surprise) -> World:
    child = world.add(Entity(id=child_name, kind="character", type="boy", meters={"sparkle": 0.0}, memes={"worry": 2.0}))
    dentist = world.add(Entity(id=dentist_name, kind="character", type="adult", meters={"sparkle": 1.0}, memes={"kindness": 2.0}))
    world.add(Entity(id="mirror", type="tool", label="mirror", phrase="a tiny shiny mirror", meters={"polish": 0.0}))
    world.add(Entity(id="chair", type="chair", label="chair", phrase="a blue chair", meters={"clean": 1.0}))

    world.say(
        f"{child.id} went to the dentist office with a slow, small frown, for the chair felt tall and the lights felt down."
    )
    world.say(
        f"Yet {child.id} had heard a rumor that made the whole day bend: a secret little {surprise.label} around the end."
    )
    world.para()

    _foreshadow(world, child)
    world.say(
        f"{child.id} peeked and wondered, with eyes grown wide: 'What could be hiding inside, inside?'"
    )
    world.para()

    _do_checkup(world, child, dentist, surprise)
    _reveal(world, child, dentist, surprise)
    world.para()

    _demo(world, child, dentist, surprise)
    world.say(
        f"So {child.id} left the office, amazed and bright, with a brave little smile and a heart that felt light."
    )

    world.facts.update(child=child, dentist=dentist, surprise=surprise)
    return world


SETTINGS = {"dentist office": Setting(place="the dentist office")}

SURPRISES = {
    "liquor": Surprise(
        id="liquor",
        label="liquor bottle",
        phrase="a sealed liquor bottle",
        reveal="It was not for sipping or for a grown-up spree; it was a safety prop for the office's shiny machinery.",
        rhyme_end="snore",
        tags={"liquor", "surprise", "foreshadowing"},
    ),
    "sparkle_box": Surprise(
        id="sparkle_box",
        label="sparkle box",
        phrase="a tiny sparkle box",
        reveal="It held a harmless polishing sample, bright and neat, for showing how the tools could wash and greet.",
        rhyme_end="light",
        tags={"surprise", "foreshadowing"},
    ),
}

FORESHADOW = Foreshadow(
    id="cabinet",
    clue="locked cabinet",
    payoff="surprise reveal",
)

NAMES = ["Milo", "Nina", "Toby", "Maya", "Ruby", "Leo"]


@dataclass
class StoryParams:
    place: str
    child: str
    dentist: str
    surprise: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming dentist-office storyworld with surprise and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--surprise", choices=SURPRISES.keys())
    ap.add_argument("--child")
    ap.add_argument("--dentist")
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
    place = args.place or "dentist office"
    if place != "dentist office":
        raise StoryError("This storyworld only works in the dentist office.")

    surprise = args.surprise or rng.choice(list(SURPRISES.keys()))
    child = args.child or rng.choice(NAMES)
    dentist = args.dentist or "Dr. Pearl"
    return StoryParams(place=place, child=child, dentist=dentist, surprise=surprise)


def generation_prompts(world: World) -> list[str]:
    s = world.facts["surprise"]
    child = world.facts["child"]
    dentist = world.facts["dentist"]
    return [
        "Write a short rhyming story set in a dentist office with a surprise that was foreshadowed earlier.",
        f"Tell a gentle rhyme where {child.id} meets {dentist.id}, notices a clue, and later feels amazed by a {s.label}.",
        "Write a child-facing story with a safe surprise, a clue in advance, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    dentist = world.facts["dentist"]
    surprise = world.facts["surprise"]
    return [
        QAItem(
            question=f"Why did {child.id} feel nervous at first?",
            answer=f"{child.id} felt nervous because the dentist office was new and the tall chair looked a little scary.",
        ),
        QAItem(
            question=f"What clue foreshadowed the surprise?",
            answer="A locked cabinet with a tiny label foreshadowed that something secret and important would be revealed later.",
        ),
        QAItem(
            question=f"What made {child.id} feel amazed at the end?",
            answer=f"{dentist.id} revealed the {surprise.label}, and the safe little demo turned the mystery into a happy surprise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dentist office for?",
            answer="A dentist office is a place where people go to have their teeth checked, cleaned, and cared for.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small clue early on that hints something will happen later.",
        ),
        QAItem(
            question="What does a surprise do in a story?",
            answer="A surprise can make the story more exciting by revealing something the reader did not expect.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


ASP_RULES = r"""
place(dentist_office).
surprise(liquor).
surprise(sparkle_box).
foreshadow(cabinet).

valid_story(P,S) :- place(P), surprise(S).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("place", "dentist_office"),
        asp.fact("surprise", "liquor"),
        asp.fact("surprise", "sparkle_box"),
        asp.fact("foreshadow", "cabinet"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    got = sorted(set(asp.atoms(model, "valid_story")))
    want = [("dentist_office", "liquor"), ("dentist_office", "sparkle_box")]
    if got == want:
        print(f"OK: ASP matches Python expectations ({len(got)} stories).")
        return 0
    print("Mismatch:", got, "vs", want)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    surprise = SURPRISES[params.surprise]
    tell(world, params.child, params.dentist, surprise)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"clues: {world.clues}")
    return "\n".join(lines)


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
    StoryParams(place="dentist office", child="Milo", dentist="Dr. Pearl", surprise="liquor"),
    StoryParams(place="dentist office", child="Nina", dentist="Dr. Pearl", surprise="sparkle_box"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
