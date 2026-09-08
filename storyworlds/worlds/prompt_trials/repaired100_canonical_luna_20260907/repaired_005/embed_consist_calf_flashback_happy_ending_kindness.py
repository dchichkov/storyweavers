#!/usr/bin/env python3
"""
A gentle mythic story world about Luna, a lost calf, and kindness remembered.

Seed tale:
---
Luna found a small calf shivering beside an old stone bridge. A blue thread was
embedded in its bell, and Luna remembered her grandmother's lesson: a kind deed
can become a light inside the heart. She followed the thread to a shepherd who
had lost the calf in a storm. Luna returned the calf, and the shepherd shared
warm bread with her. From that day on, the village kept a blue thread in every
bell, so nobody forgot to be kind.
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class StoryParams:
    name: str = "Luna"
    scenario: str = "blue_bell"
    place: str = "bridge"
    memory: int = 0
    clue: int = 0
    kindness: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Tale:
    id: str
    lost_reason: str
    calf_name: str
    clue: str
    journey: str
    memory: str
    lesson: str
    exchange: str
    resolution: str
    endings: tuple[str, ...]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "bridge": Setting(
        "the Moonstone Bridge",
        "a silver river, lavender hills, and old stones warmed by the sun",
    ),
    "meadow": Setting(
        "the Star Meadow",
        "soft grass, yellow flowers, and a hill where the stars seemed near",
    ),
    "village": Setting(
        "the village of Bellflower",
        "round cottages, blue doors, and a little square beneath an elm tree",
    ),
}

TALES = {
    "blue_bell": Tale(
        id="blue_bell",
        lost_reason="a sudden storm had scattered the shepherd's small herd",
        calf_name="Pip",
        clue="a blue thread embedded in the calf's brass bell",
        journey="followed the blue thread through wet grass and beneath the willow trees",
        memory="When I was small, Grandmother told me that kindness leaves a bright thread behind it",
        lesson="a kind heart can notice a trail that hurried eyes miss",
        exchange="Luna asked, \"Are you looking for this little calf?\" The shepherd answered, \"I have searched since the storm began. You have brought my hope home.\"",
        resolution="the calf pressed its warm nose against the shepherd's hand, and its bell gave a grateful little ring",
        endings=(
            "The shepherd shared warm bread with Luna, and the blue thread shone in the evening light.",
            "That night, Pip slept beside the flock while Luna carried the memory of the rescue in her heart.",
            "The village children tied blue threads to their own bells so kindness would never lose its way.",
            "When the moon rose, the bridge seemed to smile, and Pip's bell rang softly beside it.",
        ),
    ),
    "silver_ribbon": Tale(
        id="silver_ribbon",
        lost_reason="a gate had swung open when the shepherd went to help an injured bird",
        calf_name="Daisy",
        clue="a silver ribbon embedded beneath the calf's bell",
        journey="followed the ribbon's glint from the orchard path to a quiet sheepfold",
        memory="My mother once said that a gentle hand can turn fear into trust",
        lesson="kindness is patient enough to wait for a frightened creature",
        exchange="Luna whispered, \"Will you come with me, little one?\" The shepherd called, \"Speak softly. That is how Daisy knows she is safe.\"",
        resolution="the calf stepped from the shadows and walked calmly back to the open gate",
        endings=(
            "The shepherd braided the silver ribbon into the gate, where it flashed like a tiny moon.",
            "Daisy joined the flock, and Luna left a handful of clover by the sheepfold.",
            "The shepherd gave Luna a warm cloak, saying that kindness should keep its helpers warm.",
            "At dawn, Daisy's bell sounded from the meadow, steady and bright.",
        ),
    ),
    "red_bead": Tale(
        id="red_bead",
        lost_reason="thick fog had hidden the path from the shepherd and his youngest animal",
        calf_name="Moss",
        clue="a red bead embedded in the calf's leather bell strap",
        journey="followed the red glimmer between the stones and across the quiet stream",
        memory="Once, Father showed me how one small lantern can guide many travelers",
        lesson="even a small kindness can become a guide in a wide and shadowy world",
        exchange="Luna said, \"I see a light on your bell.\" The shepherd replied, \"Then you have found Moss, and your careful eyes have saved my night.\"",
        resolution="the calf recognized the shepherd's call and trotted through the fog toward home",
        endings=(
            "The shepherd lit a lantern for Luna, and the red bead glowed beside its flame.",
            "Moss curled near the flock while Luna watched the fog lift from the valley.",
            "Every family in the village placed a little lantern by the road for travelers.",
            "When morning came, the calf's bell chimed like a red star returning home.",
        ),
    ),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mythic story world about Luna, a lost calf, and kindness."
    )
    parser.add_argument("--name", choices=["Luna", "Luna Moonchild"], default="Luna")
    parser.add_argument("--scenario", choices=sorted(TALES), default=None)
    parser.add_argument("--place", choices=sorted(SETTINGS), default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--memory", type=int, choices=range(4), default=None)
    parser.add_argument("--clue", type=int, choices=range(4), default=None)
    parser.add_argument("--kindness", type=int, choices=range(4), default=None)
    parser.add_argument("--ending", type=int, choices=range(4), default=None)
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
    return StoryParams(
        name=args.name,
        scenario=args.scenario or rng.choice(sorted(TALES)),
        place=args.place or rng.choice(sorted(SETTINGS)),
        memory=args.memory if args.memory is not None else rng.randrange(4),
        clue=args.clue if args.clue is not None else rng.randrange(4),
        kindness=args.kindness if args.kindness is not None else rng.randrange(4),
        ending=args.ending if args.ending is not None else rng.randrange(4),
        seed=args.seed,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("Luna needs a name.")
    if params.name not in {"Luna", "Luna Moonchild"}:
        raise StoryError("This myth belongs to Luna.")
    if params.scenario not in TALES:
        raise StoryError("Unknown calf tale.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if not 0 <= params.memory < 4:
        raise StoryError("Flashback style must be between 0 and 3.")
    if not 0 <= params.clue < 4:
        raise StoryError("Clue style must be between 0 and 3.")
    if not 0 <= params.kindness < 4:
        raise StoryError("Kindness style must be between 0 and 3.")
    if not 0 <= params.ending < 4:
        raise StoryError("Happy ending must be between 0 and 3.")


ASP_RULES = r"""
girl(luna).
creature(calf).
virtue(kindness).
instrument(flashback).
instrument(happy_ending).
object(embed).
object(consist).

tale(S) :- girl(luna), creature(calf), virtue(kindness), instrument(flashback),
           instrument(happy_ending), object(embed), object(consist), scenario(S).

scenario(blue_bell).
scenario(silver_ribbon).
scenario(red_bead).

valid_story(S) :- tale(S).
#show valid_story/1.
#show scenario/1.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("girl", "luna"),
        asp.fact("creature", "calf"),
        asp.fact("virtue", "kindness"),
        asp.fact("instrument", "flashback"),
        asp.fact("instrument", "happy_ending"),
        asp.fact("object", "embed"),
        asp.fact("object", "consist"),
    ]
    facts.extend(asp.fact("scenario", sid) for sid in TALES)
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {(sid,) for sid in TALES}
    if found == expected:
        print(f"OK: clingo matches Python registry ({len(expected)} tales).")
        return 0
    print("MISMATCH")
    print("clingo:", sorted(found))
    print("python:", sorted(expected))
    return 1


def build_world(params: StoryParams, tale: Tale, setting: Setting) -> World:
    world = World(setting)
    luna = world.add(
        Entity(
            "luna",
            kind="character",
            label=params.name,
            type="girl",
            memes={"kindness": 0.4, "wonder": 0.5, "worry": 0.2},
        )
    )
    calf = world.add(
        Entity(
            "calf",
            kind="animal",
            label=tale.calf_name,
            type="calf",
            meters={"warmth": 0.2, "safety": 0.2, "trust": 0.2},
        )
    )
    shepherd = world.add(
        Entity(
            "shepherd",
            kind="character",
            label="the shepherd",
            type="person",
            memes={"worry": 0.8, "hope": 0.2},
        )
    )
    bridge = world.add(
        Entity(
            "place",
            label=setting.place,
            type="place",
            meters={"visibility": 0.6, "safety": 0.5, "belonging": 0.3},
        )
    )
    bell = world.add(
        Entity(
            "bell",
            label="the little bell",
            type="bell",
            meters={"sound": 0.7, "clue_strength": 0.8},
            memes={"memory": 0.4},
        )
    )

    world.say(f"{params.name} lived near {setting.place}, where {setting.detail}.")
    world.say(f"People said {params.name} had a heart that could hear small troubles.")
    world.para()

    world.say(f"After {tale.lost_reason}, {params.name} heard a faint bell beside the path.")
    world.say(
        f"There stood a frightened calf, its knees trembling and its eyes bright with rain."
    )
    calf.meters["warmth"] = 0.1
    calf.meters["safety"] = 0.1
    luna.memes["worry"] += 0.5

    memories = (
        tale.memory + " That old memory returned as clearly as a song.",
        "Long ago, on another rainy day, " + tale.memory.lower() + ".",
        "For a moment, the river carried " + tale.memory.lower() + " back to her.",
        "The sight of the shivering calf opened a door in her memory: " + tale.memory.lower() + ".",
    )
    world.say(memories[params.memory])
    world.say(f"That was the flashback {params.name} needed: {tale.lesson}.")
    world.para()

    clues = (
        f"She bent close and saw {tale.clue}.",
        f"When the calf moved, {tale.clue} caught one pale ray of light.",
        f"She brushed away a leaf and discovered that {tale.clue}.",
        f"The bell gave a tiny sound, and {tale.clue} showed her a true path.",
    )
    world.say(clues[params.clue])
    world.say(f"{params.name} offered a warm hand and began to {tale.journey}.")
    world.say(
        f'"Come slowly," {params.name} said. "I will not leave you here." '
        f'The calf answered with a soft "Moo," and took one careful step.'
    )
    calf.meters["trust"] += 0.5
    calf.meters["safety"] += 0.3
    luna.memes["kindness"] += 0.4
    world.para()

    kindness_actions = (
        f"She covered the calf with her wool scarf and shared the last of her apple.",
        f"She walked at the calf's pace, stopping whenever its legs began to shake.",
        f"She cleared the thorny path with both hands before asking the calf to follow.",
        f"She sang a quiet tune so the calf could hear a friendly voice through the rain.",
    )
    world.say(kindness_actions[params.kindness])
    world.say(f"The blue trail led them at last to the shepherd.")
    world.say(tale.exchange)
    shepherd.memes["worry"] = 0.1
    shepherd.memes["hope"] = 1.0
    calf.meters["safety"] = 1.0
    calf.meters["warmth"] = 0.9
    calf.meters["trust"] = 1.0
    bridge.meters["belonging"] = 1.0
    bell.memes["memory"] = 1.0
    luna.memes["relief"] = 1.0
    luna.memes["joy"] = 0.9
    world.para()

    world.say(f"Then {tale.resolution}.")
    world.say(tale.endings[params.ending])
    world.say(
        f"From that day forward, the people of {setting.place} remembered that kindness can "
        "begin as a small thread and consist of many brave, gentle choices."
    )

    world.facts.update(
        luna=luna,
        calf=calf,
        shepherd=shepherd,
        place=bridge,
        bell=bell,
        tale=tale,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    tale: Tale = world.facts["tale"]
    setting: Setting = world.facts["setting"]
    return [
        f"Write a Myth-style story about Luna finding a calf near {setting.place}.",
        f"Use a Flashback to reveal why Luna chooses kindness toward {tale.calf_name}.",
        "Include the words embed and consist naturally, then end with a clear happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    tale: Tale = facts["tale"]
    setting: Setting = facts["setting"]
    return [
        QAItem(
            "Who did Luna find?",
            f"Luna found {tale.calf_name}, a frightened calf, near {setting.place}.",
        ),
        QAItem(
            "What clue helped Luna understand where the calf belonged?",
            f"She noticed {tale.clue}, which led her toward the shepherd.",
        ),
        QAItem(
            "What did the flashback teach Luna?",
            f"The flashback reminded Luna that {tale.lesson}.",
        ),
        QAItem(
            "How did Luna show kindness?",
            "She stayed gentle and patient, helped the calf travel safely, and promised not to leave it alone.",
        ),
        QAItem(
            "How did the story end?",
            f"It ended happily when {tale.resolution}. The calf was safe and Luna's kindness was remembered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a flashback?",
            "A flashback is a story moment that returns to something that happened earlier.",
        ),
        QAItem(
            "What does kindness mean?",
            "Kindness means treating others gently and helping when they need care.",
        ),
        QAItem(
            "What is a happy ending?",
            "A happy ending is when the main problem is solved and the characters are safe or glad.",
        ),
        QAItem(
            "What does embedded mean?",
            "Embedded means set firmly inside something else, such as a thread set inside a bell.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.type}) " + " ".join(details))
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    tale = TALES[params.scenario]
    setting = SETTINGS[params.place]
    world = build_world(params, tale, setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        index = 0
        for scenario in sorted(TALES):
            for place in sorted(SETTINGS):
                rng = random.Random(base_seed + index)
                params = StoryParams(
                    name="Luna",
                    scenario=scenario,
                    place=place,
                    memory=rng.randrange(4),
                    clue=rng.randrange(4),
                    kindness=rng.randrange(4),
                    ending=rng.randrange(4),
                    seed=base_seed + index,
                )
                samples.append(generate(params))
                index += 1
    else:
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
