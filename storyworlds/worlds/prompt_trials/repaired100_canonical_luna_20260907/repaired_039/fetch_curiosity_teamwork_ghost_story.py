#!/usr/bin/env python3
"""A gentle ghost story about fetch, curiosity, and teamwork."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectItem:
    name: str
    label: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Milo"
    place: str = "the old moonlit garden"
    ghost: str = "the pale gardener"
    toy: str = "a silver ball"
    task: str = "fetch"
    charm: str = "a blue ribbon"


@dataclass(frozen=True)
class Scenario:
    key: str
    trouble: str
    clue: str
    mistake: str
    hero_task: str
    helper_task: str
    solution: str
    result: str
    lesson: str
    ending: str


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, ObjectItem] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Nora", "Milo", "Pip", "Tess", "Jun"]
HELPERS = ["Milo", "Nora", "Grandma", "Theo", "Pip"]
PLACES = [
    "the old moonlit garden",
    "the abandoned train platform",
    "the little hill cemetery",
    "the empty seaside boathouse",
]
GHOSTS = [
    "the pale gardener",
    "the lantern ghost",
    "the quiet conductor",
    "the misty violinist",
]
TOYS = ["a silver ball", "a red wooden spool", "a brass bell", "a white paper kite"]
CHARMS = ["a blue ribbon", "a warm candle", "a tiny bell", "a sprig of lavender"]

SCENARIOS = [
    Scenario(
        "garden",
        "A silver ball rolled through the iron gate and vanished among the weeds.",
        "Three faint footprints curved toward the dry fountain, but none led back.",
        "Luna rushed after the ball alone and tangled her shoes in a vine.",
        "looked beneath the fountain stones",
        "held the lantern and followed the footprints",
        "They searched in a widening circle, then lifted one loose stone together.",
        "The ball rested in a shallow tunnel beside a faded garden key.",
        "curiosity is safest when a friend shares the search",
        "the ghost smiled as moonlight filled the fountain again",
    ),
    Scenario(
        "platform",
        "The red spool rolled under the silent train platform with a soft ghostly hum.",
        "Its thread caught on an old sign pointing toward the baggage room.",
        "pulling the thread quickly made the sign creak and the spool slide farther away.",
        "watched where the thread disappeared",
        "held the loose end steady",
        "They followed the thread slowly and reached under the platform with a broom.",
        "The spool came free, carrying a little brass ticket tied to it.",
        "a careful clue can turn a scary mystery into a shared plan",
        "the quiet conductor waved from the far end of the empty track",
    ),
    Scenario(
        "cemetery",
        "A brass bell bounced over the low wall and rang from somewhere among the stones.",
        "The ringing paused whenever the wind touched a crooked marble angel.",
        "calling loudly made the echo seem to come from everywhere.",
        "watched the angel's shadow",
        "stood where the wind was calm",
        "They waited for the shadow to point, then searched beside the matching stone.",
        "The bell was tucked in a hollow, with a name tag that belonged to the ghost.",
        "listening together can reveal what noise hides",
        "the ghost heard one clear bell and finally found its way home",
    ),
    Scenario(
        "boathouse",
        "The paper kite drifted into the dark boathouse and fluttered without any wind.",
        "A trail of saltwater drops led from the door to a stack of oars.",
        "grabbing at the kite stirred dust and sent it deeper inside.",
        "counted the drops beside the oars",
        "made a gentle path with a long oar",
        "They opened the shutters, then guided the kite toward the new moonlight.",
        "The kite floated out, and a lonely ghost followed its shining tail.",
        "helping a lost thing sometimes means making a safe way out",
        "the ghost rose like a pale sail above the quiet water",
    ),
]


def make_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different people")
    world = World(params=params)
    hero = Person(params.hero, "curious child")
    helper = Person(params.helper, "helpful friend")
    ghost = Person(params.ghost, "ghost")
    toy = ObjectItem("toy", params.toy, owner=params.ghost)
    world.people = {p.name: p for p in (hero, helper, ghost)}
    world.items = {"toy": toy}
    world.facts.update(hero=hero, helper=helper, ghost=ghost, toy=toy)
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    p = params

    world.say(f"At dusk, {p.hero} and {p.helper} visited {p.place}.")
    world.say(
        f"They had heard that {p.ghost} wandered there, searching for {p.toy}."
    )
    world.say(
        f"When a pale shape appeared beside the gate, {p.hero} felt curious instead of running away."
    )
    world.para()

    world.say(scenario.trouble)
    world.say(f'"Did you see where it went?" {p.hero} asked.')
    world.say(
        f'"I saw a clue, but we should look together," {p.helper} replied.'
    )
    world.say(scenario.clue)
    world.say(f"At first, {p.hero} {scenario.mistake}")
    world.para()

    world.say(f'"Let us make a plan," {p.helper} said. "Curiosity needs care."')
    world.say(f"{p.hero} {scenario.hero_task}, while {p.helper} {scenario.helper_task}.")
    world.say(scenario.solution)
    world.say(
        f"The pale ghost whispered, 'Thank you,' and held out {p.charm}."
    )
    world.say(scenario.result)
    world.para()

    world.say(
        f"{p.hero} returned {p.toy} to {p.ghost}, who brightened like a candle behind mist."
    )
    world.say(f"The ghost explained that {scenario.lesson}.")
    world.say(
        f"When the friends left {p.place}, {scenario.ending}, and {p.charm} glowed softly in {p.hero}'s hand."
    )

    world.people[p.hero].memes.update(curiosity=1.0, courage=1.0, teamwork=1.0)
    world.people[p.helper].memes.update(care=1.0, teamwork=1.0)
    world.people[p.ghost].memes.update(relief=1.0, loneliness=0.0)
    world.items["toy"].meters["returned"] = 1.0
    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        clue=scenario.clue,
        mistake=scenario.mistake,
        hero_task=scenario.hero_task,
        helper_task=scenario.helper_task,
        solution=scenario.solution,
        result=scenario.result,
        lesson=scenario.lesson,
        ending=scenario.ending,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a gentle ghost story in which {p.hero} and {p.helper} fetch {p.toy} together.",
        f"Tell a child-friendly mystery at {p.place where curiosity becomes teamwork.",
        f"Create a warm supernatural tale about returning a lost object to {p.ghost}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    return [
        QAItem(
            question=f"What did {p.hero} and {p.helper} try to fetch?",
            answer=f"They tried to fetch {p.toy}, which had been lost by {p.ghost}.",
        ),
        QAItem(
            question="What clue helped them search?",
            answer=f"They noticed that {str(f['clue'])[0].lower() + str(f['clue'])[1:]} That clue gave them a careful direction.",
        ),
        QAItem(
            question="How did the friends use teamwork?",
            answer=f"{p.hero} {f['hero_task']}, while {p.helper} {f['helper_task']}. Their different jobs made the search safer and more useful.",
        ),
        QAItem(
            question="How did curiosity change the story?",
            answer=f"{p.hero} stayed curious about the ghost instead of fleeing. By asking questions and observing clues, {p.hero} helped discover how to return {p.toy}.",
        ),
        QAItem(
            question="What showed that the ghost was no longer troubled?",
            answer=f"{p.hero} returned {p.toy} to {p.ghost}. Then {f['ending']}, showing that the ghost had found peace.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is a wish to learn or understand something. It is strongest when questions are paired with careful observation.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people share a goal and use different strengths to reach it. Good teammates communicate and keep one another safe.",
        ),
        QAItem(
            question="Why should someone investigate a frightening mystery carefully?",
            answer="Careful investigation helps a person notice real clues instead of guessing. A trusted friend can make the search safer and less frightening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
ghost(G) :- ghost_name(G).
toy(T) :- toy_name(T).
curious(H) :- hero(H), curiosity(H).
teamwork(H,K) :- hero(H), helper(K), shared_search(H,K).
fetch_resolved(H,K,G,T) :- curious(H), teamwork(H,K), ghost(G), toy(T), returned(T,G).
gentle_ghost_story(H,K,G,T) :- fetch_resolved(H,K,G,T).
"""

DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp

    p = DEFAULT_PARAMS
    return "\n".join(
        [
            asp.fact("hero_name", p.hero),
            asp.fact("helper_name", p.helper),
            asp.fact("ghost_name", p.ghost),
            asp.fact("toy_name", p.toy),
            asp.fact("curiosity", p.hero),
            asp.fact("shared_search", p.hero, p.helper),
            asp.fact("returned", p.toy, p.ghost),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show gentle_ghost_story/4."))
    atoms = asp.atoms(symbols, "gentle_ghost_story")
    if atoms:
        print("OK: ASP and Python both support a curious teamwork fetch story.")
        return 0
    print("MISMATCH: expected gentle ghost story atom missing.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--ghost", choices=GHOSTS)
    parser.add_argument("--toy", choices=TOYS)
    parser.add_argument("--charm", choices=CHARMS)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAMES)
    helper = args.helper or rng.choice([x for x in HELPERS if x != hero])
    return StoryParams(
        seed=args.seed,
        hero=hero,
        helper=helper,
        place=args.place or rng.choice(PLACES),
        ghost=args.ghost or rng.choice(GHOSTS),
        toy=args.toy or rng.choice(TOYS),
        task="fetch",
        charm=args.charm or rng.choice(CHARMS),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(
            "\n--- trace ---\n"
            f"hero={sample.world.params.hero}\n"
            f"helper={sample.world.params.helper}\n"
            f"scenario={sample.world.facts['scenario']}\n"
            f"clue={sample.world.facts['clue']}\n"
            f"resolved={sample.world.facts['resolved']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show gentle_ghost_story/4."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible curious teamwork fetch ghost story pattern.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, scenario in enumerate(SCENARIOS):
            params = StoryParams(
                seed=base_seed + i,
                hero=args.hero or NAMES[i % len(NAMES)],
                helper=args.helper or HELPERS[i % len(HELPERS)],
                place=args.place or PLACES[i % len(PLACES)],
                ghost=args.ghost or GHOSTS[i % len(GHOSTS)],
                toy=args.toy or TOYS[i % len(TOYS)],
                charm=args.charm or CHARMS[i % len(CHARMS)],
            )
            if params.hero == params.helper:
                params.helper = "Theo"
            samples.append(generate(params))
    else:
        for i in range(args.n):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
