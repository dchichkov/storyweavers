#!/usr/bin/env python3
"""
A tiny pirate tale world about a historic shutter, friendship, and problem solving.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[3]
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
    shutter_state: str = "closed"
    problem_solved: bool = False
    friendship_boost: float = 0.0
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


NAMES = ["Mira", "Joss", "Tessa", "Pere", "Nina", "Bram", "Lio", "Sable"]
PLACES = [
    "the old harbor",
    "the lighthouse room",
    "the captain's dock",
    "the museum cove",
    "the windy attic",
]

INCIDENTS = [
    {
        "title": "the stuck historic shutter",
        "setup": "a salt-stiff shutter on an old lookout house would not open",
        "mistake": "the first guess was that the shutter only needed a hard shove",
        "danger": "a hard shove could crack the old wood and leave the room dark and damp",
        "clue": "a tiny bead of rust showed the hinge needed cleaning, not force",
        "first_try": "pulled at the shutter with all their might",
        "dialogue": "\"Let's not break the old thing,\" said {friend}. \"Let's check the hinge first.\"",
        "fix": "cleaned the hinge, oiled the pin, and opened the shutter gently with a rope loop",
        "ending": "the shutter swung wide and let a clean stripe of sea light spill across the map",
    },
    {
        "title": "the map-light puzzle",
        "setup": "a narrow shutter cast the wrong shadow across a treasure map",
        "mistake": "the shadow looked like a secret X that pointed to the floorboards",
        "danger": "chasing a false mark could waste time and disturb the old room",
        "clue": "when the shutter was half closed, the X moved with the light instead of staying put",
        "first_try": "started prying up the boards near the shadow",
        "dialogue": "\"Wait,\" said {friend}. \"If the X moves, it's only light talking.\"",
        "fix": "slid the shutter open a little at a time until the real mark on the map appeared",
        "ending": "the true X glowed red on the parchment while the floor stayed whole",
    },
    {
        "title": "the rain-spray warning",
        "setup": "rain blew through a cracked shutter and splashed an old captain's chart",
        "mistake": "the wet paper was blamed on a leaking chest nearby",
        "danger": "if the chart stayed in the spray, its ink could blur forever",
        "clue": "drops fell in a straight line from the shutter slats, not from the chest",
        "first_try": "moved the chest before looking up",
        "dialogue": "\"The wind is the trouble,\" said {friend}. \"The shutter is the gate.\"",
        "fix": "closed the shutter, dried the chart, and tied a cloth over the crack",
        "ending": "the chart dried flat beneath a safe cloth while rain tapped outside",
    },
    {
        "title": "the creaking gallery door",
        "setup": "a museum shutter kept banging beside a pirate gallery",
        "mistake": "the banging sounded like a hidden ghost ship calling for help",
        "danger": "the noise might startle visitors and rattle the glass boats",
        "clue": "the banging stopped whenever someone held the latch still",
        "first_try": "ran to warn the whole room about a ghost",
        "dialogue": "\"No ghost yet,\" said {friend}. \"Show me what moves.\"",
        "fix": "tightened the latch, added felt padding, and tested the shutter with care",
        "ending": "the gallery grew quiet, and the model ship rocked only in a tiny glass sea",
    },
    {
        "title": "the tide-locked window",
        "setup": "a low window with a historic shutter was stuck fast after high tide",
        "mistake": "the first thought was that the sea had cursed the hinge",
        "danger": "the room needed fresh air before the paint and ropes grew musty",
        "clue": "sand packed under the lower rail, holding the shutter in place",
        "first_try": "jiggled the top corner and blamed the tide",
        "dialogue": "\"It isn't cursed,\" said {friend}. \"It's just sand being stubborn.\"",
        "fix": "brushed out the sand, lifted from below, and opened the window slowly",
        "ending": "the room breathed again, and the salty air felt new",
    },
    {
        "title": "the lantern-shadow confusion",
        "setup": "a lantern made the shutter bars look like prison stripes on the wall",
        "mistake": "the stripes were mistaken for a sign that someone was trapped inside",
        "danger": "a panic rush could upset the crew and waste precious lantern oil",
        "clue": "the stripes disappeared when the lantern moved, but the room stayed empty",
        "first_try": "called for help before checking the light",
        "dialogue": "\"Look at the lamp, not the wall,\" said {friend}. \"The wall is only borrowing shapes.\"",
        "fix": "moved the lantern aside and opened the shutter to prove the room was clear",
        "ending": "the wall lost its stripes and the crew shared a relieved laugh",
    },
    {
        "title": "the old brass key mix-up",
        "setup": "a brass key lay beside a shutter latch in a dusty chest",
        "mistake": "the key was assumed to be the only tool that could free the shutter",
        "danger": "forcing the wrong tool could bend the latch and damage the old wood",
        "clue": "the latch had a tiny slide bolt that matched a slot on the frame",
        "first_try": "jammed the key into the latch",
        "dialogue": "\"That key opens doors,\" said {friend}. \"This shutter wants a slide, not a stab.\"",
        "fix": "used the slide bolt, then lifted the latch with a gentle turn",
        "ending": "the shutter opened cleanly and the key stayed safe in the chest",
    },
    {
        "title": "the sea-salt jam",
        "setup": "salt crystals crusted the shutter track after a stormy night",
        "mistake": "the stiff track was blamed on rotten wood",
        "danger": "a rotten guess could lead to needless repairs and more damage from force",
        "clue": "the white crust sparkled and crumbled like salt, not splinters",
        "first_try": "tested the track with a rough yank",
        "dialogue": "\"Easy,\" said {friend}. \"Scrape the salt before you blame the wood.\"",
        "fix": "scraped the track clean, wiped it dry, and tested the shutter with a small push",
        "ending": "the clean track slid smooth as the sea breeze",
    },
    {
        "title": "the hidden gull nest",
        "setup": "a shutter was shut tight over a quiet attic nook",
        "mistake": "the tapping inside was thought to be a thief in the walls",
        "danger": "a frightened rush could scare a nesting gull and break the eggs",
        "clue": "soft feathers and tiny shells showed the noise came from a nest",
        "first_try": "raised a broom to guard the door",
        "dialogue": "\"Hold on,\" said {friend}. \"A nest is not a thief.\"",
        "fix": "backed away, opened the shutter a little for air, and left the nest undisturbed",
        "ending": "the gull settled deeper, and the attic stayed peaceful",
    },
    {
        "title": "the mirror-glint message",
        "setup": "sunlight bounced off a shutter and flashed across the water",
        "mistake": "the flash was taken as a distress signal from another ship",
        "danger": "sailing out on a guess could send the crew the wrong way",
        "clue": "the flash repeated whenever the shutter moved, like a mirror in the wind",
        "first_try": "waved a flag toward the bright spot",
        "dialogue": "\"Signals repeat on purpose,\" said {friend}. \"Let's see if the light repeats too.\"",
        "fix": "watched the angle, calmed the deck, and found the flash came from the shutter itself",
        "ending": "the sea quieted, and the bright little flash became only afternoon sun",
    },
]

OPENINGS = [
    "On a bright morning by the sea,",
    "Late in the day at the old harbor,",
    "As gulls circled over the docks,",
    "During a blustery watch on the shore,",
    "Before the tide turned,",
    "While the crew was tending small chores,",
]

REACTIONS = [
    "{friend} frowned, then spoke softly. \"Let's solve it together instead of guessing.\"",
    "For a moment {friend} looked worried. Then they said, \"Show me the clue near the shutter.\"",
    "{friend} tapped the wood twice and whispered, \"We can be careful and still be brave.\"",
    "Instead of arguing, {friend} asked, \"What changes when the light or wind moves?\"",
    "{friend} took a slow breath. \"A good pirate checks first,\" they said.",
]

LESSONS = [
    "Friendship helped them pause, listen, and solve the trouble without breaking the old shutter.",
    "The crew learned that careful eyes can save old things better than strong hands.",
    "Problem solving turned a scary mistake into a gentle repair.",
    "The best answer came from looking at the hinge, the light, and the wind one at a time.",
    "Working together made the harbor feel safer and kinder.",
    "A small clue was enough when two friends stayed calm and curious.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a historic shutter.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([n for n in NAMES if n != name])
    return StoryParams(name=name, friend_name=friend, place=place)


def _reasonableness_gate(params: StoryParams) -> None:
    if params.name == params.friend_name:
        raise StoryError("The hero and friend need different names for a friendship story.")
    if params.place not in PLACES:
        raise StoryError("That place does not fit this pirate world.")
    if "historic" not in "historic shutter":
        raise StoryError("The seed theme must keep the historic shutter at the center.")


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    incident = rng.choice(INCIDENTS)
    opening = rng.choice(OPENINGS)
    reaction = rng.choice(REACTIONS).format(friend=params.friend_name)
    lesson = rng.choice(LESSONS)
    coda = rng.choice([
        "After that, the shutter stayed safe, and the friends kept their tools in order.",
        "From then on, they checked every hinge before the wind could surprise them again.",
        "The old room felt proud of its quiet repair, and so did the friends.",
        "They left a small note by the latch so the next helper would know the right way.",
        "The harbor glowed warmer because friendship had fixed what force might have broken.",
    ])

    hero = Character(name=params.name, kind="pirate", meme={"curious": 1.0, "kind": 1.0}, meter={"courage": 1.0})
    friend = Character(name=params.friend_name, kind="mate", meme={"steady": 1.0, "kind": 1.0}, meter={"courage": 1.0})
    world = World(hero=hero, friend=friend, place=params.place)

    lines = [
        f"{hero.name} and {friend.name} were friends on {params.place}, where a historic shutter guarded an old sea room.",
        f"{opening} {incident['setup']}.",
        f"{hero.name} first thought {incident['mistake']}.",
        f"Without checking much, {hero.name} {incident['first_try']}.",
        incident["dialogue"].format(friend=params.friend_name),
        reaction,
        f"Together they looked closer and found the real clue: {incident['clue']}.",
        f"That meant the danger was not a ghost or a curse, but this: {incident['danger']}.",
        f"So the friends chose a gentler plan and {incident['fix']}.",
        lesson,
        coda,
        f"In the end, {incident['ending']}.",
    ]

    world.shutter_state = "open safely"
    world.problem_solved = True
    world.friendship_boost = 1.0
    world.facts["incident"] = incident["title"]
    world.facts["clue"] = incident["clue"]
    world.facts["risk"] = incident["danger"]
    world.facts["repair"] = incident["fix"]
    world.facts["ending_image"] = incident["ending"]
    world.facts["story"] = " ".join(lines)

    prompts = [
        f"Write a pirate tale about {incident['title']} at {params.place}.",
        f"Tell a friendship story where a historic shutter causes trouble and a clue leads to a safe repair.",
        f"Create a child-friendly problem-solving adventure for {hero.name} and {friend.name} with a shutter, wind, or light.",
    ]

    story_qa = [
        QAItem(
            question=f"What was the problem in {incident['title']}?",
            answer=f"The problem was that {incident['setup']}.",
        ),
        QAItem(
            question=f"What did {params.name} first think was happening?",
            answer=f"{params.name} first thought {incident['mistake']}.",
        ),
        QAItem(
            question=f"What clue helped the friends solve it?",
            answer=f"The clue was that {incident['clue']}.",
        ),
        QAItem(
            question="How did the friends fix the shutter safely?",
            answer=f"They {incident['fix']}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, {incident['ending']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a panel or cover that can open or close a window or opening to control light and air.",
        ),
        QAItem(
            question="What does friendship do in a hard moment?",
            answer="Friendship helps people stay calm, listen to each other, and solve the problem together.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking for clues, testing ideas, and choosing the safest fix.",
        ),
        QAItem(
            question="What makes a story pirate-like?",
            answer="A pirate tale often has the sea, old ships or docks, brave helpers, and a lively adventure tone.",
        ),
        QAItem(
            question="Why treat an old shutter carefully?",
            answer="An old shutter can be fragile, so gentle handling helps keep it from breaking.",
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
        print(f"place={w.place}, shutter_state={w.shutter_state}, problem_solved={w.problem_solved}, friendship_boost={w.friendship_boost}")
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
place_ok(P) :- place(P).
friendship(H,F) :- hero(H), friend(F), H != F.
problem_solved(P) :- place_ok(P), friendship(_, _).

#show place_ok/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(asp.fact("place", place) for place in PLACES)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show place_ok/1."))
    return sorted(set(asp.atoms(model, "place_ok")))


def asp_verify() -> int:
    py = set((p,) for p in PLACES)
    cl = set(asp_valid_places())
    if py == cl:
        print(f"OK: clingo gate matches PLACES ({len(py)} places).")
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
    return [resolve_params(args, random.Random(base + i)) for i in range(args.n)]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show place_ok/1."))
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
