#!/usr/bin/env python3
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

STORYWORLDS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
if STORYWORLDS_ROOT not in sys.path:
    sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old clockwork museum"
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Clue:
    id: str
    observation: str
    reveal: str
    caution: str
    twist: str


@dataclass(frozen=True)
class Scenario:
    id: str
    opening: str
    mystery: str
    false_guess: str
    dialogue: str
    clue: str
    action: str
    reveal: str
    ending: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = meter(e, key) + amt


def add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = meme(e, key) + amt


SETTING = Setting(
    place="the old clockwork museum",
    affords={"watching", "asking", "searching", "listening"},
)

SCENARIOS = [
    Scenario(
        "gallery_bell",
        "On a rainy evening, the museum bell rang once even though no visitor touched the rope.",
        "A tiny brass bell inside the north gallery kept chiming whenever the lights flickered.",
        "The caretaker blamed the new volunteer and nearly locked the gallery door.",
        "“Could the bell be answering the light instead of a hand?” asked Mara, who loved puzzles.",
        "A loose gear under the floor ticked only when the hallway lamp shone through the cracked glass.",
        "Mara followed the sound with her friend Niko, lifting each rug corner carefully.",
        "They found a hidden mechanism of mirrored teeth that had been built to alert the curator when the roof leaked.",
        "Mara and Niko left the bell in place, and the museum fixed the roof before the next storm.",
    ),
    Scenario(
        "missing_key",
        "The curator's key vanished from its hook beside the case of silver watches.",
        "Every drawer in the archive stayed locked, and the map room could not be opened.",
        "The curator accused the janitor of taking it for a joke.",
        "“What if the key is not gone, but waiting where the machinery keeps time?” said Jonah.",
        "A thread of oil led to the oldest pendulum, which swung a little too smoothly.",
        "Jonah and his friend Mina listened to the tick, then searched under the floorboard panel together.",
        "They found the key tied to a weighted string inside the pendulum box, where a warning device had once stored it.",
        "The curator apologized, and the friends marked the box with a bright ribbon so no one would panic again.",
    ),
    Scenario(
        "glass_shadow",
        "At dusk, strange shadows crossed the marble floor even though the room was empty.",
        "The shadows crawled like little animals around the display of glass stars.",
        "The security guard feared a thief had come and shut off half the lamps.",
        "“Let's not chase the shadows; let's follow where they begin,” said Tessa to her friend Hugo.",
        "A cracked lens near the skylight split one lantern beam into three moving shapes.",
        "Tessa and Hugo moved a ladder slowly and covered the lens with soft cloth before climbing higher.",
        "Behind the glass, they found a toy mechanism of turning mirrors left by an inventor to test the skylight.",
        "The museum kept the mirrors for the exhibit, and the shadows stopped looking like a threat.",
    ),
    Scenario(
        "whispering_chain",
        "From the engine room came a whispering rattle no one could explain.",
        "It sounded almost like someone speaking from inside the pipes.",
        "The guide thought the sound meant a ghost in the building and wanted to leave the room sealed.",
        "“If it is a message, it may be asking to be read,” said Elias to his friend June.",
        "A chain dragged over a bent hook each time the fan turned on.",
        "Elias and June shared a small flashlight and followed the rattle to the back wall.",
        "They found a maintenance mechanism that only whispered when the fan was too strong and the chain could not rest.",
        "The pair repaired the hook, and the room became quiet enough for the guide to smile again.",
    ),
    Scenario(
        "hidden_note",
        "A note appeared every morning on the same bench in the courtyard.",
        "It always said only one word: mechanism.",
        "The baker worried someone was sending a warning and asked for the bench to be watched.",
        "“Maybe the note is a clue, not a threat,” said Lila to her friend Ben.",
        "A pencil mark on the bench matched the shape of a loose spring in the nearby fountain.",
        "Lila and Ben searched the fountain together and found a dry pocket behind the pump wheel.",
        "Inside was a little paper trail from a visiting mechanic who had hidden practice notes for a scavenger game.",
        "The friends laughed, and the baker put up a sign inviting children to solve the next clue together.",
    ),
]

NAME_POOL = ["Mara", "Niko", "Jonah", "Mina", "Tessa", "Hugo", "Elias", "June", "Lila", "Ben"]


@dataclass
class StoryParams:
    place: str
    scenario: str
    hero: str
    friend: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery storyworld about friendship, caution, and a twist.")
    ap.add_argument("--place", choices=["museum"], default="museum")
    ap.add_argument("--scenario", choices=list(s for s in range(len(SCENARIOS))), type=int)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(NAME_POOL)
    friend = args.friend or rng.choice([n for n in NAME_POOL if n != hero])
    scenario = str(args.scenario) if args.scenario is not None else str(rng.randrange(len(SCENARIOS)))
    return StoryParams(place="museum", scenario=scenario, hero=hero, friend=friend)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "museum":
        raise StoryError("This storyworld only supports the museum setting.")
    if not params.hero or not params.friend or params.hero == params.friend:
        raise StoryError("The mystery needs two different friends.")
    try:
        idx = int(params.scenario)
    except ValueError as e:
        raise StoryError("Scenario must be a valid index.") from e
    if idx < 0 or idx >= len(SCENARIOS):
        raise StoryError("Scenario index out of range.")


def make_world() -> World:
    return World(SETTING)


def tell(world: World, params: StoryParams) -> World:
    scenario = SCENARIOS[int(params.scenario)]
    hero = world.add(Entity(id=params.hero, kind="character", type="child", label=params.hero))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", label=params.friend))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type="adult", label="caretaker"))
    clue = Clue(
        id="mechanism_clue",
        observation=scenario.clue,
        reveal=scenario.reveal,
        caution="The careful answer was to look before accusing.",
        twist="The strange thing was a safety device, not a danger.",
    )
    world.facts.update(hero=hero, friend=friend, caretaker=caretaker, scenario=scenario, clue=clue)

    add_meme(hero, "curiosity", 1.0)
    add_meme(friend, "curiosity", 1.0)
    world.say(f"The museum smelled of rain, dust, and old oil, and {scenario.opening}")
    world.say(f"That was the sort of place where a mystery could hide in plain sight.")
    world.para()
    world.say(scenario.mystery)
    world.say(scenario.false_guess)
    add_meme(caretaker, "worry", 1.0)
    add_meme(hero, "worry", 1.0)
    world.say(scenario.dialogue)
    world.para()

    add_meter(hero, "sharing", 1.0)
    add_meter(friend, "sharing", 1.0)
    world.say(f"The friends listened together, and {clue.observation.lower()}")
    world.say(f"They followed the clue with a flashlight, a careful step, and no rushing.")
    world.say(f"{scenario.action}")
    add_meme(hero, "trust", 1.0)
    add_meme(friend, "trust", 1.0)
    world.para()

    world.say(f"The twist came clear at last: {clue.twist}")
    world.say(f"{scenario.reveal}")
    world.say(f"{clue.caution} The caretaker thanked the friends for solving the mystery kindly.")
    world.say(
        f"In the end, the {world.setting.place} felt safer, and the two friends walked out side by side, "
        f"certain that a strange noise is not always a bad thing."
    )
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = make_world()
    world = tell(world, params)
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
    scenario = f["scenario"]
    return [
        "Write a child-friendly mystery story with a mechanism, friendship, caution, and a twist.",
        f"Tell a short story about {f['hero'].id} and {f['friend'].id} solving this problem: {scenario.mystery}",
        "Include dialogue that changes what the characters decide to do.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scenario = f["scenario"]
    clue = f["clue"]
    return [
        QAItem(
            question="What mysterious thing happened in the museum?",
            answer=f"{scenario.mystery} It made everyone wonder what was causing the noise.",
        ),
        QAItem(
            question="What did the caretaker first think?",
            answer=f"The caretaker first made a false guess: {scenario.false_guess}",
        ),
        QAItem(
            question="What question helped the friends solve the mystery?",
            answer=f"They used this helpful idea: {scenario.dialogue}",
        ),
        QAItem(
            question="What was the clue?",
            answer=f"The clue was: {clue.observation}",
        ),
        QAItem(
            question="What was the twist?",
            answer=f"The twist was that {clue.twist.lower()}",
        ),
        QAItem(
            question="How did friendship help?",
            answer="The two friends listened, searched, and stayed careful together, which helped them find the answer without causing trouble.",
        ),
        QAItem(
            question="How did caution matter?",
            answer=f"They did not rush to accuse anyone, and {clue.caution.lower()}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a mechanism?", answer="A mechanism is a set of parts that work together to make something happen."),
        QAItem(question="What is a mystery?", answer="A mystery is something confusing that needs careful thinking to solve."),
        QAItem(question="Why is caution useful?", answer="Caution is useful because it helps people avoid mistakes and stay safe."),
        QAItem(question="Why are friends helpful?", answer="Friends can share ideas, listen closely, and support each other when a problem is tricky."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== Story QA ==")
    for qa in sample.story_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for qa in sample.world_qa:
        parts.append(f"Q: {qa.question}")
        parts.append(f"A: {qa.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        lines.append(f"{ent.id}: meters={ent.meters} memes={ent.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(museum, scenario0).
valid(museum, scenario1).
valid(museum, scenario2).
valid(museum, scenario3).
valid(museum, scenario4).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("setting", "museum"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("style", "mystery"),
            asp.fact("seed_word", "mechanism"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("museum", f"scenario{i}") for i in range(len(SCENARIOS))]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="museum", scenario="0", hero="Mara", friend="Niko"),
    StoryParams(place="museum", scenario="1", hero="Jonah", friend="Mina"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.hero} and {p.friend} / scenario {p.scenario}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
