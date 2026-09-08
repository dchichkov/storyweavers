#!/usr/bin/env python3
"""
A tiny comedy storyworld about Sup, a helpful lunch cart with a suspicious squeak.
Foreshadowing points toward a conflict, and a kind repair turns the trouble into a joke.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    helper: str
    snack: str
    location: str
    omen: str
    conflict: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Omen:
    key: str
    text: str
    clue: str


@dataclass(frozen=True)
class ConflictPath:
    key: str
    trouble: str
    cause: str
    fix: str


NAMES = ["Luna", "Milo", "Pia", "Toby", "Nia", "Sam"]
HELPERS = ["Grandma", "Ari", "the janitor", "Coach Kim"]
SNACKS = ["banana muffins", "cheese rolls", "apple slices", "tiny pancakes"]
LOCATIONS = ["the school courtyard", "the library steps", "the rainy bus stop", "the community garden"]
ENDINGS = ["parade", "picnic", "bell", "photo"]

OMENS = [
    Omen("squeak", "Sup gave one squeak before breakfast and another beside the door.", "the loose wheel"),
    Omen("wobble", "Sup's top shelf wobbled whenever anyone said the word 'snack.'", "the bent shelf pin"),
    Omen("rattle", "A spoon inside Sup rattled even though nobody had put a spoon there.", "the hidden spoon"),
    Omen("bell", "Sup's little service bell rang by itself three times.", "the stuck bell spring"),
]

CONFLICTS = [
    ConflictPath(
        "runaway",
        "Sup rolled downhill with the snack basket still aboard.",
        "one wheel had caught on a pebble and then bounced free",
        "Luna placed a book under the wheel, removed the pebble, and guided Sup with both hands",
    ),
    ConflictPath(
        "spill",
        "The snack shelf tipped, sending apple slices sliding like tiny green sleds.",
        "the bent shelf pin had finally slipped out",
        "Luna asked for a cloth, steadied the shelf, and replaced the pin before serving anything else",
    ),
    ConflictPath(
        "bell",
        "Sup's bell began ringing so loudly that three pigeons marched in a circle.",
        "the bell spring was stuck under a crumb",
        "Luna lifted the bell cover, brushed away the crumb, and tested it with one polite ding",
    ),
    ConflictPath(
        "rattle",
        "A spoon shot from Sup's drawer and landed in the principal's hat.",
        "the hidden spoon had been pushed loose by a hard turn",
        "Luna stopped the cart, found the spoon, and gave the hat back with a bow",
    ),
]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def pick(items, key):
    return next(item for item in items if item.key == key)


def complete(params: StoryParams) -> None:
    if params.name not in NAMES:
        raise StoryError(f"unknown child name: {params.name}")
    if params.helper not in HELPERS:
        raise StoryError(f"unknown helper: {params.helper}")
    if params.snack not in SNACKS:
        raise StoryError(f"unknown snack: {params.snack}")
    if params.location not in LOCATIONS:
        raise StoryError(f"unknown location: {params.location}")
    if params.omen not in [x.key for x in OMENS]:
        raise StoryError(f"unknown omen: {params.omen}")
    if params.conflict not in [x.key for x in CONFLICTS]:
        raise StoryError(f"unknown conflict: {params.conflict}")
    if params.ending not in ENDINGS:
        raise StoryError(f"unknown ending: {params.ending}")


def build_world(params: StoryParams) -> World:
    complete(params)
    omen = pick(OMENS, params.omen)
    conflict = pick(CONFLICTS, params.conflict)
    w = World()
    w.add(Entity("child", "character", params.name,
                 meters={"worry": 0.0, "courage": 0.0, "joy": 0.0},
                 memes={"curiosity": 1.0, "helpfulness": 1.0}))
    w.add(Entity("sup", "cart", "Sup",
                 meters={"wheel_health": 1.0, "shelf_health": 1.0, "bell_health": 1.0},
                 memes={"reliability": 1.0, "comic_timing": 1.0}))
    w.add(Entity("helper", "character", params.helper,
                 meters={"patience": 1.0}, memes={"care": 1.0}))
    w.facts.update(params=params, omen=omen, conflict=conflict)
    return w


def tell(params: StoryParams) -> World:
    w = build_world(params)
    p = params
    child = w.entities["child"]
    sup = w.entities["sup"]
    helper = w.entities["helper"]
    omen = w.facts["omen"]
    conflict = w.facts["conflict"]

    w.say(
        f"In {p.location}, {p.name} prepared Sup, a little snack cart with a red handle "
        f"and a very serious job: carrying {p.snack} to hungry people."
    )
    w.say(omen.text)
    w.say(f"{p.name} pointed at the cart. “Sup, are you trying to tell me something?”")
    w.say(f"{helper.label} answered, “Maybe. Or maybe Sup has swallowed another pebble.”")
    child.meters["worry"] += 1
    sup.meters["wheel_health"] -= 0.25
    w.para()

    w.say(f"At lunchtime, the foreshadowing came true: {conflict.trouble}")
    w.say(f"{p.name} grabbed the handle, but Sup answered with a loud squeak.")
    w.say(f"{p.name} called, “{helper.label}, I need help!”")
    w.say(f"{helper.label} called back, “First stop the cart. Then we can solve the mystery.”")
    child.meters["worry"] += 1
    child.meters["courage"] += 1
    w.para()

    w.say(f"{p.name} remembered the clue: {omen.clue}. The real cause was that {conflict.cause}.")
    w.say(f"{helper.label} said, “Good noticing. What is your safest next step?”")
    w.say(f"{p.name} replied, “I will stop, look closely, and fix one thing at a time.”")
    w.say(f"{p.name} {conflict.fix}.")
    child.meters["worry"] -= 1
    child.meters["courage"] += 2
    sup.meters["reliability"] = 2.0
    w.para()

    endings = {
        "parade": f"Then Sup led a tiny parade, carrying {p.snack} while everyone marched behind it.",
        "picnic": f"At the picnic, Sup stood still at last, proudly holding {p.snack} beneath a napkin flag.",
        "bell": "Sup gave one small, proper ding, and everyone applauded the quietest bell in town.",
        "photo": f"For the photograph, {p.name} stood beside Sup, while the rescued {p.snack} sat in front like a grand prize.",
    }
    w.say(endings[p.ending])
    w.say("“Sup,” said " + p.name + ", “next time, please use words.”")
    w.say(f"{helper.label} smiled. “It did use words. They were squeak, wobble, and ding.”")
    w.say(f"Sup gave one final squeak, which everyone agreed sounded exactly like laughter.")
    child.meters["joy"] += 2
    sup.memes["comic_timing"] = 2.0
    return w


def story_qa(w: World) -> list[QAItem]:
    p = w.facts["params"]
    omen = w.facts["omen"]
    conflict = w.facts["conflict"]
    return [
        QAItem(
            f"What did {p.name} notice before Sup's conflict at {p.location}?",
            f"{p.name} noticed this foreshadowing: {omen.text}",
        ),
        QAItem(
            f"What conflict happened to Sup while it carried {p.snack}?",
            conflict.trouble,
        ),
        QAItem(
            f"How did {p.name} solve Sup's problem with help from {p.helper}?",
            f"{p.name} remembered {omen.clue}, learned that {conflict.cause}, and {conflict.fix}.",
        ),
        QAItem(
            f"What did Sup do at the end of the {p.ending} ending?",
            "Sup gave one final squeak that sounded like laughter.",
        ),
    ]


def world_qa(w: World) -> list[QAItem]:
    return [
        QAItem("What is foreshadowing?", "Foreshadowing is an early clue that hints at something important later in a story."),
        QAItem("What is a conflict?", "A conflict is a problem or struggle that the characters must face."),
        QAItem("Why should someone stop before fixing a machine?", "Stopping first can make the situation safer and give the person time to find the real cause."),
        QAItem("Why can a mistake become funny?", "A mistake can become funny when nobody is hurt and the characters respond with kindness and imagination."),
    ]


def prompts(w: World) -> list[str]:
    p = w.facts["params"]
    return [
        f"Write a child-friendly comedy about {p.name}, Sup, and a snack-cart conflict at {p.location}.",
        f"Use foreshadowing so an early clue helps {p.name} repair Sup while carrying {p.snack}.",
        f"Include a brief dialogue exchange with {p.helper} and end with Sup making a harmless joke.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {q}" for i, q in enumerate(sample.prompts, 1))
    out.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        out.extend([f"Q: {q.question}", f"A: {q.answer}"])
    out.append("\n== (3) World questions ==")
    for q in sample.world_qa:
        out.extend([f"Q: {q.question}", f"A: {q.answer}"])
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("domain", "sup"),
        asp.fact("feature", "foreshadowing"),
        asp.fact("feature", "conflict"),
        asp.fact("style", "comedy"),
        asp.fact("requires", "repair"),
        asp.fact("requires", "dialogue"),
    ])


ASP_RULES = r"""
compatible :-
    domain(sup),
    feature(foreshadowing),
    feature(conflict),
    style(comedy),
    requires(repair),
    requires(dialogue).
#show compatible/0.
"""


def asp_program(show: str = "#show compatible/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if asp.atoms(model, "compatible"):
        print("OK: ASP and Python recognize the Sup comedy world.")
        for p in CURATED:
            sample = generate(p)
            if not sample.story or "Sup" not in sample.story:
                print("MISMATCH: generated story failed.")
                return 1
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Sup foreshadowing-conflict comedy storyworld.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--omen", choices=[x.key for x in OMENS])
    ap.add_argument("--conflict", choices=[x.key for x in CONFLICTS])
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        snack=args.snack or rng.choice(SNACKS),
        location=args.location or rng.choice(LOCATIONS),
        omen=args.omen or rng.choice(OMENS).key,
        conflict=args.conflict or rng.choice(CONFLICTS).key,
        ending=args.ending or rng.choice(ENDINGS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.label}: meters={e.meters} memes={e.memes}")
    if qa:
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams("Luna", "Grandma", "banana muffins", "the school courtyard", "squeak", "runaway", "parade"),
    StoryParams("Milo", "Ari", "cheese rolls", "the library steps", "wobble", "spill", "picnic"),
    StoryParams("Pia", "the janitor", "tiny pancakes", "the rainy bus stop", "bell", "bell", "bell"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(asp.atoms(asp.one_model(asp_program()), "compatible"))
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(seed + i))
            p.seed = seed + i
            samples.append(generate(p))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
