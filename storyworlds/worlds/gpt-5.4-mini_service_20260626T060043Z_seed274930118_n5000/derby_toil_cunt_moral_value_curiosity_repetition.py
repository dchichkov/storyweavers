#!/usr/bin/env python3
"""
A small mystery-style storyworld about a town derby, a tiring job, and a clue
that keeps returning until the truth is noticed.

The seed words are treated as part of the world's vocabulary:
- derby: the local event at the center of the mystery
- toil: the tiring work that leaves traces
- cunt: an in-world stray label found on a torn note; it is never used in child-facing prose

The world features:
- Moral Value: a choice between honesty and hiding
- Curiosity: the hero's urge to investigate
- Repetition: a recurring clue that points to the answer
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

PLACEHOLDER = "setting"


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    item: str
    seed: Optional[int] = None


@dataclass
class Thing:
    id: str
    kind: str
    label: str
    phrase: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    hero: Thing
    helper: Thing
    item: Thing
    clue_count: int = 0
    hidden_score: int = 0
    truth_found: bool = False
    story_parts: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.story_parts.append(text)

    def render(self) -> str:
        return " ".join(self.story_parts).strip()


PLACES = {
    "fair": "the county fairgrounds",
    "wharf": "the old wharf",
    "station": "the train station",
}

HEROES = ["Mina", "Toby", "Nell", "Jasper", "Lena", "Iris"]
HELPERS = ["Mr. Vale", "Aunt June", "Officer Pike", "Mrs. Bell"]
ITEMS = {
    "badge": "a brass derby badge",
    "ledger": "a rain-spotted ledger",
    "ribbon": "a blue ribbon from the derby",
    "ticket": "a torn ticket stub",
}


def _clean_word(word: str) -> str:
    return re.sub(r"[^A-Za-z0-9_ -]+", "", word).strip()


def reasonableness_gate(params: StoryParams) -> None:
    if not params.place or params.place not in PLACES:
        raise StoryError("Choose a real place for the mystery.")
    if not params.hero or not params.helper or not params.item:
        raise StoryError("Missing one of the story roles.")
    if params.hero == params.helper:
        raise StoryError("The hero and helper must be different people.")


ASP_RULES = r"""
% Mystery twin:
% A clue repeats when the same trace appears more than once.
repeated_clue(C) :- clue(C), clue(C).
% Curiosity rises when repeated clues appear.
curious(hero) :- repeated_clue(C), clue(C).
% A moral turn happens when the hero chooses truth over hiding.
moral_turn(hero) :- truth, not hide.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("named_place", pid, place))
    lines.append(asp.fact("theme", "moral_value"))
    lines.append(asp.fact("theme", "curiosity"))
    lines.append(asp.fact("theme", "repetition"))
    lines.append(asp.fact("seedword", "derby"))
    lines.append(asp.fact("seedword", "toil"))
    lines.append(asp.fact("seedword", "cunt"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> int:
    import asp
    model = asp.one_model(asp_program("#show theme/1."))
    themes = set(asp.atoms(model, "theme"))
    expected = {("moral_value",), ("curiosity",), ("repetition",)}
    if themes == expected:
        print("OK: ASP twin sees all three themes.")
        return 0
    print("MISMATCH in ASP twin.")
    print("got:", sorted(themes))
    print("expected:", sorted(expected))
    return 1


def build_world(params: StoryParams) -> World:
    hero = Thing(id=params.hero, kind="character", label=params.hero, phrase=f"{params.hero}, the curious one")
    helper = Thing(id=params.helper, kind="character", label=params.helper, phrase=params.helper)
    item = Thing(id=params.item, kind="thing", label=params.item, phrase=ITEMS[params.item])
    return World(place=PLACES[params.place], hero=hero, helper=helper, item=item)


def generate_story(world: World) -> None:
    hero, helper, item = world.hero, world.helper, world.item

    world.say(
        f"At {world.place}, the derby had already ended, but something about the evening still felt unfinished."
    )
    world.say(
        f"{hero.label} noticed that {item.phrase} had been left behind near a bench, where the mud looked recently disturbed."
    )
    world.say(
        f"{hero.label} was full of curiosity, so {hero.label.lower()} looked closer instead of walking away."
    )

    # Repetition of clues.
    world.clue_count += 1
    world.say(
        f"Once on the path, then again by the gate, the same dusty mark appeared: a small scrape shaped like a wheel."
    )
    world.clue_count += 1
    world.say(
        f"It showed up a third time by the steps, and each repeat made the mystery feel less like a mistake and more like a message."
    )

    world.say(
        f"{helper.label} arrived with tired shoulders, carrying the look of long toil from a day of careful work."
    )
    world.say(
        f"When {hero.label} asked about the mark, {helper.label} hesitated, as if an answer might cost more than it should."
    )

    world.hidden_score = 1
    world.say(
        f"Under the bench, {hero.label} found a torn note. One ugly word had been scratched out, but the rest made the truth plain."
    )
    world.say(
        f"The note said the derby badge had been hidden to cover a mistake, not to steal anything at all."
    )

    world.truth_found = True
    world.say(
        f"{hero.label} handed the note to {helper.label} and said that honesty would do less harm than a secret."
    )
    world.say(
        f"At last, {helper.label} admitted the truth: the badge had been tucked away during the rush of toil, and the repeated wheel marks came from the cart used to move it."
    )
    world.say(
        f"By the end, the badge was returned, the rumor was gone, and {hero.label} walked home with a clear mind, glad that curiosity had led to a moral answer."
    )

    world.facts.update(
        place=world.place,
        hero=hero,
        helper=helper,
        item=item,
        clue_count=world.clue_count,
        truth=world.truth_found,
        moral=world.truth_found,
        repetition=world.clue_count >= 2,
        curiosity=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short mystery story for children about a derby, a repeated clue, and a kind truth.",
        f"Tell a gentle story where {f['hero'].label} notices a clue at {f['place']} and asks careful questions.",
        "Write a simple mystery that begins with a lost derby item, includes repetition, and ends with an honest choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    item = f["item"].label
    place = f["place"]

    return [
        QAItem(
            question=f"What did {hero} find at {place} after the derby?",
            answer=f"{hero} found {ITEMS[item]} near {place}, and that discovery started the mystery.",
        ),
        QAItem(
            question=f"Why did the repeated wheel mark matter in the story?",
            answer="It mattered because it kept appearing again and again, which showed that the clue was important and connected to the hidden badge.",
        ),
        QAItem(
            question=f"What did {hero} choose to do when the truth became clear?",
            answer=f"{hero} chose to speak honestly to {helper} instead of keeping the secret hidden.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to ask questions, look closer, and learn what is going on.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means something happens again and again, like a clue that keeps showing up.",
        ),
        QAItem(
            question="What is moral value in a story?",
            answer="Moral value is the part of a story that points toward a good choice, like honesty, kindness, or fairness.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place: {world.place}")
    lines.append(f"hero: {world.hero.label}")
    lines.append(f"helper: {world.helper.label}")
    lines.append(f"item: {world.item.label}")
    lines.append(f"clue_count: {world.clue_count}")
    lines.append(f"truth_found: {world.truth_found}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld: derby, toil, repetition, and a moral turn.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--item", choices=ITEMS.keys())
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
    place = args.place or rng.choice(list(PLACES.keys()))
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice([h for h in HELPERS if h != hero])
    item = args.item or rng.choice(list(ITEMS.keys()))
    params = StoryParams(place=place, hero=hero, helper=helper, item=item, seed=args.seed)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
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
    StoryParams(place="fair", hero="Mina", helper="Mr. Vale", item="badge"),
    StoryParams(place="wharf", hero="Toby", helper="Officer Pike", item="ledger"),
    StoryParams(place="station", hero="Nell", helper="Mrs. Bell", item="ticket"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show theme/1."))
        return
    if args.verify:
        sys.exit(asp_check())
    if args.asp:
        print(asp_program("#show theme/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} with {p.item}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
