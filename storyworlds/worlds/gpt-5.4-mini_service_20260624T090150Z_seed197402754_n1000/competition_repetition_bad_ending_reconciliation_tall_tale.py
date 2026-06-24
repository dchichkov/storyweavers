#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/competition_repetition_bad_ending_reconciliation_tall_tale.py
=================================================================================================

A small tall-tale story world about a grand competition, a repeated boast,
a bad ending, and a reconciliation that brings the whole town back to smiling.

The seed tale idea:
---
Two friends in a windy little town keep trying to beat each other in a contest
to haul, stack, or carry something bigger than either of them expected. They
repeat the same challenge over and over, boast bigger and bigger, and finally
one attempt goes badly wrong. Then they calm down, help each other, and turn
the contest into a shared feat instead of a lonely one.
---

This script models that premise as state:
- a competition between two child characters
- a repeated challenge phrase that grows louder each round
- a bad ending where the contest goes too far
- a reconciliation where the rivals become teammates
- tall-tale exaggeration in the narration
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
class Rival:
    name: str
    epithet: str
    strength: int
    pride: int = 0
    tired: int = 0
    hurt: bool = False
    mad: bool = False
    reconciled: bool = False

    def short(self) -> str:
        return f"{self.epithet} {self.name}"


@dataclass
class Contest:
    thing: str
    weight: int
    size: str
    boast: str
    try_verb: str
    repeat_line: str
    bad_ending: str
    reconciliation: str


@dataclass
class Place:
    name: str
    detail: str
    audience: str
    wind: str
    surface: str


@dataclass
class World:
    place: Place
    contest: Contest
    one: Rival
    two: Rival
    rounds: int = 0
    winner: Optional[str] = None
    shared_win: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(
            place=copy.deepcopy(self.place),
            contest=copy.deepcopy(self.contest),
            one=copy.deepcopy(self.one),
            two=copy.deepcopy(self.two),
            rounds=self.rounds,
            winner=self.winner,
            shared_win=self.shared_win,
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )
        return clone


@dataclass
class StoryParams:
    place: str
    contest: str
    seed: Optional[int] = None


PLACES = {
    "fairground": Place(
        name="the fairground",
        detail="The fairground sat so wide that even the shadows had to walk a mile to find the ferris wheel.",
        audience="the whole town",
        wind="a wind that could comb a horse's mane the wrong way",
        surface="dusty boards",
    ),
    "riverbank": Place(
        name="the riverbank",
        detail="The riverbank curled beside the water like a ribbon tied around a giant's wrist.",
        audience="all the fisherfolk",
        wind="a wind that could ruffle a prairie and still have breath left over",
        surface="muddy ground",
    ),
    "barnyard": Place(
        name="the barnyard",
        detail="The barnyard was so open and bright that a rooster's shadow looked like a fence post at noon.",
        audience="the neighbors and their cousins",
        wind="a wind that could nudge a haystack into a dance",
        surface="packed dirt",
    ),
}

CONTESTS = {
    "pumpkin": Contest(
        thing="the biggest pumpkin in three counties",
        weight=900,
        size="wagon-sized",
        boast="I can lug that pumpkin clear across the yard before you blink!",
        try_verb="haul the pumpkin",
        repeat_line="Again! Again! Again!",
        bad_ending="the pumpkin rolled right into the mud with a splat as loud as thunder in a tin bucket",
        reconciliation="they took a breath, laughed at the muddy giant, and decided to roll it together",
    ),
    "watermelon": Contest(
        thing="the biggest watermelon at the market",
        weight=120,
        size="hog-back heavy",
        boast="I can carry that watermelon like it is a pocket apple!",
        try_verb="carry the watermelon",
        repeat_line="One more go! One more go! One more go!",
        bad_ending="the watermelon slipped, cracked open, and painted the ground pink from boot to boot",
        reconciliation="they split the sweet mess with their hands and promised to finish the job together",
    ),
    "haybale": Contest(
        thing="the tallest hay bale stack in the county",
        weight=300,
        size="barn-tall",
        boast="I can stack those hay bales higher than the church steeple!",
        try_verb="stack the hay bales",
        repeat_line="Higher! Higher! Higher!",
        bad_ending="the whole stack leaned like a sleepy giant and toppled into a fluffy golden heap",
        reconciliation="they shook the straw from their sleeves and built a steadier stack side by side",
    ),
    "bell": Contest(
        thing="the old iron dinner bell that hung by the mill",
        weight=200,
        size="elephant-heavy",
        boast="I can ring that bell so hard it will wake the moon!",
        try_verb="ring the bell",
        repeat_line="Now me! Now me! Now me!",
        bad_ending="the bell yanked loose, swung wild, and bonked the post so hard the echo came back wearing boots",
        reconciliation="they set the bell straight, rubbed the bump, and took turns ringing it gently together",
    ),
}

NAMES = ["Mabel", "June", "Nell", "Eli", "Cal", "Ruth", "Otis", "Bea", "Ivy", "Hank"]
EPITHETS = ["spry", "peppy", "bold", "swift", "loud", "steady", "sturdy", "bright"]
TRAITS = ["stubborn", "spirited", "competitive", "cheery", "rowdy"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, contest) for place in PLACES for contest in CONTESTS]


def reasonableness_gate(place: str, contest: str) -> None:
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    if contest not in CONTESTS:
        raise StoryError(f"Unknown contest: {contest}")


def _attempt(world: World, actor: Rival) -> None:
    c = world.contest
    actor.pride += 1
    actor.tired += 1
    world.rounds += 1
    if world.rounds == 1:
        world.say(f"{actor.name} stepped up and cried, \"{c.boast}\"")
    else:
        world.say(f"{actor.name} shouted, \"{c.repeat_line}\"")
    world.say(
        f"{actor.short()} tried to {c.try_verb}, and {world.place.wind.lower()} seemed to cheer for the trick."
    )


def _compete_score(actor: Rival, contest: Contest) -> int:
    return actor.strength * 10 + actor.pride * 3 - actor.tired * 2


def _bad_ending(world: World, loser: Rival) -> None:
    c = world.contest
    loser.hurt = True
    loser.mad = True
    world.say(f"Then came the bad ending: {c.bad_ending}.")
    world.say(
        f"{loser.name} sat down with a face like a storm cloud, and for a moment the whole place went quiet."
    )


def _reconcile(world: World) -> None:
    a, b = world.one, world.two
    c = world.contest
    a.mad = b.mad = False
    a.reconciled = b.reconciled = True
    world.shared_win = True
    world.say(
        f"After that, {a.name} rubbed the dust off {b.name}'s sleeve, and {b.name} offered a hand back."
    )
    world.say(
        f"They said, \"No more silly fighting. Let's do it together.\" Then they {c.reconciliation}."
    )
    world.say(
        f"With both of them pulling, the thing that had seemed as stubborn as a mule with a thunderhead for a hat moved at last."
    )


def tell(world: World) -> World:
    a, b = world.one, world.two
    c = world.contest

    world.say(world.place.detail)
    world.say(
        f"On that day, {world.place.name} was filled with {world.place.audience}, all waiting to see who could best {c.thing}."
    )
    world.say(
        f"{a.name} and {b.name} were as competitive as two roosters arguing over the sunrise."
    )
    world.say(
        f"Each of them wanted to win the contest, and each of them kept saying they could do it quicker, grander, and grander still."
    )

    world.para()
    _attempt(world, a)
    _attempt(world, b)
    _attempt(world, a)

    world.say(
        f"Again and again they tried, and again and again the crowd counted along like a pocket watch with a big brass voice."
    )
    if _compete_score(a, c) == _compete_score(b, c):
        world.say(f"At first it looked like a tie, which only made them brag louder.")

    world.para()
    loser = a if _compete_score(a, c) < _compete_score(b, c) else b
    _bad_ending(world, loser)
    world.winner = (b.name if loser is a else a.name)

    world.para()
    _reconcile(world)
    world.say(
        f"In the end, the contest stopped being about who was best, because the two of them became best at working together."
    )
    world.say(
        f"And that is how the biggest {c.thing} in the whole county ended with two grinning friends instead of one lonely winner."
    )

    world.facts.update(
        place=world.place,
        contest=world.contest,
        one=world.one,
        two=world.two,
        loser=loser,
        winner=world.winner,
    )
    return world


def narrative_intro(place: Place, contest: Contest, one: Rival, two: Rival) -> list[str]:
    return [
        f"Write a tall tale about {one.name} and {two.name} at {place.name} competing to {contest.try_verb}.",
        f"Tell a story with a repeated chant, a bad ending, and a reconciliation, using the phrase \"{contest.repeat_line}\".",
        f"Write a barn-bigger-than-life story where two rivals start out competing over {contest.thing} and end up helping each other.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a, b = world.one, world.two
    c = world.contest
    qa = [
        QAItem(
            question=f"Who were the two competitors in the story?",
            answer=f"The competitors were {a.name} and {b.name}. They kept trying to outdo each other until they learned to work together.",
        ),
        QAItem(
            question=f"What were they trying to win by {c.try_verb} at {world.place.name}?",
            answer=f"They were trying to win a competition over {c.thing}. The prize was so big that it felt like something a giant would set on a table.",
        ),
        QAItem(
            question=f"What repeated words did the rivals keep shouting?",
            answer=f"They kept shouting \"{c.repeat_line}\". The repeating chant made the contest feel bigger and bigger each time.",
        ),
        QAItem(
            question="What went wrong before the ending got better?",
            answer=f"The bad ending happened when {world.facts['loser'].name} lost control and {c.bad_ending}. That made the contest stop feeling fun.",
        ),
        QAItem(
            question="How did the story end after the bad ending?",
            answer=f"It ended with reconciliation. The two rivals stopped arguing, joined hands, and {c.reconciliation}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    c = world.contest
    return [
        QAItem(
            question="What is a competition?",
            answer="A competition is a contest where people try to do something better, faster, stronger, or smarter than someone else.",
        ),
        QAItem(
            question="Why do people sometimes use teamwork after arguing?",
            answer="People use teamwork after arguing because two helpers can often do a hard job more easily than one helper alone.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means two people stop fighting, make peace, and begin acting friendly again.",
        ),
        QAItem(
            question="What is a tall tale?",
            answer="A tall tale is a funny story that makes ordinary things sound enormous, wild, and larger than life.",
        ),
        QAItem(
            question=f"Why might a {c.thing} be hard to move?",
            answer=f"It would be hard to move because it is {c.size} and very heavy, so it would take real effort or teamwork.",
        ),
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
    for r in [world.one, world.two]:
        lines.append(
            f"  {r.name:8} pride={r.pride} tired={r.tired} hurt={r.hurt} mad={r.mad} reconciled={r.reconciled}"
        )
    lines.append(f"  rounds={world.rounds} winner={world.winner} shared_win={world.shared_win}")
    lines.append(f"  place={world.place.name} contest={world.contest.thing}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- place_fact(P).
contest(C) :- contest_fact(C).

valid_story(P, C) :- place(P), contest(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place_fact", p))
    for c in CONTESTS:
        lines.append(asp.fact("contest_fact", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale competition storyworld with repetition, a bad ending, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--contest", choices=CONTESTS)
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
    if args.place and args.place not in PLACES:
        raise StoryError(f"Unknown place: {args.place}")
    if args.contest and args.contest not in CONTESTS:
        raise StoryError(f"Unknown contest: {args.contest}")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.contest is None or c[1] == args.contest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, contest = rng.choice(sorted(combos))
    return StoryParams(place=place, contest=contest)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    contest = CONTESTS[params.contest]
    names = random.Random(params.seed or 0).sample(NAMES, 2)
    ep = random.Random((params.seed or 0) + 1).sample(EPITHETS, 2)
    r = random.Random((params.seed or 0) + 2)
    one = Rival(name=names[0], epithet=ep[0], strength=r.randint(6, 10))
    two = Rival(name=names[1], epithet=ep[1], strength=r.randint(6, 10))
    if one.name == two.name:
        two.name = NAMES[(NAMES.index(two.name) + 1) % len(NAMES)]
    world = tell(World(place=place, contest=contest, one=one, two=two))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=narrative_intro(place, contest, one, two),
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
    StoryParams(place="fairground", contest="pumpkin"),
    StoryParams(place="riverbank", contest="watermelon"),
    StoryParams(place="barnyard", contest="haybale"),
    StoryParams(place="fairground", contest="bell"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, contest) combos:\n")
        for p, c in combos:
            print(f"  {p:10} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.place} / {p.contest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
