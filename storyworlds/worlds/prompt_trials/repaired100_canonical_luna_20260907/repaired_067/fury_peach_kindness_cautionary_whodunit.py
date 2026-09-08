#!/usr/bin/env python3
"""
A small child-facing cautionary whodunit about fury, a missing peach, and
kindness that solves the mystery without blaming the wrong friend.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
calm_clue(X) :- detective(X), notices_peach_mark(X).
kind_inquiry(X) :- detective(X), asks_gently(X).
safe_mystery(X) :- calm_clue(X), kind_inquiry(X), avoids_blame(X).
truth_found(X) :- safe_mystery(X), shares_peach(X).
"""


NAMES = ["Luna", "Milo", "Nia", "Pip", "Tara", "Owen", "Suki", "Ben"]
FRIENDS = ["Mara", "Theo", "Ivy", "Jun", "Rafi", "Cleo", "Wren", "Sol"]
PLACES = ["the school garden", "the village kitchen", "the sunny orchard", "the little market"]
PEACHES = ["a golden peach", "a fuzzy peach", "a ripe peach", "a blushing peach"]


@dataclass(frozen=True)
class Case:
    title: str
    opening: str
    missing: str
    suspicion: str
    clue: str
    method: str
    culprit: str
    truth: str
    repair: str
    lesson: str
    ending: str


CASES = [
    Case(
        title="The Peach on the Empty Plate",
        opening="At snack time, the largest peach vanished from a plate beside the window.",
        missing="the golden peach set aside for everyone to share",
        suspicion="Mara, who had been standing near the table",
        clue="a small peach-colored smear curved from the plate toward the garden door",
        method="followed the smear, checked the path, and asked each friend what they had noticed",
        culprit="a hungry squirrel had carried the peach under the bean vines",
        truth="Mara had only moved the plate away from a dripping flowerpot and had not taken the fruit",
        repair="They brought the peach back, washed it, and cut it into equal pieces for the whole group",
        lesson="Fury may point at a person, but careful clues and kind questions point toward the truth",
        ending="The empty plate became a circle of peach slices, and the squirrel watched from a safe branch.",
    ),
    Case(
        title="The Peach Pit in the Pocket",
        opening="A peach pit appeared in the pocket of the blue apron after the kitchen's fruit bowl went missing.",
        missing="one ripe peach meant for the afternoon cobbler",
        suspicion="Theo, because the blue apron was hanging beside his chair",
        clue="sticky juice dotted the floor from the fruit bowl to the washing basin",
        method="examined the dots, compared footprints, and asked Theo what he had carried",
        culprit="the cook's puppy had nudged the bowl while chasing a wooden spoon",
        truth="Theo had picked up the broken bowl and placed it by the basin before anyone saw the spill",
        repair="They thanked Theo, cleaned the floor together, and saved the unbruised fruit for the cobbler",
        lesson="A suspicious object is not the same as proof, especially when kindness can uncover another explanation",
        ending="The cobbler bubbled while the puppy slept beside a clean, safely latched bowl.",
    ),
    Case(
        title="The Orchard Whodunit",
        opening="Only one peach remained on the orchard tree, though three had been counted at breakfast.",
        missing="two ripe peaches from the low branch",
        suspicion="Ivy, whose basket had a fresh leaf tucked inside it",
        clue="the leaf had a clean bite mark, while the basket held no peach juice at all",
        method="looked beneath the tree, searched for fallen fruit, and spoke to Ivy without accusing her",
        culprit="a flock of birds had pecked the peaches and carried pieces to the fence",
        truth="Ivy had gathered fallen leaves for a nest-making project",
        repair="The children left a little fruit for the birds and divided the last peach carefully",
        lesson="Kindness keeps a mystery from turning into a quarrel when the evidence is incomplete",
        ending="The last peach glowed in four small hands while birds chirped over the orchard fence.",
    ),
    Case(
        title="The Peach Jam Mystery",
        opening="The jam jar was empty before breakfast, and a red spoon lay beside the pantry door.",
        missing="the peach jam prepared for warm morning bread",
        suspicion="Jun, who loved sweet toast and had arrived first",
        clue="the red spoon was dry, but a line of jam led beneath the pantry shelf",
        method="waited for anger to cool, measured the clue, and gently asked Jun about the early footsteps",
        culprit="a loose shelf had tipped the jar into a waiting basket below",
        truth="Jun had come early to set out cups and had not touched the jam",
        repair="They found the jar in the basket, wiped the shelf, and spread the rescued jam together",
        lesson="Caution means pausing before fury turns a guess into an unfair accusation",
        ending="Warm bread passed from hand to hand beneath a shelf now held steady by two wooden blocks.",
    ),
    Case(
        title="The Peach Picnic Puzzle",
        opening="At the picnic, a peach disappeared from the blanket while everyone chased a rolling cup.",
        missing="the biggest peach in the picnic basket",
        suspicion="Sol, because he had been closest to the basket",
        clue="two round wheel marks crossed the blanket and ended beside the lemonade cart",
        method="followed the marks, listened to Sol's account, and checked the cart before making a claim",
        culprit="the cart had rolled over the blanket and pushed the peach into its lower basket",
        truth="Sol had grabbed the runaway cup and never touched the peach",
        repair="They retrieved the fruit, rinsed it, and shared it after securing the cart wheel",
        lesson="A calm search can protect a friend's feelings while it protects the picnic too",
        ending="The cart stayed still, and peach juice shone on a row of smiling picnic plates.",
    ),
    Case(
        title="The Library Peach Note",
        opening="A peach-shaped note promised a surprise, but the librarian's peach basket was suddenly light.",
        missing="a peach saved for the library's story hour",
        suspicion="Nia, because her bookmark matched the paper in the note",
        clue="the note's fold held a streak of library paste, not peach juice",
        method="read the note aloud, checked the craft table, and asked Nia to help trace its path",
        culprit="a puppet show prop maker had borrowed the fruit to paint a model moon",
        truth="Nia had made the bookmark and left it beside the note but had not taken the peach",
        repair="They returned the fruit, chose a wooden prop instead, and invited Nia to the show",
        lesson="Kind questions make room for facts that angry guesses would hide",
        ending="The peach rested in its basket while a wooden moon rose behind the puppet curtain.",
    ),
    Case(
        title="The Peach by the Pond",
        opening="A peach rolled away from the pond picnic, and a wet trail made the case look mysterious.",
        missing="a soft peach placed near the picnic cloth",
        suspicion="Ben, whose shoes were muddy beside the water",
        clue="the wet trail was made of duck footprints, not shoe prints",
        method="counted the tracks, watched the reeds, and asked Ben why he had gone near the pond",
        culprit="a duck had pushed the peach downhill with its bill",
        truth="Ben had gone to fetch a fallen cup and had noticed the duck but not the fruit",
        repair="They moved the picnic uphill, recovered the peach, and gave the duck grain instead",
        lesson="Caution checks the shape of a clue before fury chooses a target",
        ending="The duck waddled away from the peach while the picnic settled on dry grass.",
    ),
    Case(
        title="The Peach Box Riddle",
        opening="The market's peach box was open, yet the shopkeeper could not find the count written on her card.",
        missing="one peach and the card that recorded the basket's count",
        suspicion="Rafi, because he had been practicing numbers beside the stall",
        clue="the card's corner was tucked under a scale, and peach fuzz covered the scale pan",
        method="checked the scale, asked Rafi what he had counted, and rebuilt the tally together",
        culprit="the breeze had lifted the card while a customer moved the peach onto the scale",
        truth="Rafi had been counting pebbles for a math game and had not taken the fruit",
        repair="They found the card, corrected the count, and gave Rafi a peach for helping",
        lesson="A fair mystery compares evidence instead of letting fury make the loudest decision",
        ending="The market card lay flat beneath a smooth stone, and the peach box balanced at last.",
    ),
]


@dataclass
class Character:
    id: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    detective: str
    friend: str
    place: str
    peach: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    detective: Character
    friend: Character
    peach: str
    case: Case
    route: int = 0
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A kindness-first cautionary peach whodunit.")
    parser.add_argument("--detective", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--peach", choices=PEACHES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        detective=args.detective or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        place=args.place or rng.choice(PLACES),
        peach=args.peach or rng.choice(PEACHES),
    )


def make_world(params: StoryParams) -> World:
    raw = "|".join([params.detective, params.friend, params.place, params.peach])
    key = params.seed
    if key is None:
        key = int.from_bytes(hashlib.sha256(raw.encode("utf-8")).digest()[:8], "big")
    detective = Character(
        id=params.detective,
        role="detective",
        meters={"caution": 1.0, "fury": 0.2},
        memes={"kindness": 1.0, "curiosity": 1.0},
    )
    friend = Character(
        id=params.friend,
        role="friend",
        meters={"calm": 0.8},
        memes={"trust": 1.0},
    )
    return World(
        setting=Setting(params.place),
        detective=detective,
        friend=friend,
        peach=params.peach,
        case=CASES[key % len(CASES)],
        route=(key // len(CASES)) % 4,
    )


def tell(world: World) -> None:
    d, f, case = world.detective, world.friend, world.case
    openings = [
        f"In {world.setting.place}, {case.opening}",
        f"The mystery began in {world.setting.place}. {case.opening}",
        f"Everyone in {world.setting.place} noticed the trouble: {case.opening}",
        f"On a bright day at {world.setting.place}, {case.opening}",
    ]
    world.say(openings[world.route])
    world.say(
        f"The missing treat was {world.peach}, and a hot wave of fury made some people point at {case.suspicion}. "
        f"{d.id} felt that anger too, but held it like a warm stone instead of throwing it."
    )
    world.para()
    world.say(
        f'"I want to know what happened, not just who looks suspicious," said {d.id}. '
        f'"Then let us look carefully," replied {f.id}.'
    )
    world.say(
        f"{d.id} noticed the first useful clue: {case.clue}. "
        f"Rather than accusing {f.id}, {d.id} asked, \"What did you see, and what did you do?\""
    )
    world.say(
        f"{f.id} answered, \"I can tell you exactly what I remember.\" "
        f"The gentle question helped everyone share details without hiding or shouting."
    )
    world.para()
    world.say(
        f"Together, {d.id} and {f.id} {case.method}. "
        f"At last they discovered that {case.culprit}."
    )
    world.say(
        f"The truth was kinder than the first guess: {case.truth}. "
        f"Everyone apologized for the suspicion, and {case.repair}."
    )
    world.para()
    world.say(
        f"{d.id} smiled and said, \"The clue solved the mystery, but kindness kept it from becoming a quarrel.\" "
        f"{f.id} laughed softly. The fury faded because the facts had been heard."
    )
    world.say(
        f"It was a cautionary whodunit about pausing, asking, and caring: {case.lesson}. "
        f"{case.ending}"
    )
    world.facts.update(
        detective=d,
        friend=f,
        setting=world.setting,
        case=case,
        clue=case.clue,
        truth=case.truth,
        repair=case.repair,
        ending=case.ending,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.case
    return [
        f"Write a child-friendly cautionary whodunit at {world.setting.place} about {world.peach}, where {world.detective.id} solves the mystery with kindness instead of fury.",
        f"Tell a mystery in which the clue is {case.clue}, a friend is wrongly suspected, and careful questions reveal that {case.culprit}.",
        f"Write an ending image showing how {case.repair} and why the peach is shared fairly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.case
    d, f = world.detective, world.friend
    return [
        QAItem(
            question=f"What went missing in {case.title}?",
            answer=f"{world.peach} went missing. It was the treat everyone expected to find and share.",
        ),
        QAItem(
            question=f"Why did people begin to suspect someone in the case?",
            answer=f"They suspected {case.suspicion} because that person seemed close to the missing peach, but being nearby was not proof.",
        ),
        QAItem(
            question=f"What clue helped {d.id} solve the mystery?",
            answer=f"The important clue was that {case.clue}. {d.id} studied it instead of letting fury decide the answer.",
        ),
        QAItem(
            question=f"How did {d.id} and {f.id} discover the truth?",
            answer=f"They {case.method}. This careful, kind investigation showed that {case.culprit}.",
        ),
        QAItem(
            question="How did kindness change the outcome?",
            answer=f"Kindness made the friends ask questions without accusing anyone. They learned that {case.truth}, then {case.repair}.",
        ),
        QAItem(
            question="What cautionary lesson does the mystery teach?",
            answer=f"It teaches that {case.lesson}. A calm search is safer and fairer than acting in fury.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it dangerous to accuse someone before checking clues?",
            answer="An early accusation can hurt an innocent person's feelings and hide the real explanation. Checking clues helps everyone respond fairly.",
        ),
        QAItem(
            question="What does kindness look like during a mystery?",
            answer="Kindness means asking gentle questions, listening carefully, and caring about people while looking for the truth.",
        ),
        QAItem(
            question="Why should a peach be shared?",
            answer="Sharing the peach makes sure everyone receives a fair piece and turns the solved mystery into a happy ending.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"detective={world.detective.id} role={world.detective.role} meters={world.detective.meters} memes={world.detective.memes}",
            f"friend={world.friend.id} role={world.friend.role} meters={world.friend.meters} memes={world.friend.memes}",
            f"place={world.setting.place}",
            f"peach={world.peach}",
            f"case={world.case.title}",
            f"clue={world.case.clue}",
            f"culprit={world.case.culprit}",
            f"route={world.route}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("detective", "luna"),
            asp.fact("notices_peach_mark", "luna"),
            asp.fact("asks_gently", "luna"),
            asp.fact("avoids_blame", "luna"),
            asp.fact("shares_peach", "luna"),
        ]
    )


def asp_program(show: str = "#show safe_mystery/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = set(asp.atoms(model, "safe_mystery"))
    expected = {("luna",)}
    if found != expected:
        print(f"MISMATCH: {found} != {expected}")
        return 1
    for params in curated():
        sample = generate(params)
        if not sample.story or "peach" not in sample.story.lower():
            print("MISMATCH: generated story check failed")
            return 1
    print("OK: ASP parity and generated-story checks verified.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Mara", "the school garden", "a golden peach"),
        StoryParams("Milo", "Theo", "the village kitchen", "a fuzzy peach"),
        StoryParams("Nia", "Ivy", "the sunny orchard", "a ripe peach"),
        StoryParams("Pip", "Jun", "the little market", "a blushing peach"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "#show calm_clue/1.\n"
                "#show kind_inquiry/1.\n"
                "#show safe_mystery/1.\n"
                "#show truth_found/1."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
