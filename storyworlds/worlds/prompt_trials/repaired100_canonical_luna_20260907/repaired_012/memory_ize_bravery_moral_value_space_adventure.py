#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Spacecraft:
    name: str
    location: str = "the quiet edge of space"
    danger: float = 0.0
    memory_charge: float = 0.0
    moral_value: float = 0.0
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    pilot_name: str
    companion_name: str
    ship_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Sol", "Tara", "Pip", "Aria", "Bo"]
SHIP_NAMES = ["The Starling", "The Moon Kite", "The Little Comet", "The Bright Ark"]

ARCS = [
    {
        "key": "lost_signal",
        "premise": "Luna and {companion}, aboard {ship}, carried a memory beacon through a field of sleepy stars.",
        "problem": "A broken signal made the beacon forget the route home, while a dark space current pulled the ship toward a glittering black hole.",
        "conflict": "\"We must rush past it,\" said Luna. \"We must stop and help the lost signal,\" answered {companion}. Their choice mattered because the beacon held a village's only map.",
        "turn": "Luna used the ship's memory-ize setting to save the sound of the beacon's last clear message. The recording revealed a small rescue pod hiding behind a moon.",
        "action": "\"We can be brave and careful,\" Luna said. {companion} guided the ship beside the moon while Luna followed the remembered signal instead of the dangerous current.",
        "resolution": "They rescued the pod and restored the beacon's route. Their bravery protected strangers, and their moral value was clear: helping someone mattered more than taking the quick path.",
        "ending": "The beacon glowed beside the rescued travelers, and {ship} sailed home beneath a trail of remembered stars.",
        "problem_fact": "a broken beacon forgot its route while a dark current pulled the ship toward a black hole",
        "clue_fact": "the memory-ize setting saved the beacon's last clear message",
        "action_fact": "they followed the remembered message and rescued a hidden pod",
        "outcome_fact": "the beacon's route was restored and the travelers were safe",
    },
    {
        "key": "crystal_gate",
        "premise": "On {ship}, Luna and {companion} flew toward a crystal gate that opened only for a truthful heart.",
        "problem": "The gate began to close when a frightened space fox became trapped on the wrong side, and the ship had only one safe chance to pass.",
        "conflict": "\"We should leave before the gate shuts,\" said Luna. \"The fox needs us,\" said {companion}. The easy choice promised safety, but the kind choice required bravery.",
        "turn": "Luna memory-ized the fox's soft clicking call. The saved sound showed that the fox knew a hidden path through the crystal dust.",
        "action": "\"We will not leave it alone,\" Luna said. {companion} flew slowly after the remembered call while Luna kept the ship's lights bright.",
        "resolution": "The fox led them through a side opening, and the crystal gate widened for all three travelers. Their moral value was stronger than fear, and their bravery made room for another life.",
        "ending": "The space fox curled beside the warm engine as the crystal gate shone like a friendly window behind {ship}.",
        "problem_fact": "a closing crystal gate trapped a frightened space fox",
        "clue_fact": "memory-izing the fox's call revealed a hidden route",
        "action_fact": "they followed the call and guided the fox through the side opening",
        "outcome_fact": "the fox was safe and the gate opened for everyone",
    },
    {
        "key": "silent_planet",
        "premise": "Luna and {companion} landed {ship} on a silent planet to deliver water seeds to a thirsty garden.",
        "problem": "Their map vanished from the screen, and a dust storm covered the only road back to the ship.",
        "conflict": "\"We should keep the seeds and save ourselves,\" whispered Luna. \"The garden children are waiting,\" said {companion}. Neither wanted to waste the precious cargo.",
        "turn": "Luna memory-ized the garden keeper's directions before the storm grew loud. The saved memory included three bell stones beside a safe valley.",
        "action": "\"One seed for each bell,\" Luna said. They shared the water seeds with the garden and followed the remembered stones through the dust.",
        "resolution": "The garden drank, the bell stones led them home, and the children waved from the shelter. Their moral value was shown by sharing what could have been kept for themselves.",
        "ending": "Tiny green leaves rose from the red soil as {ship} lifted into a clear violet sky.",
        "problem_fact": "a dust storm erased the route from a thirsty planet",
        "clue_fact": "memory-izing the keeper's directions preserved the safe valley route",
        "action_fact": "they shared the water seeds and followed the remembered bell stones",
        "outcome_fact": "the garden received water and the crew returned safely",
    },
    {
        "key": "shadow_moon",
        "premise": "{ship} crossed the shadow of a moon while Luna and {companion} searched for a drifting school satellite.",
        "problem": "The satellite's lights were out, and a field of cold rocks spun between it and the ship.",
        "conflict": "\"We cannot risk the hull,\" said {companion}. Luna looked at the dark satellite. \"Then we will find the safest brave step.\"",
        "turn": "Luna memory-ized the rhythm of the satellite's tiny blinking emergency lamp. The rhythm showed that the rocks moved in a repeating loop.",
        "action": "\"Now, then wait, then now again,\" Luna called. {companion} steered between the rocks while Luna matched the remembered flashes.",
        "resolution": "They reached the satellite without a scratch and restarted its lights. Their bravery was not reckless; it used patience and care to protect the stranded students inside.",
        "ending": "A whole school of lights twinkled around the moon, and {ship} glided home with grateful voices on the radio.",
        "problem_fact": "a dark school satellite drifted behind a field of spinning rocks",
        "clue_fact": "the memory-ized emergency rhythm revealed the rocks' repeating motion",
        "action_fact": "they timed their flight between the rocks",
        "outcome_fact": "the satellite lights returned and its students were safe",
    },
]


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    text = "|".join((params.pilot_name, params.companion_name, params.ship_name))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


class World:
    def __init__(self, ship: Spacecraft) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    if params.pilot_name == params.companion_name:
        raise StoryError("The pilot and companion must have different names.")
    if params.ship_name not in SHIP_NAMES:
        raise StoryError("That spacecraft is not in the small space registry.")

    ship = Spacecraft(params.ship_name, danger=1.0, memory_charge=0.0, moral_value=0.0)
    world = World(ship)
    pilot = world.add(Entity(params.pilot_name, kind="character", type="pilot"))
    companion = world.add(Entity(params.companion_name, kind="character", type="companion"))
    beacon = world.add(Entity("memory_beacon", type="memory beacon", label="memory-ize beacon"))

    rng = _rng(params)
    index = (params.seed if params.seed is not None else rng.randrange(len(ARCS))) % len(ARCS)
    arc = ARCS[index]
    for number, key in enumerate(("premise", "problem", "conflict", "turn", "action", "resolution", "ending")):
        if number:
            world.para()
        text = arc[key].format(
            companion=companion.id,
            ship=ship.name,
        )
        world.say(text)

    pilot.meters["bravery"] = 1.0
    companion.meters["bravery"] = 1.0
    pilot.memes["moral_value"] = 1.0
    companion.memes["moral_value"] = 1.0
    beacon.meters["memory_charge"] = 1.0
    ship.danger = 0.0
    ship.memory_charge = 1.0
    ship.moral_value = 1.0
    ship.location = "the safe road home"
    ship.facts = {
        "pilot": pilot,
        "companion": companion,
        "beacon": beacon,
        "arc": arc,
        "problem_event": arc["problem"],
        "turn_event": arc["turn"],
        "action_event": arc["action"],
        "resolution_event": arc["resolution"],
    }
    return world


def generate_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly Space Adventure about memory-ize, Bravery, and Moral Value.",
        f"Tell a space story about {world.ship.facts['pilot'].id} and {world.ship.facts['companion'].id} helping someone even when the route is dangerous.",
        "Write a short adventure where saving a memory reveals the safe and kind choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.ship.facts
    pilot = f["pilot"].id
    companion = f["companion"].id
    return [
        QAItem(
            f"Who traveled on {world.ship.name}?",
            f"{pilot} and {companion} traveled together on {world.ship.name}.",
        ),
        QAItem(
            "What danger did they face?",
            f["problem_event"],
        ),
        QAItem(
            "How did memory-ize help them?",
            f["turn_event"],
        ),
        QAItem(
            f"How did {pilot} and {companion} show Bravery and Moral Value?",
            f"{f['action_event']} {f['resolution_event']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does memory-ize mean in this story?",
            "Memory-ize means to save an important sound, sight, or direction so it can be remembered and used later.",
        ),
        QAItem(
            "What is bravery?",
            "Bravery is choosing a careful, helpful action even when you feel afraid.",
        ),
        QAItem(
            "What is moral value?",
            "Moral value is the importance of choosing what is kind, fair, and helpful to others.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:16} ({entity.type:14}) meters={entity.meters} memes={entity.memes}"
        )
    lines.extend(
        [
            f"  ship.location={world.ship.location}",
            f"  ship.danger={world.ship.danger}",
            f"  ship.memory_charge={world.ship.memory_charge}",
            f"  ship.moral_value={world.ship.moral_value}",
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :- feature(memory_ize), feature(bravery), feature(moral_value),
               outcome(safe), choice(helpful).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("feature", "memory_ize"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "moral_value"),
            asp.fact("outcome", "safe"),
            asp.fact("choice", "helpful"),
            asp.fact("style", "space_adventure"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(symbol.name == "valid_story" for symbol in model):
        print("OK: ASP twin recognizes memory-ize, bravery, and moral value.")
        return 0
    print("MISMATCH: ASP twin rejected the story pattern.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Space Adventure world of memory-ize, Bravery, and Moral Value.")
    parser.add_argument("--pilot-name")
    parser.add_argument("--companion-name")
    parser.add_argument("--ship-name", choices=SHIP_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pilot = args.pilot_name or rng.choice(NAMES)
    companion = args.companion_name or rng.choice([name for name in NAMES if name != pilot])
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(pilot, companion, ship)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible Space Adventure pattern: memory-ize + Bravery + Moral Value")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams("Luna", "Milo", "The Starling")),
            generate(StoryParams("Nia", "Sol", "The Moon Kite")),
            generate(StoryParams("Tara", "Pip", "The Bright Ark")),
            generate(StoryParams("Aria", "Bo", "The Little Comet")),
        ]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
