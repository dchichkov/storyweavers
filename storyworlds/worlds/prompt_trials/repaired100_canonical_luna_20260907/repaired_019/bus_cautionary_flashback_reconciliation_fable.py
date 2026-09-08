#!/usr/bin/env python3
"""
A standalone storyworld: a cautionary bus fable about a flashback and
reconciliation.

Luna learns that a busy bus stop is no place for rushing. A remembered warning
helps her notice another passenger's fear, and a kind conversation repairs a
hurt feeling before the bus carries everyone onward.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Stop:
    key: str
    name: str
    weather: str
    landmark: str


@dataclass
class Passenger:
    name: str
    kind: str
    trait: str
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Bus:
    color: str = "blue"
    route: str = "the River Road"
    arriving: bool = False
    doors_open: bool = False
    seats_available: int = 3
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    kind: str
    trait: str
    stop: str
    bus_color: str
    seed: Optional[int] = None


STOPS = {
    "maple": Stop("maple", "Maple Corner", "a bright morning", "a maple tree"),
    "river": Stop("river", "River Bend", "a windy afternoon", "a stone bridge"),
    "market": Stop("market", "Market Gate", "a drizzly morning", "a striped awning"),
}

STOP_PHRASES = {
    "maple": "at Maple Corner",
    "river": "at River Bend",
    "market": "by Market Gate",
}

KINDS = ["rabbit", "fox", "mouse", "badger", "squirrel"]
TRAITS = ["quick", "cheerful", "curious", "proud", "helpful"]
BUS_COLORS = {
    "blue": "blue",
    "green": "green",
    "yellow": "yellow",
}
NAMES = {
    "rabbit": ["Luna", "Tilly", "Bram"],
    "fox": ["Mira", "Fenn", "Cora"],
    "mouse": ["Nim", "Pip", "Moss"],
    "badger": ["Bruno", "Ada", "Rook"],
    "squirrel": ["Hazel", "Pecan", "Tansy"],
}

ARCS = [
    {
        "arrival": "the bus rounded the corner with a soft puff of smoke",
        "mistake": "Luna hurried toward the door and stepped in front of an old tortoise",
        "sound": "the tortoise's cane tapped twice on the pavement",
        "flashback_teacher": "Grandmother Fern",
        "flashback_lesson": "a safe journey begins when we make room for one another",
        "hurt": "the tortoise felt pushed aside and clutched the rail with worried claws",
        "obstacle": "The bus driver had already lifted one hand to close the doors",
        "action": "Luna stepped back, held the door button, and offered the tortoise her place",
        "reconcile": '"I am sorry I rushed," Luna said. "Would you like to board first?"',
        "reply": '"Thank you," said the tortoise. "Now I can climb without fear."',
        "ending": "the tortoise sat safely by the window while Luna found a seat beside a warm yellow pole",
        "lesson": "A hurried foot can make a heavy worry, but a thoughtful pause can lift it again.",
        "tool": "the door button",
    },
    {
        "arrival": "the bus rolled in beneath the stone bridge",
        "mistake": "Luna grabbed the last empty seat before noticing a small hedgehog's basket blocking the aisle",
        "sound": "the basket gave a lonely clatter",
        "flashback_teacher": "the old station keeper",
        "flashback_lesson": "look beyond the first empty space before claiming it",
        "hurt": "the hedgehog thought Luna cared only about her own comfort",
        "obstacle": "The bus swayed as passengers reached for the rails",
        "action": "Luna moved her bag, lifted the basket gently, and made room beside her",
        "reconcile": '"I saw a seat, but I did not see your trouble," Luna said.',
        "reply": '"And I saw your bag, but not your kind heart," said the hedgehog.',
        "ending": "the basket rested safely under the seat as the bus hummed beside the river",
        "lesson": "Seeing the whole path is wiser than grabbing the nearest place.",
        "tool": "a clear space beneath the seat",
    },
    {
        "arrival": "the bus sighed beside the striped market awning",
        "mistake": "Luna spoke sharply when a young goat paused in the aisle",
        "sound": "the goat's paper parcel crinkled like a small storm",
        "flashback_teacher": "Father Willow",
        "flashback_lesson": "a frightened pause may hide a question",
        "hurt": "the goat lowered his ears and forgot which stop he needed",
        "obstacle": "The market crowd pressed close behind them",
        "action": "Luna moved aside, asked the goat what he needed, and showed him the route card",
        "reconcile": '"I should have asked before I scolded," Luna said.',
        "reply": '"I should have spoken sooner," said the goat. "Thank you for listening."',
        "ending": "the goat found his stop, and Luna watched the route card flutter calmly in his hooves",
        "lesson": "A gentle question can open a road that a sharp word closes.",
        "tool": "the route card",
    },
    {
        "arrival": "the bus came whispering through a veil of morning rain",
        "mistake": "Luna dashed under the shelter and knocked a crow's umbrella into a puddle",
        "sound": "the umbrella snapped with a wet pop",
        "flashback_teacher": "Auntie Wren",
        "flashback_lesson": "when your hurry makes a splash, stop before you make another",
        "hurt": "the crow looked ready to leave the shelter and stand in the rain",
        "obstacle": "The bus was almost ready to pull away",
        "action": "Luna picked up the umbrella, dried its handle with her scarf, and waited for the crow",
        "reconcile": '"I was watching the bus and not my feet," Luna said. "I am sorry."',
        "reply": '"I was watching the rain and not your worry," said the crow. "Let us begin again."',
        "ending": "both passengers boarded beneath the mended umbrella while rain silvered the windows",
        "lesson": "An apology is a small shelter when someone has been caught in your mistake.",
        "tool": "her wool scarf",
    },
]

OPENINGS = [
    "Luna believed that quick paws could catch every good thing.",
    "Luna liked arriving first, moving first, and choosing first.",
    "At the bus stop, Luna's feet were often faster than her thoughts.",
    "Luna carried a bright travel bag and an even brighter sense of hurry.",
]

DIALOGUE_OPENERS = [
    '"Wait," Luna said, lifting a paw. "I need to think before I move."',
    '"Please tell me what you need," Luna said. "I am listening now."',
    '"I made this harder than it had to be," Luna admitted.',
    '"A bus can wait one breath," Luna reminded herself aloud.',
]


class World:
    def __init__(self, stop: Stop) -> None:
        self.stop = stop
        self.hero: Optional[Passenger] = None
        self.bus = Bus()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.bus.meters = {"crowding": 0.0, "safety": 0.0}
        self.bus.memes = {"trust": 0.0, "relief": 0.0}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def bus_is_ready(world: World) -> bool:
    return world.bus.arriving and world.bus.doors_open


def notice_bus(world: World) -> None:
    if "notice" in world.fired:
        return
    world.fired.add("notice")
    arc = world.facts["arc"]
    world.bus.arriving = True
    world.bus.doors_open = True
    world.bus.meters["crowding"] += 1.0
    world.say(f"{arc['arrival'].capitalize()}. Its doors opened with a friendly chime.")


def make_mistake(world: World) -> None:
    if "mistake" in world.fired:
        return
    if not bus_is_ready(world):
        raise StoryError("The passenger cannot rush aboard before the bus arrives and opens its doors.")
    world.fired.add("mistake")
    arc = world.facts["arc"]
    world.bus.meters["safety"] -= 1.0
    world.hero.memes["worry"] = 1.0
    world.say(f"{arc['mistake']}.")
    world.say(f"{arc['sound'].capitalize()}. {arc['hurt'].capitalize()}.")


def remember_warning(world: World) -> None:
    if "flashback" in world.fired:
        return
    world.fired.add("flashback")
    teacher, lesson = world.facts["flashback"]
    world.hero.memes["remembered"] = 1.0
    world.say(
        f"The sound opened a flashback in {world.hero.name}'s mind. Long ago, "
        f"{teacher} had taught, \"{lesson}.\""
    )


def reconcile(world: World) -> None:
    if "reconcile" in world.fired:
        return
    if "flashback" not in world.fired:
        raise StoryError("Reconciliation requires the remembered warning to change the choice.")
    world.fired.add("reconcile")
    arc = world.facts["arc"]
    world.say(f"{arc['obstacle']}.")
    world.say(world.facts["dialogue"])
    world.say(arc["reconcile"])
    world.say(arc["action"].capitalize() + ".")
    world.say(arc["reply"])
    world.hero.memes["worry"] = 0.0
    world.hero.memes["kindness"] = 1.0
    world.bus.meters["safety"] = 1.0
    world.bus.memes["trust"] = 1.0
    world.bus.memes["relief"] = 1.0


def conclude(world: World) -> None:
    if "conclude" in world.fired:
        return
    world.fired.add("conclude")
    arc = world.facts["arc"]
    if world.bus.memes["trust"] < 1.0:
        raise StoryError("The bus story cannot conclude before the passengers reconcile.")
    world.say(
        f"At last, the bus carried them onward. {arc['ending'].capitalize()}. "
        f"{arc['lesson']}"
    )


def build_world(params: StoryParams) -> World:
    world = World(STOPS[params.stop])
    world.hero = Passenger(params.name, params.kind, params.trait)
    world.bus.color = BUS_COLORS[params.bus_color]
    key = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c)
        for i, c in enumerate("|".join([params.name, params.kind, params.trait, params.stop, params.bus_color]))
    )
    arc = ARCS[key % len(ARCS)]
    world.facts.update(
        arc=arc,
        flashback=(arc["flashback_teacher"], arc["flashback_lesson"]),
        dialogue=DIALOGUE_OPENERS[(key // len(ARCS)) % len(DIALOGUE_OPENERS)],
        opening=OPENINGS[(key // (len(ARCS) * len(DIALOGUE_OPENERS))) % len(OPENINGS)],
        location=STOP_PHRASES[params.stop],
        route=world.bus.route,
        problem=arc["hurt"],
        action=arc["action"],
        ending=arc["ending"],
        tool=arc["tool"],
    )
    return world


def tell_story(world: World) -> None:
    hero = world.hero
    arc = world.facts["arc"]
    world.say(
        f"Once {world.facts['location']}, there lived a {hero.trait} little "
        f"{hero.kind} named {hero.name}."
    )
    world.say(
        f"{world.facts['opening']} Every day, {hero.name} waited for the "
        f"{world.bus.color} bus on {world.facts['route']}."
    )
    world.para()
    notice_bus(world)
    make_mistake(world)
    world.say(f"{hero.name} froze beside the bus door. {arc['hurt'].capitalize()}.")
    world.para()
    remember_warning(world)
    reconcile(world)
    world.para()
    conclude(world)
    world.facts.update(
        hero=hero,
        bus=world.bus,
        stop=world.stop,
        resolved=True,
        cause=arc["hurt"],
        remembered_lesson=world.facts["flashback"][1],
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.hero
    arc = world.facts["arc"]
    return [
        f"Write a fable about {hero.name}, a bus, and the caution that {arc['flashback_lesson']}.",
        f"Tell a flashback story {world.facts['location']} in which a rushed {hero.kind} repairs a hurt feeling.",
        f"Write a reconciliation fable featuring {arc['tool']} and the ending image: {arc['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    arc = world.facts["arc"]
    hero = world.hero
    return [
        QAItem(
            f"What mistake did {hero.name} make while boarding the bus?",
            f"{hero.name} rushed and caused this trouble: {arc['hurt']}.",
        ),
        QAItem(
            f"What did {hero.name} remember in the flashback?",
            f"{hero.name} remembered that {world.facts['remembered_lesson']}.",
        ),
        QAItem(
            "How did the passengers reconcile?",
            f"{hero.name} apologized, listened, and then {arc['action']}. {arc['reply']}",
        ),
        QAItem(
            "What proved that the problem was resolved?",
            f"{arc['ending'].capitalize()} This showed that the passengers trusted one another again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a bus?", "A bus is a vehicle that carries several passengers along a route."),
        QAItem("Why should people wait their turn when boarding?", "Waiting your turn helps everyone board safely and gives people room to move."),
        QAItem("What is a flashback?", "A flashback is a part of a story that remembers something that happened earlier."),
        QAItem("Why can an apology help?", "An honest apology shows that someone understands the hurt and wants to repair the relationship."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"stop={world.stop.name}",
            f"hero={world.hero.name} ({world.hero.kind}, {world.hero.trait})",
            f"bus.color={world.bus.color}",
            f"bus.route={world.bus.route}",
            f"problem={world.facts.get('problem')}",
            f"remembered_lesson={world.facts.get('remembered_lesson')}",
            f"action={world.facts.get('action')}",
            f"bus.meters={world.bus.meters}",
            f"bus.memes={world.bus.memes}",
            f"fired={sorted(world.fired)}",
        ]
    )


def valid_combos() -> list[tuple[str, str, str]]:
    return [(stop, kind, color) for stop in STOPS for kind in KINDS for color in BUS_COLORS]


ASP_RULES = r"""
stop(S) :- stop_name(S).
kind(K) :- kind_name(K).
color(C) :- color_name(C).
valid(S,K,C) :- stop(S), kind(K), color(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.extend(asp.fact("stop_name", x) for x in STOPS)
    lines.extend(asp.fact("kind_name", x) for x in KINDS)
    lines.extend(asp.fact("color_name", x) for x in BUS_COLORS)
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
    if py != cl:
        print("MISMATCH between Python and ASP valid combinations.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or "bus" not in sample.story.lower():
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combinations); generated stories pass.")
    return 0


@dataclass
class _Args:
    stop: Optional[str] = None
    kind: Optional[str] = None
    trait: Optional[str] = None
    color: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


CURATED = [
    StoryParams("Luna", "rabbit", "quick", "maple", "blue"),
    StoryParams("Mira", "fox", "curious", "river", "green"),
    StoryParams("Nim", "mouse", "helpful", "market", "yellow"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary bus fable about memory and reconciliation.")
    ap.add_argument("--stop", choices=STOPS)
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--color", choices=list(BUS_COLORS))
    ap.add_argument("--name")
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
    kind = args.kind or rng.choice(KINDS)
    return StoryParams(
        name=args.name or rng.choice(NAMES[kind]),
        kind=kind,
        trait=args.trait or rng.choice(TRAITS),
        stop=args.stop or rng.choice(list(STOPS)),
        bus_color=args.color or rng.choice(list(BUS_COLORS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
    if trace and sample.world:
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
        for stop, kind, color in asp_valid_combos():
            print(f"{stop:8} {kind:10} {color}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(max(0, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False)
        )
        return

    for i, sample in enumerate(samples):
        p = sample.params
        header = f"### {p.name}: {p.kind} at {p.stop}" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
