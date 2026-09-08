#!/usr/bin/env python3
"""
A small stand-alone storyworld about a pirate tale with historic shutters, friendship, and problem solving.

Seed premise:
A crew visits an old harbor fort with historic shutters, but one shutter sticks in a storm. Friends must work together, talk it out, and solve the problem before the tide changes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    friend: str
    captain: str
    place: str
    shutter: str
    relic: str
    storm: int = 0
    premise: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Mira", "Jory", "Lena", "Tomas", "Pia", "Oren", "Sage", "Nell"]
FRIENDS = ["Finn", "Bea", "Rook", "Ivy", "Nico", "Tilda"]
CAPTAINS = ["Captain Brine", "Captain Salt", "Captain Marlow", "Captain Wave"]
PLACES = [
    "the old harbor fort",
    "the lighthouse stairs",
    "the museum pier",
    "the weathered port gate",
]
SHUTTERS = [
    "a green wooden shutter",
    "a blue shutter with brass hinges",
    "a tall historic shutter",
    "a carved shutter with peeling paint",
]
RELICS = [
    "a brass key",
    "an old map tube",
    "a silver compass",
    "a sealed letter",
]

PREMISES = [
    "{name} and {friend} came to {place} with {captain} to study its historic shutter. The sea wind tugged at the old wood like a curious ghost.",
    "At {place}, {captain} promised a short visit and a long story. {name} only cared that the historic shutter looked ready to snap in the wind.",
    "The crew crossed the stones of {place} while gulls cried overhead. Behind one historic shutter, {relic} was said to be hidden from storm spray.",
    "{name} had never seen {place} so close. {friend} said the fort's historic shutter could tell secrets if anyone listened kindly enough.",
    "Rain clouds gathered above {place}, and the old walls shivered. {captain} pointed to the historic shutter and said it needed careful hands, not quick ones.",
    "The harbor path led straight to {place}, where a historic shutter had stuck for years. {name} and {friend} came ready to help with any small repair.",
]

STORMS = [
    {
        "lead": "First, the historic shutter creaked open halfway, then stopped with a grumpy squeal.",
        "trigger": "A gust of sea wind pressed it harder, and the shutter jammed against the stone frame.",
        "risk": "If it stayed stuck, the rain would blow inside and wet the papers, ropes, and anything else kept there.",
        "action": "{name} held the shutter steady while {friend} tucked a folded cloth under the lower edge. {captain} eased the hinge with a drop of oil.",
        "resolution": "The shutter swung free at last, and the room breathed out the salty air without letting in the rain.",
        "cause": "a sea gust jammed the historic shutter against the frame",
        "deed": "held the shutter steady and helped slip cloth under the edge",
        "result": "the captain oiled the hinge and the shutter swung free",
    },
    {
        "lead": "{captain} found {relic} behind the shutter, but the latch had locked itself tight again.",
        "trigger": "The metal latch rattled, then clamped shut when thunder rolled over the harbor.",
        "risk": "No one could reach the relic without opening the shutter, and the tide was climbing faster every minute.",
        "action": "{friend} said, 'We need a kinder trick, not a harder pull.' {name} fetched a flat stick and nudged the latch while {captain} lifted the frame.",
        "resolution": "The latch loosened, the relic came safely out, and the crew set it on a dry crate near the door.",
        "cause": "thunder made the old latch clamp shut",
        "deed": "used a flat stick to nudge the latch while the captain lifted",
        "result": "the latch loosened and the relic came out safely",
    },
    {
        "lead": "The shutter's paint flaked into the wind, and a narrow gap showed the dark room beyond.",
        "trigger": "Through that gap, a rolled map began slipping toward the rain-soaked floor.",
        "risk": "One splash could blur the ink and lose the route to the harbor path.",
        "action": "{name} called, 'I see it!' and {friend} caught the map tube before it dropped. {captain} slid the shutter closed just enough to block the wind.",
        "resolution": "The map stayed dry, and the crew carried it to the table to copy the route carefully.",
        "cause": "the wind blew a rolled map toward the floor through a gap",
        "deed": "caught the map tube and helped close the shutter",
        "result": "the map stayed dry and the route was saved",
    },
    {
        "lead": "{name} and {friend} cleaned the salt from the historic shutter while {captain} checked the hinges.",
        "trigger": "Then a loose screw rolled across the sill and disappeared under a crate with a soft clack.",
        "risk": "Without that screw, the shutter might sag and drag on the stone floor.",
        "action": "{friend} lifted the crate, and {name} found the screw by shining a lantern across the sill. {captain} tightened it back in place.",
        "resolution": "The shutter sat square again, and the old fort looked proud instead of tired.",
        "cause": "a loose screw rolled under the crate",
        "deed": "shone a lantern and found the missing screw",
        "result": "the captain tightened the screw and the shutter sat square",
    },
    {
        "lead": "{captain} asked the crew to test the shutter after the storm, so {name} gave it a careful push.",
        "trigger": "It moved two inches, then stopped because a knot in the wood snagged on the frame.",
        "risk": "The shutter would stay half open and let the draft rattle every paper in the room.",
        "action": "{name} asked, 'Can we sand the knot smooth?' {friend} nodded, fetched a file, and worked the rough spot gently.",
        "resolution": "With the knot smoothed down, the shutter glided open and shut like a boat in calm water.",
        "cause": "a wooden knot snagged the shutter on the frame",
        "deed": "used a file to smooth the rough spot",
        "result": "the shutter glided open and shut cleanly",
    },
    {
        "lead": "Behind the shutter, {name} saw a candle in a drafty niche and a thin ribbon fluttering in front of it.",
        "trigger": "The ribbon nearly touched the flame as the wind rose once more.",
        "risk": "If the ribbon caught, the tiny room could fill with smoke.",
        "action": "{friend} blew out the candle, and {name} slid the shutter shut to block the wind. {captain} thanked them both at once.",
        "resolution": "The ribbon dropped still, the room cooled, and the crew relit the candle in a safer spot.",
        "cause": "the wind pushed a ribbon toward a candle flame",
        "deed": "blowed out the candle and closed the shutter against the wind",
        "result": "the room stayed safe and the candle was relit elsewhere",
    },
]

DIALOGUES = [
    "'We fix it together,' said {friend}. 'A pirate crew is stronger with two pairs of hands.'",
    "'Can the shutter wait?' asked {name}. 'No,' said {captain}, 'but a calm plan can make it behave.'",
    "'Look for the small problem first,' said {captain}. 'Big storms often hide little causes.'",
    "'I hear the hinge crying,' said {friend}. 'Then let us speak kindly to it,' answered {name}.",
    "'Easy does it,' said {captain}. 'A stubborn shutter likes patience more than pulling.'",
    "'I'll hold it,' said {name}. 'Then I'll find the missing piece,' said {friend}.",
]

ENDINGS = [
    "At sunset, {place} glowed gold, and the historic shutter moved as smoothly as a ship leaving the dock. {name} and {friend} grinned because their teamwork had saved the room and the story inside it.",
    "When the rain finally passed, the crew stood under the repaired shutter and watched the tide settle. {captain} tipped a hat and said the fort had found the right kind of helpers.",
    "Before they left, {name} tapped the shutter once and heard only a quiet, solid thump. The old place felt safe again, as if it had been waiting for friends all along.",
    "The last light slipped over the harbor stones, and the historic shutter rested closed and sound. {friend} called it a brave old door, and {name} laughed at the title.",
    "Soon the crew carried their notes home, along with dry boots and a useful memory. The shutter stood steady behind them, proof that careful thinking could beat a wild wind.",
    "By the time the moon rose, the room behind the shutter was dry and calm. {captain} said the fort looked younger, and {name} believed it.",
]

ASP_RULES = r"""
#show valid/4.
#show valid_story/5.

name(N) :- name_name(N).
friend(F) :- friend_name(F).
captain(C) :- captain_name(C).
place(P) :- place_name(P).
shutter(S) :- shutter_name(S).
relic(R) :- relic_name(R).

valid(N,F,C,P) :- name(N), friend(F), captain(C), place(P).
valid_story(N,F,C,P,S) :- valid(N,F,C,P), shutter_name(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for n in NAMES:
        lines.append(asp.fact("name_name", n))
    for f in FRIENDS:
        lines.append(asp.fact("friend_name", f))
    for c in CAPTAINS:
        lines.append(asp.fact("captain_name", c))
    for p in PLACES:
        lines.append(asp.fact("place_name", p))
    for s in SHUTTERS:
        lines.append(asp.fact("shutter_name", s))
    for r in RELICS:
        lines.append(asp.fact("relic_name", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale storyworld with historic shutters, friendship, and problem solving.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--captain", choices=CAPTAINS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shutter", choices=SHUTTERS)
    ap.add_argument("--relic", choices=RELICS)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        captain=args.captain or rng.choice(CAPTAINS),
        place=args.place or rng.choice(PLACES),
        shutter=args.shutter or rng.choice(SHUTTERS),
        relic=args.relic or rng.choice(RELICS),
        storm=rng.randrange(len(STORMS)),
        premise=rng.randrange(len(PREMISES)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def apply_seeded_structure(params: StoryParams, seed: int) -> None:
    params.storm = seed % len(STORMS)
    params.premise = (seed // len(STORMS)) % len(PREMISES)
    params.dialogue = (seed // 3) % len(DIALOGUES)
    params.ending = (seed // 5) % len(ENDINGS)


def generate(params: StoryParams) -> StorySample:
    values = {
        "name": params.name,
        "friend": params.friend,
        "captain": params.captain,
        "place": params.place,
        "shutter": params.shutter,
        "relic": params.relic,
    }
    event = STORMS[params.storm % len(STORMS)]

    w = World()
    w.add(Entity(id=params.name, kind="character", label=params.name))
    w.add(Entity(id=params.friend, kind="character", label=params.friend))
    w.add(Entity(id=params.captain, kind="character", label=params.captain))
    shutter = w.add(Entity(id="shutter", label=params.shutter, meters={"open": 0.0}, memes={"stubbornness": 0.8}))
    relic = w.add(Entity(id="relic", label=params.relic, meters={"dry": 1.0}, memes={"importance": 0.9}))

    w.say(PREMISES[params.premise % len(PREMISES)].format(**values))
    w.say(f"The salt wind worried the {shutter.label}, and the crew could hear the old wood knock like a drum.")
    w.say(event["lead"].format(**values))

    w.para()
    shutter.meters["open"] = 0.5
    shutter.memes["stubbornness"] = 1.0
    relic.meters["dry"] = 0.7
    w.say(event["trigger"].format(**values))
    w.say(event["risk"].format(**values))
    w.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(**values))
    w.say(event["action"].format(**values))

    w.para()
    shutter.meters["open"] = 1.0
    shutter.memes["stubbornness"] = 0.0
    relic.meters["dry"] = 1.0
    w.say(event["resolution"].format(**values))
    w.say(ENDINGS[params.ending % len(ENDINGS)].format(**values))

    w.facts.update(
        name=params.name,
        friend=params.friend,
        captain=params.captain,
        place=params.place,
        shutter=params.shutter,
        relic=params.relic,
        storm=params.storm,
        cause=event["cause"],
        deed=event["deed"],
        result=event["result"],
        friendship=True,
        problem_solving=True,
        resolved=True,
    )

    prompts = [
        "Write a pirate tale about friends solving a problem with a historic shutter at an old harbor place.",
        f"Tell a child-friendly pirate story where {params.name} and {params.friend} help {params.captain} fix a stubborn shutter.",
        f"Write an adventurous story with friendship, problem solving, a historic shutter, and a calm ending by the sea.",
    ]

    story_qa = [
        QAItem(
            question="Who worked together in the story?",
            answer=f"{params.name}, {params.friend}, and {params.captain} worked together to solve the problem.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble started because {event['cause']}. That made the historic shutter hard to manage.",
        ),
        QAItem(
            question="What did the friends say or do that helped?",
            answer=f"They talked it through and {event['deed']}. Their teamwork changed the problem into a fix.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"In the end, {event['result']}, and the place was safe and dry again.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a board or panel that opens and closes over a window or opening to protect what is inside.",
        ),
        QAItem(
            question="What does historic mean?",
            answer="Historic means something is old and important because it belongs to the past.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means people care about each other, help each other, and work well together.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a way to fix a difficulty by thinking carefully and trying helpful actions.",
        ),
        QAItem(
            question="Why can teamwork help in a storm?",
            answer="Teamwork can help because different people can hold, watch, and fix different parts of the problem at once.",
        ),
    ]

    return StorySample(params=params, story=w.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=w)


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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mira", friend="Finn", captain="Captain Brine", place="the old harbor fort", shutter="a tall historic shutter", relic="a brass key", storm=0, premise=0, dialogue=0, ending=0),
        StoryParams(name="Jory", friend="Bea", captain="Captain Salt", place="the museum pier", shutter="a carved shutter with peeling paint", relic="an old map tube", storm=2, premise=3, dialogue=3, ending=2),
        StoryParams(name="Lena", friend="Rook", captain="Captain Marlow", place="the weathered port gate", shutter="a blue shutter with brass hinges", relic="a silver compass", storm=4, premise=4, dialogue=1, ending=4),
        StoryParams(name="Oren", friend="Ivy", captain="Captain Wave", place="the lighthouse stairs", shutter="a green wooden shutter", relic="a sealed letter", storm=5, premise=5, dialogue=5, ending=5),
    ]


CURATED = build_curated()


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted({(name, friend, captain, place) for name, friend, captain, place in asp.atoms(model, "valid")})


def asp_verify() -> int:
    py = {(n, f, c, p) for n in NAMES for f in FRIENDS for c in CAPTAINS for p in PLACES}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches python registry coverage ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python registry coverage:")
    if py - cl:
        print("  only in python:", sorted(py - cl)[:10])
    if cl - py:
        print("  only in clingo:", sorted(cl - py)[:10])
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (name, friend, captain, place) combos:\n")
        for row in combos[:50]:
            print("  " + " | ".join(row))
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            apply_seeded_structure(params, seed)
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
            header = f"### {p.name}: pirate tale at {p.place} with {p.shutter}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
