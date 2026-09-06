#!/usr/bin/env python3
"""
A small story world set at a riverbank, where a child makes a tiny commitment,
takes a gentle quest, and ends transformed by what they learn and do.

The seed idea is slice-of-life: a quiet day near the river becomes meaningful
because someone decides to commit to a helpful task, follows it through, and
changes a little in the process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    place: str = "riverbank"
    child: str = "Mina"
    companion: str = "Grandpa"
    quest: str = "collect the fallen litter"
    transformation: str = "brave"
    commitment: str = "commit to helping the riverbank stay clean"
    seed: Optional[int] = None


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"energy": 1.0, "mess": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"care": 0.0, "confidence": 0.0, "calm": 0.0})

    def pronoun(self) -> str:
        return "they"


@dataclass
class World:
    place: str
    child: Person
    companion: Person
    river_cleanliness: float = 0.4
    river_mood: float = 0.3
    found_items: list[str] = field(default_factory=list)
    committed: bool = False
    quest_started: bool = False
    quest_finished: bool = False
    transformed: bool = False
    incident: str = ""
    obstacle: str = ""
    clue: str = ""
    first_attempt: str = ""
    resolution: str = ""
    lesson: str = ""
    ending_image: str = ""
    lines: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Riverbank slice-of-life story world.")
    ap.add_argument("--place", choices=["riverbank"], default="riverbank")
    ap.add_argument("--child")
    ap.add_argument("--companion")
    ap.add_argument("--quest")
    ap.add_argument("--transformation")
    ap.add_argument("--commitment")
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


NAME_POOL = ["Mina", "Theo", "Iris", "Jun", "Sana", "Ari", "Niko", "Lina"]
COMPANION_POOL = ["Grandpa", "Mom", "Auntie", "Dad", "Neighbor Sam"]
QUEST_POOL = [
    "collect the fallen litter",
    "stack smooth stones into a little wall",
    "bring seeds to plant by the reeds",
    "return a lost kite to the path",
]
TRANS_POOL = ["confident", "kind", "patient", "careful", "thoughtful"]


INCIDENTS = [
    {
        "name": "the ribbon near the turtle",
        "premise": "A young turtle kept backing away from a blue ribbon that fluttered between two reeds.",
        "obstacle": "The ribbon was looped around a low branch, and tugging it could have dropped the branch onto the turtle.",
        "first_attempt": "reached toward the ribbon, then stopped before touching it",
        "clue": "The turtle moved calmly whenever everyone stepped back, showing that space mattered more than speed.",
        "action": "They marked a wide path around the turtle, and the companion used a litter grabber from firm ground to lift the ribbon free.",
        "result": "The turtle crossed into the reeds while the ribbon went safely into their bag.",
        "lesson": "care can mean slowing down and giving a wild animal room",
        "ending": "Only a small V-shaped wake remained beside the clean reeds.",
        "items": ["blue ribbon", "litter grabber"],
    },
    {
        "name": "the washed-away trail marker",
        "premise": "Last night's rain had carried the painted trail marker from the path to a patch of mud.",
        "obstacle": "Two families were already following the wrong bend toward a slippery part of the bank.",
        "first_attempt": "tried to point from a distance, but the wind swallowed the warning",
        "clue": "A square dry mark on the signpost matched the back of the fallen marker.",
        "action": "They asked the park keeper for help, held the safe path open, and watched the marker get fastened to its proper post.",
        "result": "The next walkers turned onto the broad path before reaching the mud.",
        "lesson": "a useful promise includes asking the right grown-up for help",
        "ending": "The restored arrow shone red in a puddle as the last raincloud drifted away.",
        "items": ["trail marker", "square dry mark"],
    },
    {
        "name": "the duck nest detour",
        "premise": "A mother duck had tucked her nest beside the usual cleanup path.",
        "obstacle": "Finishing the quest by the shortest route would have brought noisy footsteps too close to the eggs.",
        "first_attempt": "counted the short path's litter bags, then realized the plan protected tidiness but not the nest",
        "clue": "The duck lowered her head whenever someone approached and relaxed when they used the upper trail.",
        "action": "They moved the work to the upper trail and made a temporary detour sign with the ranger's permission.",
        "result": "The quest continued quietly, and the duck settled over her eggs again.",
        "lesson": "helping a place means noticing the lives already using it",
        "ending": "Four pale eggs rested beneath one quiet wing while footsteps passed far above.",
        "items": ["detour sign", "four duck eggs"],
    },
    {
        "name": "the blurred seed labels",
        "premise": "A box of native seed packets had been left under a leaky picnic roof.",
        "obstacle": "The labels had blurred, so planting at once might put shade-loving seeds in the hot open sand.",
        "first_attempt": "almost guessed by the packet colors, but noticed that two colors held different seed shapes",
        "clue": "A waterproof planting chart showed each seed's shape beside its best patch of ground.",
        "action": "They sorted the seeds on a dry table, checked every shape against the chart, and planted only the confirmed packets.",
        "result": "Each kind of seed reached the soil where it had the best chance to grow.",
        "lesson": "patient checking can turn uncertainty into responsible action",
        "ending": "Tiny labeled sticks stood in neat rows beside the silver-green reeds.",
        "items": ["blurred seed packets", "planting chart"],
    },
    {
        "name": "the kite in the willow",
        "premise": "A lost kite bobbed from a willow branch above the shallow edge.",
        "obstacle": "The string crossed wet stones, and climbing or wading after it would have been unsafe.",
        "first_attempt": "pulled the string from the path, but stopped when the branch bent toward the water",
        "clue": "Each gust lowered the kite close to the long fork of a fallen, dry branch on shore.",
        "action": "The companion steadied the dry branch while the child guided the loose string onto the path without approaching the water.",
        "result": "They rolled the string around a card and placed the undamaged kite at the ranger kiosk.",
        "lesson": "bravery is choosing a safe method instead of a dramatic one",
        "ending": "The kite's yellow tail flickered from the lost-and-found hook like a little flag.",
        "items": ["lost kite", "string card"],
    },
    {
        "name": "the leaf-blocked rain channel",
        "premise": "A narrow rain channel beside the path was overflowing across a bench leg.",
        "obstacle": "A soggy clump hid the grate, and no one could tell whether sharp rubbish was mixed into it.",
        "first_attempt": "started to move the clump with a shoe, then remembered that hidden rubbish should not be kicked",
        "clue": "Water slipped through one corner whenever a long twig floated away from the grate.",
        "action": "They kept visitors clear while the groundskeeper lifted the clump with tools and checked the grate underneath.",
        "result": "Rainwater returned to the channel, and the bench stood on dry ground again.",
        "lesson": "good problem solving includes recognizing which jobs require trained hands",
        "ending": "A clear ribbon of rainwater curled through the grate without touching the bench.",
        "items": ["leaf clump", "rain grate"],
    },
    {
        "name": "the runaway picnic wrappers",
        "premise": "A sudden breeze scattered paper wrappers from an open picnic basket.",
        "obstacle": "Chasing one wrapper at a time only sent the others tumbling closer to the river.",
        "first_attempt": "sprinted after the brightest wrapper, then heard the basket lid flap behind them",
        "clue": "The wrappers stopped whenever they reached the sheltered side of the picnic table.",
        "action": "One helper closed and weighted the basket while the other approached the wrappers from the windy side and guided them toward the shelter.",
        "result": "Every wrapper was counted into the bin before any reached the water.",
        "lesson": "teamwork begins by fixing the cause, not merely chasing each result",
        "ending": "The closed basket sat still beneath a smooth stone, and the river carried only sunlight.",
        "items": ["paper wrappers", "picnic basket"],
    },
    {
        "name": "the stranded minnow pool",
        "premise": "The falling river had left three minnows in a warm puddle behind a ridge of pebbles.",
        "obstacle": "Scooping the fish by hand could hurt them, and moving random stones might muddy their gills.",
        "first_attempt": "knelt to scoop a minnow, then pulled both hands back and called for the ranger",
        "clue": "The ranger found an old side channel where cool water had flowed before the pebble ridge formed.",
        "action": "The child fetched the ranger's marker flags while the ranger reopened a narrow channel with the proper permit and tool.",
        "result": "Cool water trickled in, and the minnows swam back to the river on their own.",
        "lesson": "kindness toward wildlife should be guided by knowledge",
        "ending": "Three quick silver flashes vanished beneath the river's shadow.",
        "items": ["marker flags", "pebble ridge"],
    },
    {
        "name": "the missing nature-box note",
        "premise": "The riverside nature box stood open, with its borrowing notebook missing.",
        "obstacle": "Without the note, a returned magnifier looked stolen even though someone might simply have followed old instructions.",
        "first_attempt": "wanted to blame the last visitor, but chose to inspect the box first",
        "clue": "A clean rectangle under the lid and two paper corners showed where the wind had caught the notebook.",
        "action": "They followed the path of trapped pages, found the notebook beneath a bench, and added an elastic strap to the box with the librarian's help.",
        "result": "The magnifier was checked in properly, and nobody was accused unfairly.",
        "lesson": "evidence deserves attention before blame",
        "ending": "The notebook rested under its green strap, open to a page of careful signatures.",
        "items": ["borrowing notebook", "green strap"],
    },
    {
        "name": "the faded distance dots",
        "premise": "The colored dots marking the accessible riverside loop had faded after a week of sun.",
        "obstacle": "Visitors could no longer tell which path returned gently and which one ended at steep steps.",
        "first_attempt": "set out to repaint the dots, then noticed there was no approved paint or route map",
        "clue": "A weatherproof map at the kiosk still showed the loop's colors and every step-free turn.",
        "action": "They copied the problem onto a maintenance card, offered directions to visitors, and helped the keeper place approved temporary markers.",
        "result": "Everyone could follow the gentle loop until the permanent paint arrived.",
        "lesson": "lasting help follows shared plans and includes everyone",
        "ending": "Fresh temporary dots curved along the path in blue, green, and bright white.",
        "items": ["route map", "temporary markers"],
    },
    {
        "name": "the thirsty reed seedlings",
        "premise": "New reed seedlings drooped in their protected garden after a watering can sprang a leak.",
        "obstacle": "Pouring faster wasted more water onto the path instead of reaching the roots.",
        "first_attempt": "tipped the can higher, then saw a sparkling trail running from a crack near the handle",
        "clue": "A spare bottle with tiny cap holes sat beside the garden's written watering directions.",
        "action": "They carried small measured bottles, shared the rows, and reported the cracked can for repair.",
        "result": "Every seedling received water at its roots without turning the path muddy.",
        "lesson": "steady small actions can accomplish more than one hurried effort",
        "ending": "Water beads balanced on the reeds while the dry path glowed in the late sun.",
        "items": ["cracked watering can", "measured bottles"],
    },
    {
        "name": "the bell beneath the bench",
        "premise": "A tiny brass bell rang beneath a bench whenever the river breeze rose.",
        "obstacle": "The sound worried a nearby child, while reaching blindly under the bench risked splinters and hidden litter.",
        "first_attempt": "called into the reeds to find the bell's owner, then noticed the sound came from the path side",
        "clue": "A red thread appeared below the bench each time the bell chimed.",
        "action": "They shone a flashlight from the path, used a grabber to retrieve the bell, and matched its red thread to a puppet troupe's sign.",
        "result": "The troupe recovered its prop, and the worried child learned what had made the mysterious sound.",
        "lesson": "curiosity becomes helpful when it is paired with a careful test",
        "ending": "At sunset the little bell chimed once from the puppet cart, safely above the path.",
        "items": ["brass bell", "red thread"],
    },
]

OPENINGS = [
    "On an ordinary slice-of-life afternoon at the riverbank",
    "Although nothing about the quiet riverbank afternoon seemed like the start of a quest",
    "After lunch, on a day made for small riverside errands",
    "During a low-water afternoon on the busy riverbank path",
    "While cloud shadows moved over the river on a calm afternoon",
    "With birdsong and bicycle bells sharing the riverside air",
    "At the beginning of one unhurried riverbank walk",
    "Between an ordinary snack and the walk home from the riverbank",
    "Although the riverbank looked peaceful enough for a simple visit",
    "As a mild breeze followed two walkers down the riverside path",
]

PROMISE_BEATS = [
    "said the promise aloud so it would be easy to remember",
    "wrote the promise on the back of an old receipt",
    "asked the companion to help keep the promise honest",
    "made the promise before picking up a single tool",
    "paused at the map and chose one useful promise",
    "tied a loose loop in a piece of string as a reminder of the promise",
    "repeated the promise slowly, thinking about what it required",
    "turned an ordinary plan into a real promise",
    "checked that the promise was safe and possible",
    "chose a promise small enough to finish well",
]

TURN_BEATS = [
    "The plan changed when they noticed something unexpected:",
    "Halfway to the first task, a new problem interrupted them:",
    "Then the quiet afternoon presented a real puzzle:",
    "The quest became more complicated at the next bend:",
    "Before the work could properly begin, something else needed attention:",
    "A detail beside the path demanded a better plan:",
    "The easy part of the promise ended with a surprise:",
    "One bend later, they discovered the day's real challenge:",
    "Their checklist suddenly needed another line:",
    "The riverbank offered an unexpected test:",
]

REFLECTION_BEATS = [
    "Keeping a commitment, the child understood, was not the same as rushing.",
    "The quest had become useful precisely because the first plan had changed.",
    "A small decision had grown into careful work with a visible result.",
    "The companion pointed out that noticing was part of helping.",
    "The child could now explain not only what worked, but why it worked.",
    "Finishing well felt quieter and stronger than finishing first.",
    "The afternoon proved that an ordinary problem could teach an uncommon lesson.",
    "Their best tool had turned out to be the pause before acting.",
    "The child saw that a promise could protect people, animals, and places together.",
    "What looked like a detour had become the most important part of the quest.",
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(NAME_POOL)
    companion = args.companion or rng.choice(COMPANION_POOL)
    quest = args.quest or rng.choice(QUEST_POOL)
    transformation = args.transformation or rng.choice(TRANS_POOL)
    commitment = args.commitment or "commit to helping the riverbank stay tidy"
    if "commit" not in commitment.lower():
        commitment = f"commit to {commitment}"
    if args.place and args.place != "riverbank":
        raise StoryError("This world only supports the riverbank setting.")
    return StoryParams(
        place="riverbank",
        child=child,
        companion=companion,
        quest=quest,
        transformation=transformation,
        commitment=commitment,
    )


def make_world(params: StoryParams) -> World:
    child = Person(name=params.child, role="child")
    companion = Person(name=params.companion, role="companion")
    return World(place=params.place, child=child, companion=companion)


def generate_story(world: World, params: StoryParams) -> None:
    if params.seed is None:
        material = "|".join(
            [params.place, params.child, params.companion, params.quest, params.transformation, params.commitment]
        )
        story_seed = int.from_bytes(hashlib.blake2b(material.encode("utf-8"), digest_size=8).digest(), "big")
    else:
        story_seed = params.seed
    incident = INCIDENTS[story_seed % len(INCIDENTS)]
    mode = (story_seed // len(INCIDENTS)) % len(OPENINGS)
    promise = params.commitment.strip().rstrip(".")
    if not promise.lower().startswith("commit to"):
        promise = f"commit to {promise}"
    action = (
        incident["action"]
        .replace("The companion", world.companion.name)
        .replace("the companion", world.companion.name)
        .replace("The child", world.child.name)
        .replace("the child", world.child.name)
    )

    world.incident = incident["name"]
    world.obstacle = incident["obstacle"]
    world.clue = incident["clue"]
    world.first_attempt = incident["first_attempt"]
    world.resolution = incident["result"]
    world.lesson = incident["lesson"]
    world.ending_image = incident["ending"]
    world.found_items.extend(incident["items"])

    world.say(
        f"{OPENINGS[mode]}, {world.child.name} walked with "
        f"{world.companion.name} and watched light travel over the reeds."
    )
    world.say(
        f"{world.child.name} {PROMISE_BEATS[mode]}: \"I {promise}.\" "
        f"Today's gentle quest was to {params.quest}."
    )
    world.committed = True
    world.child.memes["care"] += 1.0
    world.child.meters["energy"] -= 0.1
    world.say(
        f"\"A commitment is something we keep with our judgment as well as our hands,\" "
        f"{world.companion.name} replied, packing gloves, a grabber, and the park keeper's number."
    )
    world.quest_started = True
    world.say(
        f"{TURN_BEATS[mode]} {incident['premise']} {incident['obstacle']}"
    )
    world.say(
        f"At first, {world.child.name} {incident['first_attempt']}. \"Let's look for evidence before "
        f"we decide,\" {world.child.name} said. {incident['clue']}"
    )
    world.say(action)
    world.say(incident["result"])
    world.river_cleanliness += 0.25
    world.river_mood += 0.35
    world.child.meters["energy"] -= 0.2
    world.child.memes["confidence"] += 0.5
    world.say(
        f"With the surprise handled, they returned to the original quest and finished the work to "
        f"{params.quest}, checking the path once more before packing their tools."
    )
    world.quest_finished = True
    world.say(
        f"{REFLECTION_BEATS[mode]} {world.child.name} learned that {incident['lesson']}."
    )
    world.transformed = True
    world.child.memes["confidence"] += 1.0
    world.child.memes["care"] += 1.0
    world.child.memes["calm"] += 0.5
    world.say(
        f"That choice transformed the afternoon and left {world.child.name} feeling genuinely "
        f"{params.transformation}. {incident['ending']}"
    )


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    commitment_detail = p.commitment.strip().rstrip(".")
    if commitment_detail.lower().startswith("commit to "):
        commitment_detail = commitment_detail[len("commit to ") :]
    return [
        QAItem(
            question=f"Where did {p.child} spend the afternoon?",
            answer=f"{p.child} spent the afternoon at the riverbank with {p.companion}.",
        ),
        QAItem(
            question=f"What did {p.child} commit to do?",
            answer=(
                f"{p.child} committed to {commitment_detail}. The promise guided the whole riverbank quest."
            ),
        ),
        QAItem(
            question=f"What unexpected problem changed {p.child}'s plan?",
            answer=f"The plan changed during {world.incident}. {world.obstacle}",
        ),
        QAItem(
            question=f"What clue helped {p.child} choose a better response?",
            answer=world.clue,
        ),
        QAItem(
            question=f"Why did {p.child} change the first approach?",
            answer=(
                f"{p.child} first {world.first_attempt}. The clue showed that a more careful response "
                f"would address the real cause without creating another problem."
            ),
        ),
        QAItem(
            question="What was different after the riverbank problem was solved?",
            answer=world.resolution,
        ),
        QAItem(
            question=f"How did the quest change {p.child}?",
            answer=(
                f"By the end, {p.child} felt {p.transformation} because they kept the commitment "
                f"and learned that {world.lesson}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land next to a river.",
        ),
        QAItem(
            question="Why might people pick up litter near water?",
            answer="People pick up litter near water to keep the shore clean and protect the place where animals and plants live.",
        ),
        QAItem(
            question="What does it mean to commit to something?",
            answer="To commit to something means to decide to do it and keep trying until it is done.",
        ),
    ]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        f"Write a gentle slice-of-life story set at a {params.place} about a child who makes a commitment.",
        f"Tell a child-friendly quest story where {params.child} goes to the riverbank to {params.quest}.",
        f"Write a short story about how helping at the riverbank can transform someone into a more {params.transformation} person.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(riverbank).
commitment(X) :- phrase(X).
quest(Q) :- task(Q).
transformation(T) :- feeling(T).
valid_story :- place(riverbank), commitment(_), quest(_), transformation(_).
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "riverbank"),
            asp.fact("phrase", "commit to helping the riverbank stay clean"),
            asp.fact("task", "collect the fallen litter"),
            asp.fact("feeling", "brave"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP story gate is satisfiable.")
        return 0
    print("MISMATCH: ASP story gate did not produce a model.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world.facts["params"] = params
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(params),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        print(asdict(sample.params))
        print({
            "child": sample.world.child.meters | sample.world.child.memes,
            "river_cleanliness": sample.world.river_cleanliness,
            "river_mood": sample.world.river_mood,
            "committed": sample.world.committed,
            "quest_started": sample.world.quest_started,
            "quest_finished": sample.world.quest_finished,
            "transformed": sample.world.transformed,
            "found_items": sample.world.found_items,
        })
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        child="Mina",
        companion="Grandpa",
        quest="collect the fallen litter",
        transformation="confident",
        commitment="commit to helping the riverbank stay clean",
    ),
    StoryParams(
        child="Theo",
        companion="Mom",
        quest="bring seeds to plant by the reeds",
        transformation="thoughtful",
        commitment="commit to taking care of the quiet shore",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("ASP model:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
