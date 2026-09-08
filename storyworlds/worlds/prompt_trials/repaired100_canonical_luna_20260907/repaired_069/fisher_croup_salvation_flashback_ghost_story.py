#!/usr/bin/env python3
"""A gentle ghost story about a fisher, a cough, and a remembered salvation."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    fisher: str = "Mara"
    companion: str = "Eli"
    ghost: str = "Old Nessa"
    setting: str = "the moonlit inlet"
    incident: int = 0
    opening: int = 0
    memory: int = 0
    warning: int = 0
    ending: int = 0


FISHERS = ["Mara", "Jon", "Lina", "Tomas", "Bea"]
COMPANIONS = ["Eli", "Ruth", "Pax", "Niko", "June"]
GHOSTS = ["Old Nessa", "Silas Reed", "Aunt Wren", "Captain Vale"]
SETTINGS = [
    "the moonlit inlet",
    "the blackwater pier",
    "the quiet river bend",
    "the salt-marsh channel",
]
INCIDENTS = [
    {
        "title": "the lantern boat",
        "problem": "A small boat drifted loose while a child inside coughed with a harsh croupy rattle.",
        "clue": "A pale handprint appeared on the wet gunwale, pointing toward the old bell rope.",
        "action": "Mara threw the rope around a piling, and Eli pulled while the ghost rang the bell from the mist.",
        "result": "The boat slid safely back to shore, where warm blankets and a doctor were waiting.",
        "lesson": "A remembered kindness can become a light for someone in danger.",
        "object": "bell rope",
    },
    {
        "title": "the fog net",
        "problem": "Fog hid a fishing skiff, and its coughing crew could not find the channel markers.",
        "clue": "The ghost's reflection showed three bright ripples leading around the sandbar.",
        "action": "Mara followed the ripples, while Eli beat a slow signal on an empty bait tin.",
        "result": "The skiff heard the signal and reached the sheltered dock before the tide turned.",
        "lesson": "Careful listening can guide people through frightening confusion.",
        "object": "bait tin",
    },
    {
        "title": "the silver hook",
        "problem": "A fisher's hook caught in a storm line as a feverish deckhand struggled to breathe through croup.",
        "clue": "The ghost pointed to a loose knot beneath the rail instead of the tangled hook above.",
        "action": "Mara loosened the hidden knot, and Eli lifted the line clear without jerking it.",
        "result": "The deckhand breathed more easily, and the boat returned before the storm arrived.",
        "lesson": "Finding the real cause is kinder and safer than pulling harder.",
        "object": "storm line",
    },
]

OPENINGS = [
    "At midnight, {fisher} the fisher mended a net beside {setting}.",
    "The tide was low when {fisher} carried a lantern to {setting}.",
    "Everyone in the harbor avoided {setting} after dark, but {fisher} still worked there.",
    "Rain whispered over {setting} as {fisher} checked the boats.",
]

MEMORIES = [
    "Then the fog folded backward in {fisher}'s mind, and a flashback returned: years ago, the same ghost had pulled {fisher} from a freezing current.",
    "For one breath, {fisher} saw a flashback of childhood waves and the ghost's steady lantern guiding a lost family home.",
    "The mist became a flashback. {fisher} remembered being small, sick, and frightened while a pale stranger carried medicine across the flooded pier.",
    "A flashback shimmered on the water: the ghost had once chosen salvation over sleep and kept watch until every boat was safe.",
]

WARNINGS = [
    "'Do not chase the loudest fear,' whispered the ghost. 'Look for the quiet rope.'",
    "'Coughs need warm air and grown-up help,' said the ghost. 'Your brave work is to bring both.'",
    "'Salvation is often a hand offered in time,' the ghost said. 'Offer yours carefully.'",
    "'Remember what saved you,' breathed the ghost. 'Then make the path safe for another.'",
]

ENDINGS = [
    "At dawn, the ghost faded, leaving one dry lantern glowing on the pier.",
    "When the sun rose, a silver fish leaped where the ghost had stood.",
    "The mist opened like a curtain, and the old bell gave one gentle ring.",
    "By morning, the rescued boat rested beside a row of warm, shining windows.",
]

ASP_RULES = r"""
#show fisher/1.
#show salvation/1.
#show remembers/2.

fisher(F) :- chosen_fisher(F).
salvation(S) :- rescued(S).
remembers(F, E) :- fisher(F), ghost(E), has_memory(F, E).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("chosen_fisher", "fisher"),
            asp.fact("rescued", "salvation"),
            asp.fact("ghost", "old_ghost"),
            asp.fact("has_memory", "fisher", "old_ghost"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ghost story about a fisher, croup, and salvation.")
    parser.add_argument("--fisher", choices=FISHERS)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--ghost", choices=GHOSTS)
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--incident", type=int, choices=range(len(INCIDENTS)))
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
        seed=args.seed,
        fisher=args.fisher or rng.choice(FISHERS),
        companion=args.companion or rng.choice(COMPANIONS),
        ghost=args.ghost or rng.choice(GHOSTS),
        setting=args.setting or rng.choice(SETTINGS),
        incident=args.incident if args.incident is not None else rng.randrange(len(INCIDENTS)),
        opening=rng.randrange(len(OPENINGS)),
        memory=rng.randrange(len(MEMORIES)),
        warning=rng.randrange(len(WARNINGS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.fisher == params.companion:
        raise StoryError("The fisher and companion must have different names.")
    if not params.setting:
        raise StoryError("A setting is required for the ghost story.")

    world = World()
    fisher = world.add(Entity(params.fisher, "fisher", params.fisher))
    companion = world.add(Entity(params.companion, "companion", params.companion))
    ghost = world.add(Entity("ghost", "ghost", params.ghost))
    boat = world.add(Entity("boat", "boat", "the rescue boat"))

    fisher.meters["distance_to_shore"] = 4.0
    companion.meters["warmth"] = 0.2
    companion.memes["fear"] = 1.0
    ghost.memes["watchfulness"] = 1.0
    boat.meters["drift"] = 1.0

    incident = INCIDENTS[params.incident % len(INCIDENTS)]

    def fill(text: str) -> str:
        return text.format(
            fisher=params.fisher,
            companion=params.companion,
            ghost=params.ghost,
            setting=params.setting,
        )

    world.say(fill(OPENINGS[params.opening % len(OPENINGS)]))
    world.say(fill(incident["problem"]))
    world.say(
        f"{params.companion} called, '{params.fisher}, I can hear the croup in the boat. "
        "Please bring us in gently!'"
    )
    world.say(
        f"{params.fisher} answered, 'I hear you. Keep low and breathe slowly while I find the safest line.'"
    )
    world.say(fill(MEMORIES[params.memory % len(MEMORIES)]))
    world.say(fill(WARNINGS[params.warning % len(WARNINGS)]))
    world.say(f"{params.ghost} appeared beside the water, pale but calm.")
    world.say(fill(incident["clue"]))
    world.say(fill(incident["action"]))
    world.say(fill(incident["result"]))

    boat.meters["drift"] = 0.0
    companion.meters["warmth"] = 1.0
    companion.memes["fear"] = 0.2
    fisher.memes["hope"] = 1.0
    ghost.memes["watchfulness"] = 0.0

    world.say(
        f"The harbor doctor checked {params.companion}'s breathing, and the croup eased beside the warm stove."
    )
    world.say(
        f"{params.companion} asked, 'Was that ghost real?' {params.fisher} replied, "
        f"'Real enough to help us remember salvation.'"
    )
    world.say(fill(incident["lesson"]))
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    world.facts.update(
        fisher=fisher,
        companion=companion,
        ghost=ghost,
        boat=boat,
        incident=incident,
        croup=True,
        salvation=True,
        flashback=True,
        solved_object=incident["object"],
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    incident = f["incident"]
    fisher = f["fisher"]
    return [
        f"Write a gentle ghost story about {fisher.id}, a fisher who remembers salvation during {incident['title']}.",
        "Tell a child-friendly story involving croup, a helpful ghost, a flashback, and a safe rescue.",
        f"Write a misty harbor tale ending with an image of the {incident['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fisher = f["fisher"]
    companion = f["companion"]
    ghost = f["ghost"]
    incident = f["incident"]
    return [
        QAItem(
            question=f"What danger did {fisher.id} face?",
            answer=f"{fisher.id} had to bring help to a boat in danger while {companion.id} struggled with a croupy cough.",
        ),
        QAItem(
            question="What did the flashback help the fisher remember?",
            answer=f"The flashback reminded {fisher.id} that {ghost.label} had once helped save someone, so the fisher trusted careful kindness instead of panic.",
        ),
        QAItem(
            question=f"What clue helped solve {incident['title']}?",
            answer=incident["clue"],
        ),
        QAItem(
            question=f"How was {companion.id} helped?",
            answer=f"{companion.id} was brought safely to shore, kept warm, and checked by a harbor doctor for the croup.",
        ),
        QAItem(
            question="What did salvation mean in the story?",
            answer="Salvation meant being brought out of danger through timely help, careful choices, and kindness.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fisher?",
            answer="A fisher is a person who catches or works with fish, often from a river, lake, or sea.",
        ),
        QAItem(
            question="What is croup?",
            answer="Croup is an illness that can cause a barking cough and noisy breathing, especially in children. A trusted adult or medical professional should help someone who is having trouble breathing.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a part of a story that briefly returns to an earlier event so the reader can understand the present.",
        ),
        QAItem(
            question="What does salvation mean?",
            answer="Salvation means being saved from danger or serious trouble.",
        ),
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
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts)}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show fisher/1.\n#show salvation/1.\n#show remembers/2."))
    expected = {
        "fisher": {("fisher",)},
        "salvation": {("salvation",)},
        "remembers": {("fisher", "old_ghost")},
    }
    for predicate, facts in expected.items():
        actual = set(asp.atoms(model, predicate))
        if actual != facts:
            print(f"MISMATCH for {predicate}: expected {sorted(facts)}, got {sorted(actual)}")
            return 1
    sample = generate(StoryParams())
    if not sample.story or "croup" not in sample.story.lower():
        print("Generated story verification failed.")
        return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


def asp_valid() -> dict[str, list[tuple]]:
    import asp
    model = asp.one_model(asp_program("#show fisher/1.\n#show salvation/1.\n#show remembers/2."))
    return {
        name: sorted(set(asp.atoms(model, name)))
        for name in ("fisher", "salvation", "remembers")
    }


CURATED = [
    StoryParams(fisher="Mara", companion="Eli", ghost="Old Nessa", setting="the moonlit inlet", incident=0),
    StoryParams(fisher="Jon", companion="Ruth", ghost="Silas Reed", setting="the blackwater pier", incident=1, opening=2, memory=1, warning=2, ending=1),
    StoryParams(fisher="Lina", companion="Pax", ghost="Captain Vale", setting="the salt-marsh channel", incident=2, opening=3, memory=3, warning=0, ending=2),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program("#show fisher/1.\n#show salvation/1.\n#show remembers/2."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for name, facts in asp_valid().items():
            print(f"{name}:")
            for fact in facts:
                print(f"  {fact}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + attempt))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.fisher}: ghost story"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
