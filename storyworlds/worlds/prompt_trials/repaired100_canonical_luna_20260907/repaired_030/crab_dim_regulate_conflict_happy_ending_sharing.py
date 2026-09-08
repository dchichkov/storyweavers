#!/usr/bin/env python3
"""
A tiny pirate storyworld about Crab-Dim, a lantern crab who learns to regulate
a quarrel by sharing the treasure light.
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
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class StoryParams:
    captain: str
    crab: str
    helper: str
    reef: str
    conflict: str
    sharing: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Conflict:
    warning: str
    quarrel: str
    mistake: str
    danger: str
    repair: str
    result: str


@dataclass(frozen=True)
class Sharing:
    object_name: str
    offer: str
    lesson: str


@dataclass(frozen=True)
class HappyEnding:
    image: str
    final_line: str


NAMES = ["Luna", "Mara", "Pip", "Coral", "Nix", "Tide", "Bram", "Sail"]
HELPERS = ["the parrot", "the old deckhand", "the cabin boy"]
REEFS = ["Moonlit Reef", "Whispering Shoal", "Bluefin Bay"]

CONFLICTS = {
    "lantern_tug": Conflict(
        warning="a silver fog rolled over the deck",
        quarrel="who should hold the only glow-shell",
        mistake="They tugged at the shell until its warm light flickered",
        danger="Without the glow-shell, the pirate ship could drift onto the black rocks",
        repair="stop pulling, breathe slowly, and place the glow-shell between them",
        result="the shell shone steadily again and showed the safe channel",
    ),
    "map_rip": Conflict(
        warning="a strong wind snatched the treasure map from the captain's table",
        quarrel="who had been watching the map",
        mistake="They blamed each other while the map flapped toward the sea",
        danger="The ship could lose its way among the reefs",
        repair="hold the map flat together and mark the safe route with a blue crayon",
        result="the map was saved and the blue route led them home",
    ),
    "bell_race": Conflict(
        warning="the warning bell began to ring in the night",
        quarrel="who should be first to reach the bell rope",
        mistake="They raced so fiercely that they crossed the ropes and made the bell silent",
        danger="The crew could not hear that shallow water lay ahead",
        repair="untangle the ropes, let one sailor ring, and listen for the echo",
        result="the bell rang clearly and the crew turned away from danger",
    ),
}

SHARINGS = {
    "glow_shell": Sharing(
        object_name="the glow-shell",
        offer="share the glow-shell, with one friend carrying it while the other reads the water",
        lesson="a light grows more useful when everyone can use it",
    ),
    "coconut": Sharing(
        object_name="a sweet coconut",
        offer="split the coconut into equal cups before taking a sip",
        lesson="a small treat feels bigger when it is shared fairly",
    ),
    "compass": Sharing(
        object_name="the brass compass",
        offer="take turns holding the brass compass and calling the next turn",
        lesson="shared responsibility keeps a voyage steady",
    ),
}

ENDINGS = {
    "moon_cove": HappyEnding(
        image="At dawn, the crew reached a quiet cove where moonlight rested on the calm water",
        final_line="Crab-Dim curled happily beside the shared lantern, and every sailor knew there was room for kindness on a pirate ship",
    ),
    "bright_deck": HappyEnding(
        image="By sunrise, the whole deck glittered with drops of sea spray and friendly smiles",
        final_line="The crew cheered because the treasure they shared was brighter than any treasure they could hoard",
    ),
    "reef_feast": HappyEnding(
        image="That evening, the pirates spread a warm feast beneath the stars",
        final_line="Crab-Dim passed every cup around until no sailor was left thirsty or cross",
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pirate tale about Crab-Dim.")
    parser.add_argument("--captain")
    parser.add_argument("--crab")
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--reef", choices=REEFS)
    parser.add_argument("--conflict", choices=CONFLICTS)
    parser.add_argument("--sharing", choices=SHARINGS)
    parser.add_argument("--ending", choices=ENDINGS)
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
    captain = args.captain or rng.choice(NAMES)
    crab = args.crab or "Crab-Dim"
    if captain == crab:
        raise StoryError("The captain and Crab-Dim need different names.")
    return StoryParams(
        captain=captain,
        crab=crab,
        helper=args.helper or rng.choice(HELPERS),
        reef=args.reef or rng.choice(REEFS),
        conflict=args.conflict or rng.choice(tuple(CONFLICTS)),
        sharing=args.sharing or rng.choice(tuple(SHARINGS)),
        ending=args.ending or rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    conflict = CONFLICTS[params.conflict]
    sharing = SHARINGS[params.sharing]
    ending = ENDINGS[params.ending]

    world = World(f"the pirate ship near {params.reef}")
    captain = world.add(Entity(params.captain, "captain", params.captain, "deck"))
    crab = world.add(Entity("crab_dim", "crab", params.crab, "deck"))
    helper = world.add(Entity("helper", "helper", params.helper, "mast"))
    shell = world.add(Entity("shared_light", "treasure", sharing.object_name, "captain's table"))

    world.facts.update(
        captain=captain,
        crab=crab,
        helper=helper,
        shell=shell,
        conflict=conflict,
        sharing=sharing,
        ending=ending,
        regulated=False,
        shared=False,
    )

    world.say(
        f"Once, on a pirate ship sailing near {params.reef}, Captain {params.captain} "
        f"trusted {params.crab}, a small crab with a bright shell and a very quick temper."
    )
    world.say(
        f"{params.helper.capitalize()} kept watch while {params.crab} helped guide the ship through "
        f"the dark water."
    )
    world.para()

    crab.meters["tension"] = 1.0
    captain.meters["tension"] = 1.0
    world.say(f"Then {conflict.warning}.")
    world.say(f"The captain and {params.crab} argued about {conflict.quarrel}.")
    world.say(f'"Give it here!" cried Captain {params.captain}. "I can steer us safely."')
    world.say(f'"Wait!" snapped {params.crab}. "I can see the reef better from down here."')
    world.say(f"{conflict.mistake}.")
    world.say(f"{conflict.danger}.")

    world.para()
    crab.memes["anger"] = 1.0
    captain.memes["anger"] = 1.0
    world.say(f"{params.helper.capitalize()} raised a wing and called, \"Both of you, pause!\"")
    world.say(
        f"{params.crab} took one slow breath, counted three waves, and decided to regulate "
        f"the hot feeling in {params.crab}'s claws."
    )
    world.say(f'"I was afraid," admitted {params.crab}. "But pulling will not help us."')
    world.say(
        f'"You are right," said Captain {params.captain}. "Let us {sharing.offer}.'
        f'"'
    )
    world.facts["regulated"] = True
    crab.memes["anger"] = 0.0
    captain.memes["anger"] = 0.0
    crab.memes["calm"] = 1.0
    captain.memes["trust"] = 1.0
    world.facts["shared"] = True

    world.para()
    world.say(f"Together, they chose to {conflict.repair}.")
    world.say(f"{conflict.result.capitalize()}.")
    world.say(
        f"{params.crab} carried the {sharing.object_name} for a while, then passed it to "
        f"Captain {params.captain}; each gave the other a clear turn."
    )
    world.say(
        f"The crew learned that {sharing.lesson}, and the ship sailed safely beyond the reef."
    )

    world.para()
    world.say(f"{ending.image}.")
    world.say(ending.final_line)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    conflict: Conflict = world.facts["conflict"]  # type: ignore[assignment]
    return [
        f"Write a child-friendly pirate tale about {world.facts['crab'].label} learning to regulate a quarrel.",
        f"Show a conflict over {world.facts['sharing'].object_name} that is healed by sharing.",
        f"End with a happy image near {world.facts['ending'].image.lower()}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    crab: Entity = world.facts["crab"]  # type: ignore[assignment]
    captain: Entity = world.facts["captain"]  # type: ignore[assignment]
    conflict: Conflict = world.facts["conflict"]  # type: ignore[assignment]
    sharing: Sharing = world.facts["sharing"]  # type: ignore[assignment]
    return [
        QAItem(
            f"Who was Crab-Dim arguing with?",
            f"{crab.label} was arguing with Captain {captain.label} on the pirate ship near {world.setting.split(' near ', 1)[1]}.",
        ),
        QAItem(
            "What danger caused the conflict?",
            f"{conflict.danger}. The danger made the sailors realize they needed to work together.",
        ),
        QAItem(
            "How did Crab-Dim regulate the angry feeling?",
            f"Crab-Dim paused, took a slow breath, counted three waves, and stopped pulling before choosing a calmer plan.",
        ),
        QAItem(
            "How did sharing solve the problem?",
            f"They decided to {sharing.offer}. Taking turns restored trust, and {conflict.result}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does it mean to regulate a strong feeling?",
            "To regulate a strong feeling means to pause and use a safe action, such as breathing or counting, so the feeling does not control your behavior.",
        ),
        QAItem(
            "Why can sharing help during a conflict?",
            "Sharing can help because each person gets a fair turn and the group can use an important object or resource together.",
        ),
        QAItem(
            "What is a pirate ship?",
            "A pirate ship is a sailing vessel used by a pirate crew to travel across the sea.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} kind={entity.kind:8} location={entity.location:18} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  regulated={world.facts.get('regulated')}")
    lines.append(f"  shared={world.facts.get('shared')}")
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(pirate_ship).
feature(conflict).
feature(happy_ending).
feature(sharing).
seed_word(crab_dim).
seed_word(regulate).
valid_story(pirate_ship, conflict, happy_ending, sharing).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "pirate_ship"),
            asp.fact("feature", "conflict"),
            asp.fact("feature", "happy_ending"),
            asp.fact("feature", "sharing"),
            asp.fact("seed_word", "crab_dim"),
            asp.fact("seed_word", "regulate"),
        ]
    )


def asp_program(show: str = "#show valid_story/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_story"))


def asp_verify() -> int:
    expected = {("pirate_ship", "conflict", "happy_ending", "sharing")}
    actual = asp_valid_stories()
    if expected != actual:
        print(f"ASP mismatch: expected {expected}, got {actual}")
        return 1
    sample = generate(
        StoryParams(
            captain="Luna",
            crab="Crab-Dim",
            helper="the parrot",
            reef="Moonlit Reef",
            conflict="lantern_tug",
            sharing="glow_shell",
            ending="moon_cove",
        )
    )
    required = ["Crab-Dim", "regulate", "conflict", "shared"]
    if "Crab-Dim" not in sample.story or "regulate" not in sample.story:
        print("Generated story failed required seed-word check.")
        return 1
    if not sample.world or not sample.world.facts.get("shared"):
        print("Generated story failed sharing check.")
        return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def show_qa_item(item: QAItem) -> str:
    return f"Q: {item.question}\nA: {item.answer}"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        for prompt in sample.prompts:
            print(f"\n[Prompt] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print(f"\n{show_qa_item(item)}")


CURATED = [
    StoryParams("Luna", "Crab-Dim", "the parrot", "Moonlit Reef", "lantern_tug", "glow_shell", "moon_cove"),
    StoryParams("Mara", "Crab-Dim", "the old deckhand", "Whispering Shoal", "map_rip", "compass", "bright_deck"),
    StoryParams("Pip", "Crab-Dim", "the cabin boy", "Bluefin Bay", "bell_race", "coconut", "reef_feast"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print("Compatible ASP stories:")
        for item in sorted(asp_valid_stories()):
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for offset in range(max(1, args.n)):
            rng = random.Random(base_seed + offset)
            params = resolve_params(args, rng)
            params.seed = base_seed + offset
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples, 1):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index}" if len(samples) > 1 else "",
        )
        if index < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
