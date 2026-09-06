#!/usr/bin/env python3
"""
A small slice-of-life story world about a guppy, a cashew, a misunderstanding,
and a brave little fix.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    kind: str
    meme: dict[str, float] = field(default_factory=dict)
    meter: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    friend_name: str
    place: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Character
    friend: Character
    place: str
    cashew_state: str = "safe"
    misunderstanding: bool = False
    bravery: bool = False
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Mina", "Pip", "Nori", "Luna", "Tavi", "Roo", "Milo", "Suri"]
PLACES = ["the pond", "the little market", "the fish bowl", "the sunny kitchen", "the dock"]


INCIDENTS = [
    {
        "title": "the mislabeled snack jar",
        "setup": "a curved cashew sat in a jar beside the tin of guppy flakes",
        "mistake": "the faded label made the jar look like fish food",
        "danger": "a cashew is not suitable food for a guppy and could foul the water",
        "clue": "the fish-food tin showed tiny flakes, while the jar listed cashews in bold type",
        "first_try": "reached toward the wrong jar",
        "signal": "swam between the feeding ring and the familiar flake tin",
        "fix": "closed the cashew jar, washed their hands, and measured proper guppy flakes",
        "ending": "one silver flake drifted down while the sealed cashew jar stood on the highest shelf",
    },
    {
        "title": "the fallen lunchbox snack",
        "setup": "a cashew rolled from an open lunchbox toward the edge of the water",
        "mistake": "a round ripple made it seem as though the guppy had knocked the snack loose",
        "danger": "people food must not be tossed to fish, even when a fish looks interested",
        "clue": "a sloping napkin pointed from the lunchbox to the cashew's little trail",
        "first_try": "blamed the guppy and hurried toward the water",
        "signal": "held steady beneath a lily leaf instead of hiding from the sudden shadow",
        "fix": "asked an adult to retrieve the cashew and moved lunch well back from the water",
        "ending": "the lunchbox clicked shut as clear rings widened around the guppy's leaf",
    },
    {
        "title": "the allergy table card",
        "setup": "a card marked CASHEW ALLERGY stood beside a snack tray near the guppy display",
        "mistake": "the card was mistaken for a name tag that could be moved anywhere",
        "danger": "moving an allergy warning could send cashews to someone who must avoid them",
        "clue": "a small shield symbol matched the allergy notice on the classroom wall",
        "first_try": "started carrying the card to an empty chair",
        "signal": "tapped the glass beside the reflected red shield again and again",
        "fix": "put the card back, told the supervising adult, and kept the cashew tray separate",
        "ending": "the red warning card stayed visible while every child received a checked snack",
    },
    {
        "title": "the craft-shell confusion",
        "setup": "a cashew lay among clean wooden shapes for a dry pond-picture collage",
        "mistake": "its curved shape was mistaken for a tiny cave meant for the live guppy",
        "danger": "craft pieces and nuts do not belong in a fish's water",
        "clue": "the project sheet said GLUE TO PAPER and showed the real tank crossed out",
        "first_try": "lifted the cashew toward the bowl",
        "signal": "darted away from the rim, then returned to hover by the paper picture",
        "fix": "kept every craft item on the dry table and used a cardboard crescent instead",
        "ending": "the paper pond gained a golden crescent while the real water stayed spotless",
    },
    {
        "title": "the market scoop mix-up",
        "setup": "two scoops rested between a bin of cashews and a sealed shelf of fish flakes",
        "mistake": "the smaller scoop was assumed to belong to the smaller animal",
        "danger": "shared scoops can spread cashew traces and are not safe for measuring fish food",
        "clue": "colored handles matched colored labels on their proper containers",
        "first_try": "picked up the cashew scoop for the flake tin",
        "signal": "followed the blue handle's reflection along the display glass",
        "fix": "called the shopkeeper, who cleaned the area and returned each labeled scoop",
        "ending": "blue met blue and yellow met yellow beneath two freshly printed signs",
    },
    {
        "title": "the counting-game spill",
        "setup": "cashews used for an adult-led counting game spilled beside the guppy's covered home",
        "mistake": "quick little splashes sounded as if the guppy were begging for the pieces",
        "danger": "cashews are not guppy treats, and loose nuts can also be an allergy risk",
        "clue": "the guppy made the same splashes whenever its feeding-light timer blinked",
        "first_try": "began counting the fallen nuts toward the tank",
        "signal": "waited at the feeding ring and ignored the cashews on the table",
        "fix": "asked an adult to collect the nuts, clean the surface, and serve fish flakes separately",
        "ending": "ten counters sat in a lidded box, and a measured serving of safe flakes vanished at the feeding ring",
    },
    {
        "title": "the missing cashew packet",
        "setup": "a sealed cashew packet disappeared from a picnic basket beside the guppy's water",
        "mistake": "wet marks near the basket made the guppy seem responsible",
        "danger": "the packet needed to stay sealed and away from both wildlife and anyone with allergies",
        "clue": "the marks were round drops from a water bottle, not a fish's impossible footprints",
        "first_try": "searched among the water plants for the packet",
        "signal": "remained calmly near its shelter, showing that the search had frightened it",
        "fix": "looked on dry ground and found the packet tucked under the picnic cloth",
        "ending": "the sealed packet returned to the basket and the water plants slowly stood upright again",
    },
    {
        "title": "the donation-bin question",
        "setup": "a cashew snack and a tin of guppy food waited beside two donation boxes",
        "mistake": "the pictures on the boxes had been turned toward the wall",
        "danger": "the snack required an allergy check, and the guppy food needed to remain sealed",
        "clue": "one receipt named the aquarium club while the other named the community pantry",
        "first_try": "placed both items in the same box",
        "signal": "hovered beside the aquarium club's blue badge on the tank",
        "fix": "read the receipts with an adult and sorted each sealed item into its proper box",
        "ending": "two labels faced forward, with one safe donation resting beneath each",
    },
    {
        "title": "the photograph misunderstanding",
        "setup": "a photograph made a cashew on the table appear to float inside the guppy's bowl",
        "mistake": "the reflection was taken as proof that someone had fed the nut to the fish",
        "danger": "if food truly enters a tank, an adult should check the water instead of guessing",
        "clue": "the cashew vanished from the image when the camera moved sideways",
        "first_try": "announced that the whole bowl needed to be emptied",
        "signal": "kept swimming normally and investigated only its regular feeding corner",
        "fix": "tested the camera angle, confirmed the water was clear, and moved the snack away",
        "ending": "the second photograph showed only the guppy, a green plant, and clean blue water",
    },
    {
        "title": "the recipe-card swap",
        "setup": "a cashew recipe card lay beneath the guppy's weekly care checklist",
        "mistake": "the two cards were read as one strange set of feeding directions",
        "danger": "human recipes must never replace a fish's measured care plan",
        "clue": "one card named an oven, while the other named a feeding ring and water test",
        "first_try": "read the cashew amount beside the guppy's name",
        "signal": "circled the empty feeding ring at the ordinary feeding time",
        "fix": "separated the cards, checked the care plan with an adult, and used proper flakes",
        "ending": "a magnet held the care card above the tank while the recipe returned to the kitchen drawer",
    },
    {
        "title": "the mystery crunch",
        "setup": "a loud crunch sounded just as the guppy disappeared behind a water plant",
        "mistake": "the timing made it seem that the little fish had bitten a cashew",
        "danger": "a guppy should eat appropriately sized fish food, never a hard nut",
        "clue": "a second crunch came from a bench where an adult was eating a cashew snack",
        "first_try": "peered into the water for crumbs",
        "signal": "came out from the plant and calmly chased a harmless bubble",
        "fix": "checked the clear water with an adult and kept the snack on the distant bench",
        "ending": "the last bubble popped silently while the snack bag rustled far from the water",
    },
    {
        "title": "the bravery badge mix-up",
        "setup": "a cashew-shaped bravery badge rested beside a real cashew in a closed snack cup",
        "mistake": "the real nut was picked up as the badge for the guppy's display card",
        "danger": "real nuts should stay contained, labeled, and away from shared displays",
        "clue": "the badge had a pin and painted smile; the cashew had neither",
        "first_try": "carried the wrong curved object toward the display",
        "signal": "swam into the open after a noisy cart passed, earning the badge honestly",
        "fix": "returned the nut to the adult, washed hands, and fastened the painted badge to the card",
        "ending": "the bright badge gleamed outside the glass as the brave guppy crossed the open water",
    },
]

OPENINGS = [
    "The ordinary afternoon changed when",
    "Just after the usual feeding check,",
    "During a quiet errand with no adventure planned,",
    "Between two familiar chores,",
    "On a day that had begun as calmly as any other,",
    "While everyone was attending to small jobs,",
    "Near the end of an otherwise peaceful visit,",
    "As the light shifted across the water,",
]

REACTIONS = [
    "Heat rose in {friend}'s cheeks. \"I think I made that story up too quickly,\" they admitted.",
    "{friend} took one slow breath. \"A guess is not evidence,\" they said.",
    "For a moment {friend} wanted to defend the first idea. Then they asked, \"What can we check?\"",
    "{friend}'s stomach tightened, but they chose a question over an accusation: \"What actually happened?\"",
    "\"Pause, look, and ask,\" {friend} whispered, borrowing the safety rule they had practiced.",
    "{friend} felt embarrassed by the mix-up. Bravery, they decided, meant correcting it aloud.",
    "Instead of rushing, {friend} crouched where the whole scene was visible. \"Show me the clue,\" they said.",
    "{friend} almost hid the mistake. \"No,\" they said softly. \"Being brave means getting help now.\"",
]

LESSONS = [
    "Bravery was not touching something risky; it was pausing, checking, and asking for help.",
    "They learned that a careful question can untangle a misunderstanding before it becomes a bigger problem.",
    "Being wrong was uncomfortable, but admitting it made the next safe step possible.",
    "The small event proved that kindness includes checking food labels and respecting allergy rules.",
    "A guppy's curious movement was only a clue, not permission to feed it people food.",
    "Courage sometimes looked wonderfully ordinary: read, ask, correct, and clean up.",
    "They learned to separate what they observed from the story they first imagined.",
    "The best brave choice protected both the guppy and every person sharing the space.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life guppy/cashew story world.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend-name", choices=NAMES)
    ap.add_argument("--place", choices=PLACES)
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


def valid_places() -> list[str]:
    return list(PLACES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(valid_places())
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in NAMES if n != name])
    return StoryParams(name=name, friend_name=friend, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.friend_name:
        raise StoryError("The hero and friend need different names for the misunderstanding to work.")
    if params.place not in PLACES:
        raise StoryError("That place does not belong in this little world.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)

    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS).format(friend=params.friend_name)
    lesson = rng.choice(LESSONS)
    notice = rng.choice([
        "described what they had actually seen before describing what they had assumed",
        "compared the first guess with every visible clue instead of choosing the most exciting explanation",
        "checked the labels, positions, and order of events without touching anything else",
        "made two short lists headed OBSERVED and IMAGINED",
        "remembered that a guppy could offer behavior to observe but could not explain the mix-up in words",
        "checked the scene from a second angle and found a detail the first hurried glance had missed",
        "retraced the last minute one step at a time with the adult",
        "asked the adult to verify the clue before anyone moved food or changed the water",
    ])
    coda = rng.choice([
        "Afterward, they wrote the safe rule on a card for the next visitor.",
        "They retold the mistake without blame so everyone could learn from it.",
        "Before leaving, they checked that every lid, label, and feeding tool was in its proper place.",
        "The next small chore felt easier because they now knew how to slow a worried thought down.",
        "They gave the guppy its usual quiet space and let the ordinary afternoon become ordinary again.",
        "An adult thanked them for reporting the mix-up before trying to solve it alone.",
        "Together they made one simple rule: people snacks here, fish food there.",
        "They drew a tiny checklist: observe, ask, act safely, then check again.",
    ])

    hero = Character(name=params.name, kind="guppy", meme={"curious": 1.0, "brave": 1.0})
    friend = Character(name=params.friend_name, kind="child", meme={"kind": 1.0})
    world = World(hero=hero, friend=friend, place=params.place)

    lines = [
        f"{hero.name} was a small guppy whose daily loops made {params.place} feel familiar to {friend.name}.",
        f"{opening} {incident['setup']} nearby.",
        f"{friend.name} misunderstood the scene: {incident['mistake']}.",
        f"Without stopping to test that idea, {friend.name} {incident['first_try']}.",
    ]
    world.misunderstanding = True
    world.facts["incident"] = incident["title"]
    world.facts["misunderstanding"] = incident["mistake"]
    world.facts["risk"] = incident["danger"]

    lines.extend([
        f"That was when {hero.name} did something quietly brave: the guppy {incident['signal']}.",
        reaction,
        f"With a nearby adult listening, {friend.name} {notice}.",
        f"The useful clue was simple: {incident['clue']}.",
        f"Now the misunderstanding made sense, and so did the risk: {incident['danger']}.",
        f"To put matters right, {friend.name} {incident['fix']}.",
    ])
    world.bravery = True
    world.cashew_state = "contained and kept away from the water"
    world.facts["bravery"] = incident["signal"]
    world.facts["clue"] = incident["clue"]
    world.facts["repair"] = incident["fix"]
    world.facts["lesson"] = lesson
    world.facts["ending_image"] = incident["ending"]
    lines.extend([lesson, coda, f"By the end, {incident['ending']}."])

    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a gentle slice-of-life story called {incident['title']} about a guppy and a cashew.",
        f"Tell a child-friendly story set at {params.place} where {incident['mistake']}, then a clue corrects the misunderstanding.",
        f"Write about {hero.name}'s quiet bravery and {friend.name}'s safe repair without feeding a cashew to a fish.",
    ]

    story_qa = [
        QAItem(
            question=f"What did {params.friend_name} misunderstand during {incident['title']}?",
            answer=f"{params.friend_name} misunderstood the scene because {incident['mistake']}.",
        ),
        QAItem(
            question=f"What brave thing did {params.name} do when the misunderstanding happened?",
            answer=f"{params.name} bravely {incident['signal']}.",
        ),
        QAItem(
            question=f"Which clue helped {params.friend_name} correct the first guess?",
            answer=f"The decisive clue was that {incident['clue']}.",
        ),
        QAItem(
            question=f"How did {params.friend_name} safely repair the problem?",
            answer=f"{params.friend_name} {incident['fix']}.",
        ),
        QAItem(
            question="Why was it important to keep the cashew separate?",
            answer=f"It was important because {incident['danger']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a guppy?",
            answer="A guppy is a small fish that can swim quickly and lives in water.",
        ),
        QAItem(
            question="What is a cashew?",
            answer=(
                "A cashew is a tree nut eaten by many people. It is not fish food, and people handling or serving it "
                "should follow labels and allergy-safety instructions."
            ),
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means staying calm and doing the right thing even when you feel worried.",
        ),
        QAItem(
            question="What should a guppy eat?",
            answer=(
                "A guppy should receive an appropriately sized, balanced fish food in the amount recommended by its caregiver. "
                "It should not be fed cashews or other people snacks."
            ),
        ),
        QAItem(
            question="What should a child do when a food allergy warning may have been moved?",
            answer=(
                "The child should stop moving or serving the food and tell a responsible adult. "
                "The adult can check labels, prevent cross-contact, and make sure everyone receives a safe snack."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        w = sample.world
        print(f"hero={w.hero.name}, kind={w.hero.kind}, meme={w.hero.meme}, meter={w.hero.meter}")
        print(f"friend={w.friend.name}, kind={w.friend.kind}, meme={w.friend.meme}, meter={w.friend.meter}")
        print(f"place={w.place}, misunderstanding={w.misunderstanding}, bravery={w.bravery}, cashew_state={w.cashew_state}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


ASP_RULES = r"""
misunderstanding(hero,cashew) :- place(P), hero(H), friend(F), H != F.
brave(hero) :- misunderstanding(hero,cashew).

#show valid_place/1.
valid_place(P) :- place(P).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(asp.fact("place", place) for place in PLACES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    py = set((p,) for p in valid_places())
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches valid_places() ({len(py)} places).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generation_samples(args: argparse.Namespace) -> list[StoryParams]:
    if args.all:
        out: list[StoryParams] = []
        for i, place in enumerate(PLACES):
            name = NAMES[i % len(NAMES)]
            friend = NAMES[(i + 1) % len(NAMES)]
            if friend == name:
                friend = NAMES[(i + 2) % len(NAMES)]
            out.append(StoryParams(name=name, friend_name=friend, place=place))
        return out
    base = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base)
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{p[0]}" for p in asp_valid_places()))
        return

    samples: list[StorySample] = []
    for i, params in enumerate(generation_samples(args)):
        params.seed = (args.seed if args.seed is not None else 0) + i
        samples.append(generate(params))

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
