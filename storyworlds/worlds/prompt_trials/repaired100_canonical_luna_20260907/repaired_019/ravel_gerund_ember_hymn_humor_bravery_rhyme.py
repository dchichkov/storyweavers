#!/usr/bin/env python3
"""
A standalone storyworld about a brave little ghost, a ravel-gerund, an ember,
and a hymn whose rhyme untangles a haunting.
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
class Place:
    key: str
    name: str
    light: str


@dataclass
class Character:
    name: str
    kind: str
    trait: str
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Haunt:
    material: str
    knot: str
    sound: str
    resolved: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    kind: str
    trait: str
    place: str
    ember_color: str
    seed: Optional[int] = None


PLACES = {
    "chapel": Place("chapel", "the little hill chapel", "moon-pale"),
    "boathouse": Place("boathouse", "the old boathouse", "silver"),
    "bell_tower": Place("bell tower", "the abandoned bell tower", "blue"),
}

KINDS = ["ghost", "bat", "fox", "mouse", "raven"]
TRAITS = ["brave", "cheerful", "curious", "kind"]
EMBER_COLORS = {
    "red": "a red ember",
    "gold": "a gold ember",
    "violet": "a violet ember",
}

NAMES = {
    "ghost": ["Luna", "Wisp", "Morrow"],
    "bat": ["Bram", "Pip", "Echo"],
    "fox": ["Fenn", "Merry", "Tavi"],
    "mouse": ["Nell", "Puck", "Moss"],
    "raven": ["Rook", "Sable", "Jett"],
}


@dataclass(frozen=True)
class HauntArc:
    use: str
    trigger: str
    sound: str
    apparition: str
    knot: str
    clue: str
    obstacle: str
    action: str
    result: str
    ending: str
    rhyme: str
    joke: str


ARCS = [
    HauntArc(
        "polishing the chapel keys",
        "a draft blew three hymn pages from the stand",
        "whuff-whuff",
        "a pale sleeve curled from the organ pipes",
        "a ravel-gerund of silver thread around the bell rope",
        "each loop tightened whenever the hymn lost its rhyme",
        "The rope gave a tug, as if the ghost wanted to dance but had forgotten the steps.",
        "held the ember near the thread and sang the missing couplet with a bright rhyme",
        "the silver loops loosened without burning the old rope",
        "the bell rang once, gently, and the pale sleeve waved goodbye",
        "Bright ember, gentle flame; rhyme the knot and name its name",
        "Even the ghost looked embarrassed, as if it had worn its sheet backward.",
    ),
    HauntArc(
        "sorting buttons for the winter coats",
        "a cold giggle rose from beneath the choir bench",
        "hee-hee-hush",
        "a transparent hand pointed toward the dusty stove",
        "a ravel-gerund of gray cobweb around one stubborn ember",
        "the cobweb shivered at every word that ended without a matching sound",
        "The ember sneezed a spark, and the cobweb replied with a tiny ghostly hiccup.",
        "shielded the ember, spoke the hymn in rhyming pairs, and unwound the cobweb one loop at a time",
        "the ember glowed warmly while the gray web fell into a harmless puff",
        "the stove warmed the bench, and the giggle became a grateful chuckle",
        "Small light, warm and bright; rhyme the dark into the night",
        "The ghost had tried to look frightening, but its hiccup sounded like a duck.",
    ),
    HauntArc(
        "mending a banner for the moon festival",
        "the banner began waving though every window was shut",
        "flap-flap-floom",
        "a round ghostly face peeked over the rafters",
        "a ravel-gerund of blue ribbon tied around the hymn book",
        "the ribbon pulled tighter whenever anyone spoke in a straight, unrhymed line",
        "The face puffed its cheeks so fiercely that dust formed a mustache.",
        "carried the ember beneath the ribbon and answered the ghost in a brave little rhyme",
        "the knot opened and the ribbon settled flat on the book",
        "the banner flew only in the friendly night breeze",
        "Ember red, ribbon blue; rhyme a song and I will too",
        "The ghost's mustache floated away, which made everyone laugh, including the ghost.",
    ),
    HauntArc(
        "counting acorns beside the bell",
        "one acorn rolled uphill and tapped the bell",
        "plink-plonk-plink",
        "a tiny ghost rode the bell's swinging clapper",
        "a ravel-gerund of root fibers wrapped around the bell's wooden frame",
        "the roots hummed whenever the hymn's final words failed to echo",
        "The clapper swung harder, although the tiny ghost insisted it was only practicing manners.",
        "held the ember under the roots and sang the hymn with a matching final rhyme",
        "the roots slipped free and the clapper slowed to a soft tick",
        "the bell kept the last rhyme like a secret and the tiny ghost bowed",
        "Ring low, ring high; rhyme the night beneath the sky",
        "The ghost bowed so low that its head nearly rolled under the bell.",
    ),
    HauntArc(
        "painting stars on a wooden music box",
        "the music box played one note that was not in its tune",
        "plunk-plunk-plink",
        "a smoky little ghost rose from the painted stars",
        "a ravel-gerund of black yarn threaded through the music box",
        "the yarn tightened every time the tune forgot its rhyme",
        "The music box coughed out a note so sour that the ghost covered its ears.",
        "set the ember beside the box and sang a brave, funny rhyme until the yarn relaxed",
        "the black yarn unwound and the music box found its tune",
        "the painted stars seemed to wink while the ghost hummed along",
        "Star by star, near and far; rhyme the tune and mend the jar",
        "The ghost declared the sour note excellent, then quietly asked for another.",
    ),
]

LESSONS = [
    "Courage does not mean never feeling a shiver; it means carrying a little light while asking what the shiver means.",
    "A kind joke can open a door that a hard command only rattles.",
    "When a problem is tangled, a patient rhyme can make the next loop visible.",
    "Bravery grows brighter when it is shared with laughter.",
]

OPENINGS = [
    "At midnight, the moon hung over the place like a button on a dark coat.",
    "Everyone said the place was empty, but empty places can remember.",
    "The night was quiet enough to hear dust settling on the old stones.",
    "A small light waited in the dark, and the dark pretended not to notice.",
]


class World:
    def __init__(self, place: Place):
        self.place = place
        self.hero: Optional[Character] = None
        self.haunt = Haunt("", "")
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    world.hero = Character(params.name, params.kind, params.trait)
    choice = params.seed
    if choice is None:
        key = "|".join([params.name, params.kind, params.trait, params.place, params.ember_color])
        choice = sum((i + 1) * ord(c) for i, c in enumerate(key))
    arc = ARCS[choice % len(ARCS)]
    world.haunt = Haunt(
        material="old thread",
        knot=arc.knot,
        meters={"tangle": 1.0, "warmth": 0.0},
        memes={"fear": 0.7, "trust": 0.0, "humor": 0.0},
    )
    world.facts.update(
        arc=arc,
        opening=OPENINGS[(choice // len(ARCS)) % len(OPENINGS)],
        lesson=LESSONS[(choice * 3) % len(LESSONS)],
        ember=EMBER_COLORS[params.ember_color],
        location=f"in {place.name}" if "tower" not in place.name else "inside " + place.name,
        dialogue=f'"If the knot can giggle, it can listen," {params.name} said.',
    )
    return world


def light_ember(world: World) -> None:
    if "ember" in world.fired:
        return
    world.fired.add("ember")
    world.haunt.meters["warmth"] = 0.4
    world.haunt.memes["fear"] = 0.5
    world.say(
        f"{world.hero.name} cupped {world.facts['ember']} in both paws. "
        f"It was small, but it made the shadows step back politely."
    )


def hear_haunt(world: World) -> None:
    if "hear" in world.fired:
        return
    world.fired.add("hear")
    arc = world.facts["arc"]
    world.say(f"The darkness answered with {arc.sound}, like {arc.apparition}.")
    world.say(f"{arc.joke} {world.facts['dialogue']}")
    world.hero.memes["bravery"] = 0.5


def inspect_knot(world: World) -> None:
    if "inspect" in world.fired:
        return
    world.fired.add("inspect")
    arc = world.facts["arc"]
    world.say(
        f"{world.hero.name} did not chase the apparition. Instead, {world.hero.name} "
        f"watched the ember's glow and saw that {arc.clue}."
    )
    world.facts["cause_found"] = True


def untangle(world: World) -> None:
    if "untangle" in world.fired:
        return
    if not world.facts.get("cause_found"):
        raise StoryError("The ravel-gerund cannot be untangled before its clue is understood.")
    world.fired.add("untangle")
    arc = world.facts["arc"]
    world.say(f"{arc.obstacle} The ghost whispered, 'Do you know the way?'")
    world.say(
        f'"I know one step," {world.hero.name} replied. '
        f'"We follow the rhyme, not the fright."'
    )
    world.say(
        f"{world.hero.name} {arc.action}. {arc.result.capitalize()}."
    )
    world.haunt.resolved = True
    world.haunt.meters["tangle"] = 0.0
    world.haunt.meters["warmth"] = 1.0
    world.haunt.memes["fear"] = 0.0
    world.haunt.memes["trust"] = 1.0
    world.haunt.memes["humor"] = 1.0
    world.hero.memes["bravery"] = 1.0


def conclude(world: World) -> None:
    if "conclude" in world.fired:
        return
    world.fired.add("conclude")
    arc = world.facts["arc"]
    world.say(
        f"At last, {arc.ending}. The ghost bowed, and {world.hero.name} bowed back "
        f"so bravely that the ember nearly rolled away laughing. {world.facts['lesson']}"
    )


def tell_story(world: World) -> None:
    hero = world.hero
    arc = world.facts["arc"]
    world.say(
        f"{world.facts['opening']} {world.hero.name}, a {hero.trait} little {hero.kind}, "
        f"lived {world.facts['location']}."
    )
    world.say(
        f"Each night, {hero.name} {arc.use}. The work was peaceful until {arc.trigger}."
    )
    world.para()
    light_ember(world)
    hear_haunt(world)
    world.say(f"The hymn on the stand opened by itself, and its loose pages began to rhyme.")
    world.para()
    inspect_knot(world)
    untangle(world)
    conclude(world)
    world.facts.update(
        problem=arc.knot,
        cause=arc.clue,
        action=arc.action,
        result=arc.result,
        ending=arc.ending,
        rhyme=arc.rhyme,
        resolved=world.haunt.resolved,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly ghost story about {f['hero'].name}, {f['ember']}, and a hymn.",
        f"Use the ravel-gerund '{f['problem']}' as the haunting problem and solve it with the rhyme '{f['rhyme']}'.",
        "Include humor and bravery, with a spoken exchange that changes the hero's plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            f"What was tangled in the haunting?",
            f"The haunting was tangled by {f['problem']}.",
        ),
        QAItem(
            f"How did {hero.name} discover what to do?",
            f"{hero.name} watched the ember and learned that {f['cause']}.",
        ),
        QAItem(
            f"What did {hero.name} say to the ghost?",
            f'{hero.name} said, "I know one step. We follow the rhyme, not the fright."',
        ),
        QAItem(
            f"What proved the haunting was resolved?",
            f"{f['result'].capitalize()} Afterward, {f['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an ember?", "An ember is a small glowing piece of coal or wood that remains after a fire."),
        QAItem("What is a hymn?", "A hymn is a song of praise or devotion, often sung by a group."),
        QAItem("What does brave mean?", "Being brave means facing something difficult or frightening while still trying to do what is right."),
        QAItem("Why can rhyme help a song?", "Rhyme gives matching sounds to words, making a song easier to remember and sing."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"place={world.place.name}",
        f"hero={world.hero.name} ({world.hero.kind}, {world.hero.trait})",
        f"problem={world.facts.get('problem')}",
        f"cause={world.facts.get('cause')}",
        f"resolved={world.haunt.resolved}",
        f"meters={world.haunt.meters}",
        f"memes={world.haunt.memes}",
        f"fired={sorted(world.fired)}",
    ])


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, k, e) for p in PLACES for k in KINDS for e in EMBER_COLORS]


ASP_RULES = r"""
place(P) :- place_name(P).
kind(K) :- kind_name(K).
ember(E) :- ember_name(E).
valid(P,K,E) :- place(P), kind(K), ember(E).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    for k in KINDS:
        lines.append(asp.fact("kind_name", k))
    for e in EMBER_COLORS:
        lines.append(asp.fact("ember_name", e))
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
        print("MISMATCH between Python and ASP gates.")
        return 1
    for p, k, e in valid_combos()[:5]:
        sample = generate(StoryParams("Luna", k, "brave", p, e))
        if not sample.story or not sample.world.haunt.resolved:
            print("Generated-story verification failed.")
            return 1
    print(f"OK: ASP parity and generated stories verified ({len(py)} combinations).")
    return 0


@dataclass
class _Args:
    place: Optional[str] = None
    kind: Optional[str] = None
    trait: Optional[str] = None
    ember: Optional[str] = None
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
    StoryParams("Luna", "ghost", "brave", "chapel", "red"),
    StoryParams("Pip", "bat", "cheerful", "boathouse", "gold"),
    StoryParams("Merry", "fox", "curious", "bell_tower", "violet"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous ghost story about an ember, a hymn, and a brave rhyme.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--ember", choices=list(EMBER_COLORS))
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
        place=args.place or rng.choice(list(PLACES)),
        ember_color=args.ember or rng.choice(list(EMBER_COLORS)),
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
    if trace:
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
        for p, k, e in asp_valid_combos():
            print(f"{p:12} {k:8} {e}")
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        p = sample.params
        header = f"### {p.name}: {p.kind} in {p.place}" if args.all or len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
