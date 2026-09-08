#!/usr/bin/env python3
"""
A child-friendly superhero storyworld about bacon, a missing breakfast,
a surprising twist, and reconciliation.
"""

from __future__ import annotations

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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
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
    hero_name: str = "Luna"
    friend_name: str = "Milo"
    hero_type: str = "girl"
    friend_type: str = "boy"
    city_name: str = "Brighton City"


HERO_NAMES = ["Luna", "Nova", "Zara", "Maya", "Theo", "Kai", "Pip", "Rafi"]
CITY_NAMES = ["Brighton City", "Sunbeam Town", "Cloudtop City", "Maple Metro"]


INCIDENTS = [
    {
        "title": "the bacon rescue",
        "threat": "a gust from the Whisker Wind machine lifted every strip of bacon from the town breakfast fair",
        "wrong": "thought her friend had hidden the bacon to keep it for himself",
        "clue": "tiny grease spots led from the fair toward the old clock tower",
        "twist": "the bacon had not been stolen at all; it was stuck to the Whisker Wind machine's spinning safety plate",
        "action": "used a gentle beam to slow the machine while her friend reached the plate with a long wooden spoon",
        "repair": "admitted that she had blamed him before checking the clues",
        "ending": "the rescued bacon crackled safely on the fair's giant griddle",
        "lesson": "A hero checks the facts before making a hurtful guess",
    },
    {
        "title": "the vanished breakfast cart",
        "threat": "the mayor's breakfast cart rolled away by itself just before the hungry neighbors arrived",
        "wrong": "chased the cart and accused her friend of removing its wheels",
        "clue": "one wheel mark curved uphill toward the community garden",
        "twist": "the cart had been pulled by a sleepy robot goat that wanted one more smell of bacon",
        "action": "blocked the garden gate with a soft force field while her friend offered the goat a basket of carrots",
        "repair": "said sorry for accusing her friend and listened to what he had noticed",
        "ending": "the cart returned, and the robot goat received a carrot-shaped medal",
        "lesson": "Listening can solve a mystery faster than shouting",
    },
    {
        "title": "the smoky signal",
        "threat": "a cloud of harmless smoke covered the square and made the bacon sign disappear",
        "wrong": "used her super-speed to remove the sign from its post without asking anyone",
        "clue": "the sign's shadow still pointed toward the bakery roof",
        "twist": "the smoke was a secret practice signal from young firefighters, and the sign was meant to guide them",
        "action": "cleared the smoke in a spiral and helped the firefighters carry the sign back into place",
        "repair": "explained why she had acted too quickly and asked her friend to help her pause next time",
        "ending": "the bacon sign shone above the square while the firefighters cheered",
        "lesson": "Power becomes safer when a hero makes room for other helpers",
    },
    {
        "title": "the crispy comet",
        "threat": "a tiny comet of flying bacon zipped over the rooftops and startled everyone below",
        "wrong": "tried to remove it from the sky with one giant leap",
        "clue": "the comet slowed whenever someone played a calm rhythm on a lunchbox",
        "twist": "it was a delivery drone carrying breakfast to the night-shift nurses",
        "action": "made a soft landing path while her friend tapped the calming rhythm",
        "repair": "thanked her friend for noticing the rhythm instead of insisting on her own plan",
        "ending": "the drone landed beside the hospital kitchen, where warm bacon sandwiches waited",
        "lesson": "A different idea can be the missing piece in a rescue",
    },
]


MODES = [
    ("Luna wore her bright cape and listened for trouble.", "The first answer was not always the right one."),
    ("The morning seemed peaceful until the breakfast bell rang twice.", "A true superhero changes plans when new evidence appears."),
    ("Luna promised to protect everyone, even from very small mysteries.", "Her biggest strength turned out to be making things right."),
    ("The city trusted Luna because she was brave and kind.", "Being kind also meant admitting when bravery had rushed ahead of care."),
]


def _setup(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(params.hero_name, "character", params.hero_type, params.hero_name))
    friend = world.add(Entity(params.friend_name, "character", params.friend_type, params.friend_name))
    city = world.add(Entity("city", "place", "city", params.city_name))
    bacon = world.add(Entity("bacon", "thing", "food", "bacon", owner="community"))
    cape = world.add(Entity("cape", "thing", "gear", "bright cape", owner=params.hero_name))

    hero.meters.update(courage=1.0, patience=0.4)
    hero.memes.update(worry=0.0, trust=0.7)
    friend.meters.update(observation=1.0, kindness=1.0)
    friend.memes["hurt"] = 0.0
    city.meters["safety"] = 1.0
    bacon.meters["warmth"] = 1.0
    cape.meters["lift"] = 1.0
    world.facts.update(hero=hero, friend=friend, city=city, bacon=bacon, cape=cape)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join([params.hero_name, params.friend_name, params.city_name])
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    token = _token(params)
    incident = INCIDENTS[token % len(INCIDENTS)]
    mode = MODES[(token // len(INCIDENTS)) % len(MODES)]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    city = world.facts["city"]

    world.say(mode[0])
    world.say(
        f"{hero.label} flew over {city.label} just as {incident['threat']}. "
        f"The breakfast crowd gasped, but {friend.label} stayed close to help."
    )
    world.say(
        f"{hero.label} swooped down and {incident['wrong']}. "
        "She wanted to fix the problem before anyone else could be frightened."
    )

    world.para()
    world.say(
        f'"Wait," {friend.label} said. "I saw something you may have missed."'
    )
    world.say(
        f'"I have to protect the breakfast," {hero.label} replied. '
        '"But I will listen before I act again."'
    )
    world.say(
        f"{friend.label} pointed to {incident['clue']}. "
        f"That clue revealed that {incident['twist']}."
    )
    world.say(mode[1])

    world.para()
    world.say(
        f"Together, they {incident['action']}. "
        "The danger faded without anyone being hurt, and the breakfast could be saved."
    )
    world.say(
        f"{hero.label} turned to {friend.label} and {incident['repair']}. "
        f'"I was worried and rushed," she said. "I should have trusted you enough to ask."'
    )
    world.say(
        f'"I was upset, but I am glad you listened," {friend.label} replied. '
        '"We can solve the next problem together."'
    )

    world.para()
    world.say(f"{incident['ending'].capitalize()}.")
    world.say(
        f"{incident['lesson']}. {hero.label} and {friend.label} shared the first serving, "
        "and the bright morning felt safe again."
    )

    hero.meters["patience"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["trust"] = 1.0
    friend.memes["hurt"] = 0.0
    city.meters["safety"] = 1.0
    bacon.meters["warmth"] = 1.0
    world.fired.update({("twist", incident["title"]), ("reconciliation", incident["title"])})
    world.facts.update(
        params=params,
        incident=incident,
        incident_index=token % len(INCIDENTS),
        mode_index=(token // len(INCIDENTS)) % len(MODES),
        twist=True,
        reconciliation=True,
        bacon_saved=True,
    )
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly superhero story about {p.hero_name}, bacon, and a mystery in {p.city_name}.",
        f"Show how {p.hero_name} wrongly blames {p.friend_name}, discovers that {incident['twist']}, and reconciles with the friend.",
        "Include a brave rescue, a surprising twist, spoken dialogue, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            f"What problem threatened breakfast in {p.city_name}?",
            f"{incident['threat'].capitalize()}.",
        ),
        QAItem(
            f"What did {p.hero_name} wrongly believe about {p.friend_name}?",
            f"{p.hero_name} thought that {p.friend_name} {incident['wrong'].split(' and ')[-1]}.",
        ),
        QAItem(
            "What was the surprising twist?",
            f"The twist was that {incident['twist']}.",
        ),
        QAItem(
            "How did the two friends solve the problem?",
            f"They {incident['action']}.",
        ),
        QAItem(
            "How did reconciliation happen?",
            f"{p.hero_name} {incident['repair']}, and the friends agreed to solve future problems together.",
        ),
        QAItem(
            "What proved that the ending was happy?",
            f"{incident['ending'].capitalize()} The friends shared breakfast peacefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is bacon?",
            "Bacon is a food often made from cured pork and cooked until it is crisp.",
        ),
        QAItem(
            "What does remove mean?",
            "Remove means to take something away from a place.",
        ),
        QAItem(
            "What is reconciliation?",
            "Reconciliation is making peace after a disagreement by speaking honestly, listening, and repairing trust.",
        ),
        QAItem(
            "What does a superhero do?",
            "A superhero uses special abilities, courage, and care to help people and protect them from danger.",
        ),
    ]


ASP_RULES = r"""
confused(S) :- bacon_problem(S), wrong_blame(S).
twist(S) :- confused(S), hidden_truth(S).
reconciled(S) :- twist(S), apology(S), forgiveness(S).
bacon_saved(S) :- reconciled(S), rescue(S).
valid_story(S) :- bacon_saved(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("bacon_problem", "story1"),
            asp.fact("wrong_blame", "story1"),
            asp.fact("hidden_truth", "story1"),
            asp.fact("apology", "story1"),
            asp.fact("forgiveness", "story1"),
            asp.fact("rescue", "story1"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    found = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if found == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(found))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about bacon, a twist, and reconciliation."
    )
    parser.add_argument("--hero-name", choices=HERO_NAMES)
    parser.add_argument("--friend-name", choices=HERO_NAMES)
    parser.add_argument("--city-name", choices=CITY_NAMES)
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
    hero = args.hero_name or rng.choice(HERO_NAMES)
    choices = [name for name in HERO_NAMES if name != hero]
    friend = args.friend_name or rng.choice(choices)
    city = args.city_name or rng.choice(CITY_NAMES)
    return StoryParams(
        seed=None,
        hero_name=hero,
        friend_name=friend,
        hero_type="girl" if hero in {"Luna", "Nova", "Zara", "Maya"} else "boy",
        friend_type="boy" if friend in {"Theo", "Kai", "Pip", "Rafi"} else "girl",
        city_name=city,
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
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) {' '.join(details)}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
    StoryParams(hero_name="Luna", friend_name="Milo", hero_type="girl", friend_type="boy", city_name="Brighton City"),
    StoryParams(hero_name="Nova", friend_name="Theo", hero_type="girl", friend_type="boy", city_name="Sunbeam Town"),
    StoryParams(hero_name="Zara", friend_name="Maya", hero_type="girl", friend_type="girl", city_name="Cloudtop City"),
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
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
