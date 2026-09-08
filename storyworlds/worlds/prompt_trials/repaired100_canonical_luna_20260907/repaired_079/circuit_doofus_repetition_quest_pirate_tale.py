#!/usr/bin/env python3
"""
A tiny pirate storyworld about a doofus, a repeating circuit signal, and a quest
to repair a lighthouse machine before the tide covers the harbor.
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Repetition:
    signal: str
    count: int = 0
    understood: bool = False


@dataclass
class Quest:
    goal: str
    started: bool = False
    completed: bool = False
    setbacks: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    trace: list[str] = field(default_factory=list)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain_name: str = "Luna"
    doofus_name: str = "Bram"
    ship_name: str = "the Jolly Circuit"


NAMES = ["Luna", "Mara", "Pip", "Nell", "Bram", "Toby", "Rook", "Sella"]
SHIP_NAMES = ["the Jolly Circuit", "the Brass Minnow", "the Moonlit Gull", "the Wobbly Anchor"]

ADVENTURES = [
    {
        "place": "Skullcap Island",
        "signal": "three bright flashes, then one dark pause",
        "wrong": "Bram pressed the brass switch after every flash and sent the circuit spinning backward",
        "setback": "the lighthouse went dark, and the harbor boats had to anchor outside the reef",
        "clue": "the dark pause was part of the signal, not a missing flash",
        "meaning": "Wait through the pause, then press the switch only once",
        "repair": "they cleaned the salt from the contacts, counted the flashes aloud, and waited through the dark pause",
        "success": "the lighthouse beam swept across the sea and showed the boats a safe channel",
        "ending": "the harbor bells rang while warm lanterns glowed along the pier",
        "lesson": "A pause can be an important part of a message",
    },
    {
        "place": "Parrot's Tooth Cay",
        "signal": "a copper click repeated twice, followed by a low hum",
        "wrong": "Bram copied only the clicks and tied the circuit into a knot of humming wire",
        "setback": "the tide pulled the quest boat onto a sandbar before the harbor beacon could answer",
        "clue": "the low hum told them where the circuit should stop",
        "meaning": "Follow the two clicks, then stop when the hum begins",
        "repair": "they untangled the wire, marked the two clicks with shells, and stopped at the first low hum",
        "success": "the beacon answered with a green glow and opened the channel home",
        "ending": "the crew sailed beneath a green lantern while a parrot shouted their names",
        "lesson": "A signal is understood only when every part is noticed",
    },
    {
        "place": "the Reef of Seven Bells",
        "signal": "a tiny bell ringing in a pattern of one, two, and one",
        "wrong": "Bram counted every echo as a new bell and steered toward the reef",
        "setback": "the ship bumped a harmless sandbank and lost its morning tide",
        "clue": "the real circuit bell always sounded softer after the second ring",
        "meaning": "Ignore the loud echoes and follow the soft final bell",
        "repair": "they covered one ear, listened for the soft ring, and traced its wire back to the beacon box",
        "success": "the repaired circuit blinked in the one-two-one pattern",
        "ending": "the ship floated free beneath a sky full of pink sails",
        "lesson": "The loudest sound is not always the useful one",
    },
]


def _setup(world: World, params: StoryParams) -> None:
    captain = world.add(Entity(params.captain_name, "character", "captain", params.captain_name))
    doofus = world.add(Entity(params.doofus_name, "character", "doofus", params.doofus_name))
    ship = world.add(Entity("ship", "thing", "ship", params.ship_name))
    circuit = world.add(Entity("circuit", "thing", "circuit", "brass circuit"))
    beacon = world.add(Entity("beacon", "place", "lighthouse", "harbor lighthouse"))

    captain.meters["courage"] = 1.0
    captain.memes["patience"] = 0.5
    doofus.meters["helpfulness"] = 1.0
    doofus.memes["worry"] = 0.2
    ship.meters["safety"] = 1.0
    circuit.meters["charge"] = 0.2
    beacon.meters["light"] = 0.0

    world.facts.update(
        captain=captain,
        doofus=doofus,
        ship=ship,
        circuit=circuit,
        beacon=beacon,
        params=params,
    )


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        f"{params.captain_name}|{params.doofus_name}|{params.ship_name}"
    ))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    adventure = ADVENTURES[_token(params) % len(ADVENTURES)]
    captain = world.facts["captain"]
    doofus = world.facts["doofus"]
    ship = world.facts["ship"]
    circuit = world.facts["circuit"]
    beacon = world.facts["beacon"]

    repetition = Repetition(adventure["signal"])
    quest = Quest(f"repairing the lighthouse circuit at {adventure['place']}", started=True)
    world.facts.update(adventure=adventure, repetition=repetition, quest=quest)

    world.say(
        f"Captain {captain.label} sailed {ship.label} toward {adventure['place']} "
        f"with {doofus.label}, the crew's cheerful doofus, beside the brass circuit box."
    )
    world.say(
        f"The harbor lighthouse had gone dark, and a repeating signal—{adventure['signal']}—"
        "was calling for help before the rising tide closed the passage."
    )
    world.say(
        f'"I can fix it in a jiffy!" {doofus.label} cried, reaching for the switch.'
    )
    world.say(
        f'"First listen to the whole signal," {captain.label} warned. '
        f'"A pirate who hurries may repair the wrong thing."'
    )

    world.para()
    repetition.count = 3
    world.say(
        f"The signal repeated. Then it repeated again. On the third time, {doofus.label} "
        f"{adventure['wrong']}."
    )
    world.say(
        f"The mistake caused trouble: {adventure['setback']}. "
        "Their quest seemed ready to end in a soggy, gloomy failure."
    )
    quest.setbacks += 1
    ship.meters["safety"] = 0.5
    circuit.meters["charge"] = 0.0

    world.para()
    world.say(
        f"Captain {captain.label} did not scold the doofus. Instead, the captain held a lantern "
        f"near the circuit and listened again. The clue was that {adventure['clue']}."
    )
    world.say(
        f'"So the message means: {adventure["meaning"]}," {captain.label} said.'
    )
    world.say(
        f'"Then my first idea was a banana peel of an idea," {doofus.label} admitted. '
        f'"Let us try the better one together."'
    )
    world.say(
        f"Together they {adventure['repair']}. "
        "The captain watched the pattern while the doofus turned the small copper key."
    )
    repetition.understood = True
    circuit.meters["charge"] = 1.0

    world.para()
    world.say(f"The repaired circuit worked: {adventure['success']}.")
    world.say(
        f'"You were not a useless doofus," {captain.label} told {doofus.label}. '
        f'"You were a useful doofus after you listened."'
    )
    world.say(
        f'"I shall listen before leaping from now on," {doofus.label} promised.'
    )
    world.say(f"{adventure['lesson']}.")
    world.say(f"The quest ended happily: {adventure['ending']}.")

    quest.completed = True
    beacon.meters["light"] = 1.0
    ship.meters["safety"] = 1.0
    doofus.memes["worry"] = 0.0
    world.facts["adventure_index"] = _token(params) % len(ADVENTURES)
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    a = world.facts["adventure"]
    return [
        f"Write a child-friendly pirate tale about {p.captain_name}, {p.doofus_name}, and a repeating circuit signal at {a['place']}.",
        f"Tell how a doofus makes a mistake during a quest, accepts the setback, and repairs the circuit by listening carefully.",
        f"Write a pirate adventure with repetition, spoken dialogue, a bad turn, and a happy ending proven by a glowing lighthouse.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    a = world.facts["adventure"]
    return [
        QAItem(
            f"Who sailed {p.ship_name} on the quest?",
            f"Captain {p.captain_name} sailed {p.ship_name} with {p.doofus_name}, the cheerful doofus, to repair the lighthouse circuit.",
        ),
        QAItem(
            "What repeated signal did the crew hear?",
            f"They heard {a['signal']} repeating from the lighthouse circuit.",
        ),
        QAItem(
            "What mistake did the doofus make?",
            f"{p.doofus_name} {a['wrong']}.",
        ),
        QAItem(
            "What made the first part of the quest go badly?",
            f"{a['setback'].capitalize()} The crew had to accept that setback before trying a better plan.",
        ),
        QAItem(
            "What clue helped them understand the repetition?",
            f"They learned that {a['clue']}. This changed how they read the circuit's signal.",
        ),
        QAItem(
            "How did the crew repair the circuit?",
            f"They {a['repair']}. Their careful teamwork restored the lighthouse.",
        ),
        QAItem(
            "What showed that the quest ended happily?",
            f"{a['ending'].capitalize()} The repaired circuit made the lighthouse guide the harbor safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a circuit?",
            "A circuit is a path that lets electricity travel through connected parts, such as wires, switches, and lights.",
        ),
        QAItem(
            "What does repetition mean?",
            "Repetition means that something happens or is heard again in a pattern.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a journey with a special goal, such as finding, helping, or repairing something.",
        ),
    ]


ASP_RULES = r"""
confused(S) :- repeats(S), signal_problem(S).
bad_ending(S) :- confused(S), wrong_choice(S), setback(S).
happy_ending(S) :- translated_signal(S), circuit_fixed(S), beacon_lit(S).
valid_story(S) :- bad_ending(S), happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("repeats", "story1"),
        asp.fact("signal_problem", "story1"),
        asp.fact("wrong_choice", "story1"),
        asp.fact("setback", "story1"),
        asp.fact("translated_signal", "story1"),
        asp.fact("circuit_fixed", "story1"),
        asp.fact("beacon_lit", "story1"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    got = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if got == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(got))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale storyworld about a doofus, repetition, a quest, and a circuit."
    )
    parser.add_argument("--captain-name", choices=NAMES)
    parser.add_argument("--doofus-name", choices=NAMES)
    parser.add_argument("--ship-name", choices=SHIP_NAMES)
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
    captain = args.captain_name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != captain]
    doofus = args.doofus_name or rng.choice(choices)
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    if captain == doofus:
        raise StoryError("captain and doofus must have different names")
    return StoryParams(
        seed=None,
        captain_name=captain,
        doofus_name=doofus,
        ship_name=ship,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) {' '.join(bits)}"
        )
    repetition = world.facts.get("repetition")
    quest = world.facts.get("quest")
    if repetition:
        lines.append(
            f"  repetition: count={repetition.count}, understood={repetition.understood}"
        )
    if quest:
        lines.append(
            f"  quest: started={quest.started}, setbacks={quest.setbacks}, completed={quest.completed}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(captain_name="Luna", doofus_name="Bram", ship_name="the Jolly Circuit"),
    StoryParams(captain_name="Mara", doofus_name="Pip", ship_name="the Brass Minnow"),
    StoryParams(captain_name="Nell", doofus_name="Rook", ship_name="the Moonlit Gull"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base_seed + index))
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
