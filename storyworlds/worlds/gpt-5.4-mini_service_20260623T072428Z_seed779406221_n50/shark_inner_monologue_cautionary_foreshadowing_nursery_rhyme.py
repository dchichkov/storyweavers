#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260623T072428Z_seed779406221_n50/shark_inner_monologue_cautionary_foreshadowing_nursery_rhyme.py
====================================================================================================

A tiny standalone storyworld: a nursery-rhyme ocean tale with a shark, inner
monologue, cautionary tension, and foreshadowing that pays off in a safe turn.

Premise:
- A small swimmer or sailor sees a shark near a treasure, shell, or kite.
- The character thinks to themselves in a soft inner monologue.
- The story foreshadows a danger sign in the water or sky.
- A cautious choice and a helpful object or companion lead to a gentle ending.

The domain is deliberately small and state-driven:
- meters: distance, wave height, hunger, calm, speed, safety
- memes: worry, courage, caution, relief, curiosity, love

The prose aims for a nursery-rhyme feel: rhythmic, concrete, child-facing,
and lightly repetitive without becoming a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the bright shore"
    weather: str = "breezy"
    affords: set[str] = field(default_factory=lambda: {"swim", "row", "watch"})


@dataclass
class Shark:
    label: str
    phrase: str
    size: str
    mood: str
    hunger: str
    warning_sign: str


@dataclass
class SafeChoice:
    id: str
    label: str
    phrase: str
    effect: str
    ending_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _inner_monologue(hero: Entity, shark: Shark, setting: Setting) -> str:
    if hero.memes.get("worry", 0) >= THRESHOLD:
        return (
            f"{hero.pronoun().capitalize()} thought, “The water looks funny today; "
            f"I should stay near the sand and keep my eyes on the waves.”"
        )
    if hero.memes.get("curiosity", 0) >= THRESHOLD:
        return (
            f"{hero.pronoun().capitalize()} thought, “I want to look, but I must be "
            f"careful, because {shark.label} may be near the blue-green swell.”"
        )
    return (
        f"{hero.pronoun().capitalize()} thought, “Little feet go slow, little eyes "
        f"go wide, and I will not rush near the sea.”"
    )


def _foreshadow(setting: Setting, shark: Shark) -> str:
    return (
        f"Before the tale grew tall, a dark fin made a soft line across the bay, "
        f"and even the gulls flew a little higher."
    )


def _danger_meter(hero: Entity, shark: Shark) -> float:
    dist = hero.meters.get("distance_to_water", 0.0)
    wave = hero.meters.get("wave_height", 0.0)
    hunger = shark_state["hunger_level"]
    return max(0.0, (10.0 - dist) + wave + hunger)


def _warn(hero: Entity, shark: Shark) -> str:
    return (
        f"The little heart in {hero.id} whispered, “A shark can glide where the foam "
        f"is white, so I must not paddle too far out.”"
    )


def _choose_safely(hero: Entity, choice: SafeChoice) -> str:
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    return (
        f"So {hero.id} chose {choice.phrase}, and {choice.effect}. "
        f"{choice.ending_line}"
    )


def _rescue_beats(hero: Entity, companion: Entity) -> str:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    companion.memes["love"] = companion.memes.get("love", 0.0) + 1
    return (
        f"{companion.id} paddled close and called, “Come on back, little one.” "
        f"{hero.id} listened, and the tide felt kind again."
    )


def tell(setting: Setting, shark: Shark, choice: SafeChoice,
         hero_name: str = "Mia", hero_type: str = "girl",
         companion_name: str = "Ned", companion_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, role="hero",
        meters={"distance_to_water": 3.0, "wave_height": 1.0},
        memes={"curiosity": 1.0, "worry": 1.0},
    ))
    companion = world.add(Entity(
        id=companion_name, kind="character", type=companion_type, role="companion",
        meters={"distance_to_water": 5.0, "wave_height": 0.5},
        memes={"caution": 1.0},
    ))
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["shark"] = shark
    world.facts["choice"] = choice

    world.say(
        f"By {setting.place}, in the {setting.weather} air, {hero.id} and {companion.id} "
        f"found a day that sparkled like a shell."
    )
    world.say(
        f"They watched the water, and {shark.label} drifted by like a silver knife "
        f"under cloth-of-blue."
    )
    world.say(_foreshadow(setting, shark))
    world.para()
    world.say(_inner_monologue(hero, shark, setting))
    world.say(_warn(hero, shark))
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    hero.meters["distance_to_water"] += 1.0

    world.para()
    world.say(
        f"{hero.id} saw the white foam line and did not race the tide. "
        f"{_choose_safely(hero, choice)}"
    )
    world.say(_rescue_beats(hero, companion))
    world.say(
        f"Then the {choice.label} glowed in little hands, and the shore stayed "
        f"safe and sweet."
    )
    return world


SETTING_REGISTRY = {
    "shore": Setting(place="the bright shore", weather="breezy"),
    "harbor": Setting(place="the sleepy harbor", weather="misty"),
    "cove": Setting(place="the little cove", weather="sunny"),
}

SHARKS = {
    "reef": Shark(
        label="a reef shark",
        phrase="a reef shark with a stripy shadow",
        size="small",
        mood="watchful",
        hunger="mild",
        warning_sign="a dark fin",
    ),
    "hammer": Shark(
        label="a hammerhead shark",
        phrase="a hammerhead shark with a broad, bobbing head",
        size="medium",
        mood="calm",
        hunger="mild",
        warning_sign="a wide silver back",
    ),
}

CHOICES = {
    "bucket": SafeChoice(
        id="bucket",
        label="bucket",
        phrase="a small bucket for collecting shells",
        effect="the shells clinked softly as they were gathered",
        ending_line="No one needed to splash farther than the ankle-deep water.",
    ),
    "kite": SafeChoice(
        id="kite",
        label="kite",
        phrase="a bright kite with a long tail",
        effect="the kite danced high and light above the beach",
        ending_line="The wind kept the play in the sky, away from the shark.",
    ),
    "boat": SafeChoice(
        id="boat",
        label="boat",
        phrase="a little rowboat tied near the dock",
        effect="the boat rocked gently while they stayed close to shore",
        ending_line="The oars stayed still, and the children stayed smart.",
    ),
}


@dataclass
class StoryParams:
    setting: str
    shark: str
    choice: str
    name: str
    gender: str
    companion: str
    companion_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTING_REGISTRY:
        for sh in SHARKS:
            for c in CHOICES:
                combos.append((s, sh, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme shark storyworld with inner monologue, cautionary foreshadowing, and safe endings."
    )
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--shark", choices=SHARKS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    shark = args.shark or rng.choice(list(SHARKS))
    choice = args.choice or rng.choice(list(CHOICES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = ["Mia", "Luna", "Pip", "Nora"] if gender == "girl" else ["Ned", "Finn", "Owen", "Ben"]
    name = args.name or rng.choice(name_pool)
    comp_gender = args.companion_gender or ("boy" if gender == "girl" else "girl")
    comp_pool = ["Ned", "Finn", "Owen", "Ben"] if comp_gender == "boy" else ["Mia", "Luna", "Pip", "Nora"]
    companion = args.companion or rng.choice(comp_pool)
    return StoryParams(setting=setting, shark=shark, choice=choice, name=name, gender=gender,
                       companion=companion, companion_gender=comp_gender)


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    shark = f["shark"]
    choice = f["choice"]
    return [
        f'Write a short nursery-rhyme story about a child named {hero.id}, a {shark.label}, and a safe choice like {choice.label}.',
        f'Tell a gentle cautionary tale with foreshadowing where {hero.id} notices {shark.warning_sign} and listens carefully.',
        f'Write a soft rhyming story in which inner monologue helps {hero.id} stay safe near the sea.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    shark = f["shark"]
    choice = f["choice"]
    comp = f["companion"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, who spent a day by {world.setting.place} and stayed safe near the water.",
        ),
        QAItem(
            question=f"What did {hero.id} notice before choosing safely?",
            answer=f"{hero.id} noticed {shark.warning_sign} and understood that {shark.label} might be nearby.",
        ),
        QAItem(
            question=f"What did {hero.id} think to themself?",
            answer=f"{_inner_monologue(hero, shark, world.setting)}",
        ),
        QAItem(
            question=f"How did {hero.id} stay safe?",
            answer=f"{hero.id} chose {choice.phrase} and stayed near the shore instead of going too far out.",
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"{comp.id} helped by calling {hero.id} back to the shore and keeping the play calm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shark?",
            answer="A shark is a sea animal that swims in the ocean. Some sharks are big, and all of them deserve careful distance.",
        ),
        QAItem(
            question="Why is it wise to listen to a warning near the water?",
            answer="A warning can help you avoid danger, because the sea can change fast and a shark should be given space.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is a clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thinking voice inside the story.",
        ),
        QAItem(
            question="What makes a story cautionary?",
            answer="A cautionary story teaches a careful lesson about avoiding danger or making a safer choice.",
        ),
    ]


ASP_RULES = r"""
safe_choice(S) :- choice(S).
foreshadowing(shark_sign) :- shark_sign(_).
cautionary_story :- foreshadowing(shark_sign), safe_choice(_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for shid, sh in SHARKS.items():
        lines.append(asp.fact("shark", shid))
        lines.append(asp.fact("warning_sign", sh.warning_sign))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show cautionary_story/0."))
    asp_ok = bool(model)
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH: ASP/Python reasonableness disagree.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTING_REGISTRY[params.setting],
        SHARKS[params.shark],
        CHOICES[params.choice],
        hero_name=params.name,
        hero_type=params.gender,
        companion_name=params.companion,
        companion_type=params.companion_gender,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} {e.kind:8} {e.type:6} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


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
    StoryParams("shore", "reef", "bucket", "Mia", "girl", "Ned", "boy"),
    StoryParams("harbor", "hammer", "kite", "Owen", "boy", "Luna", "girl"),
    StoryParams("cove", "reef", "boat", "Nora", "girl", "Ben", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show cautionary_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show cautionary_story/0."))
        print("ASP model:", asp.atoms(model, "cautionary_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
