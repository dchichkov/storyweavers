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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = {
    "canal path": {
        "setting": "the canal path",
        "hazard": "a broken lock gate",
        "safe_place": "the old towbridge",
        "material": "a thick rope",
    },
    "willow canal path": {
        "setting": "the willow canal path",
        "hazard": "a fallen willow blocking the sluice",
        "safe_place": "the stone footbridge",
        "material": "a canvas strap",
    },
    "mill canal path": {
        "setting": "the mill canal path",
        "hazard": "a jammed waterwheel",
        "safe_place": "the mill yard",
        "material": "a wooden lever",
    },
}

NAMES = ("Luna", "Milo", "Tess", "Pip", "Mara", "Jonah", "Iris", "Sol")
MOODS = ("steady", "curious", "careful", "bold")
CREATURES = ("a tiny field mouse", "a patient heron", "a sleepy frog", "a bright kingfisher")

TALES = (
    {
        "giant": "a gigantic turtle",
        "arrival": "It lumbered onto the path with a cartwheel caught around one shell edge.",
        "conflict": "The turtle wanted to hurry home, but every hurried step pulled the cartwheel tighter.",
        "clue": "Luna saw a trail of crushed reeds leading from the wheel to the shallow bank.",
        "turn": "The giant creature was not attacking anyone; it was frightened and trapped.",
        "action": "looped the rope around the wheel while the turtle held still",
        "result": "the wheel slid free, and the turtle could crawl safely toward the reeds",
        "lesson": "bravery is not the absence of fear; it is choosing a helpful action while fear is present",
        "ending": "At sunset, the gigantic turtle blinked beside the quiet canal, and Luna's small footprints led home.",
    },
    {
        "giant": "a gigantic paper kite",
        "arrival": "It had fallen across the path and tugged at a row of young canal trees.",
        "conflict": "The kite's owner shouted from the far bank, while the wind pulled the kite farther into the water.",
        "clue": "Luna noticed that one corner was snagged on a low branch, not wrapped around the whole canal.",
        "turn": "The frightening shadow came from paper and wind, while the real problem was one hidden knot.",
        "action": "asked the owner to stop pulling, then used the long lever to lift the branch",
        "result": "the knot loosened and the kite rose without tearing the trees",
        "lesson": "conflict grows when people pull in opposite directions, but a calm plan can give everyone room",
        "ending": "The gigantic kite sailed above the canal like a red moon, while the trees stood unbroken below.",
    },
    {
        "giant": "a gigantic wooden boat",
        "arrival": "It had drifted sideways and blocked the narrow canal path.",
        "conflict": "The miller blamed the boatman, and the boatman blamed the strong current.",
        "clue": "Luna found a small branch wedged beneath the boat's rudder.",
        "turn": "The quarrel had hidden a simple cause that neither grown-up had noticed.",
        "action": "showed both adults the branch and helped them push together from the safe bank",
        "result": "the boat turned with the current and opened the path for everyone",
        "lesson": "before choosing whom to blame, look for the small thing that may be causing the trouble",
        "ending": "The gigantic boat glided on, and the miller and boatman shared a sheepish wave.",
    },
)

DIALOGUES = (
    ("That is gigantic, and I am scared", "Being scared tells us to be careful, not to stop thinking"),
    ("We should pull harder", "Not until we know what is caught"),
    ("It must be angry", "A trapped thing may look angry when it is only afraid"),
    ("You cannot solve this alone", "Then stand with me and help make a safe plan"),
    ("Everyone is shouting", "Let us use quiet words so we can hear the water"),
)

OPENINGS = (
    "At dawn, the canal path looked thin beside the wide silver water.",
    "The village fable began where towboats once crept beneath the willow trees.",
    "Luna was carrying a basket of apples when the canal path suddenly grew noisy.",
    "On a bright morning, even the ordinary canal path held room for a gigantic surprise.",
)

ASP_RULES = r"""
kind(gigantic).
feature(bravery).
feature(conflict).
style(fable).
setting(canal_path).
valid_story :- kind(gigantic), feature(bravery), feature(conflict), style(fable), setting(canal_path).
#show valid_story/0.
"""


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: Optional[str] = None
    carried_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    mood: str
    seed: Optional[int] = None


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable of bravery and conflict on a canal path.")
    parser.add_argument("--place", choices=tuple(PLACES))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_facts() -> str:
    import asp
    return "\n".join(
        (
            asp.fact("kind", "gigantic"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "conflict"),
            asp.fact("style", "fable"),
            asp.fact("setting", "canal_path"),
        )
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    models = asp.solve(asp_program(), models=1)
    valid = any(sym.name == "valid_story" for sym in models[0]) if models else False
    if not valid:
        print("MISMATCH: ASP rejected the canonical story features.")
        return 1
    print("OK: ASP accepts gigantic, bravery, conflict, fable, and canal path.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "canal path"
    if place not in PLACES:
        raise StoryError(f"Unknown place: {place}")
    hero = rng.choice(NAMES)
    companion = rng.choice([name for name in NAMES if name != hero])
    return StoryParams(place=place, hero=hero, companion=companion, mood=rng.choice(MOODS))


def story_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.place, params.hero, params.companion, params.mood))
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("The tale must be set on a known canal path.")
    rng = random.Random(story_seed(params))
    tale = TALES[story_seed(params) % len(TALES)]
    opening = OPENINGS[(story_seed(params) // len(TALES)) % len(OPENINGS)]
    dialogue = DIALOGUES[(story_seed(params) // (len(TALES) * len(OPENINGS))) % len(DIALOGUES)]
    creature = rng.choice(CREATURES)
    place = PLACES[params.place]

    hero = Entity(
        id="hero",
        kind="character",
        label=params.hero,
        meters={"distance_to_hazard": 18.0, "energy": 1.0},
        memes={"bravery": 0.3, "worry": 0.7},
        location=params.place,
    )
    companion = Entity(
        id="companion",
        kind="character",
        label=params.companion,
        meters={"distance_to_hazard": 20.0, "energy": 1.0},
        memes={"bravery": 0.4, "worry": 0.6},
        location=params.place,
    )
    giant = Entity(
        id="giant",
        kind="creature",
        label=tale["giant"],
        meters={"size": 12.0, "distance_to_safe_place": 9.0},
        memes={"fear": 0.8, "trust": 0.1},
        location=params.place,
    )
    tool = Entity(
        id="tool",
        kind="helpful material",
        label=place["material"],
        meters={"length": 4.0},
        memes={"useful": 1.0},
        location=params.place,
    )
    world = World(place=place["setting"], entities={e.id: e for e in (hero, companion, giant, tool)})

    world.say(opening)
    world.say(f"{params.hero}, a {params.mood} child, walked beside {params.companion} along {place['setting']}.")
    world.say(f"A {creature} watched from a reed, and the canal water whispered under the bank.")
    world.say(tale["arrival"])

    world.para()
    world.say(tale["conflict"])
    world.say(f"'{dialogue[0]},' said {params.companion}. '{dialogue[1]},' answered {params.hero}.")
    world.say(f"They did not rush toward the gigantic trouble. First, {params.hero} noticed that {tale['clue']}")
    world.say(f"Then {params.companion} understood that {tale['turn']}")

    world.para()
    world.say(f"Together, the children {tale['action']}.")
    world.say(f"The work was difficult, but their bravery changed the conflict: {tale['result']}.")
    world.say(f"The creature's fear softened into trust, and the two children stepped back toward {place['safe_place']}.")
    world.say(f"The fable's lesson was simple: {tale['lesson'].capitalize()}.")
    world.say(tale["ending"])

    hero.memes["bravery"] = 1.0
    hero.memes["worry"] = 0.2
    companion.memes["bravery"] = 0.9
    companion.memes["worry"] = 0.2
    giant.memes["fear"] = 0.2
    giant.memes["trust"] = 1.0
    giant.meters["distance_to_safe_place"] = 0.0
    world.trace = [
        "noticed:gigantic trouble",
        "named:conflict without blaming",
        "observed:" + tale["clue"],
        "chose:bravery with a safe plan",
        "resolved:" + tale["result"],
    ]
    world.facts = {
        "setting": params.place,
        "hero": params.hero,
        "companion": params.companion,
        "gigantic_subject": tale["giant"],
        "conflict": tale["conflict"],
        "clue": tale["clue"],
        "resolution": tale["result"],
        "lesson": tale["lesson"],
    }

    prompts = [
        f"Write a fable set on {place['setting']} about {params.hero} facing a gigantic danger.",
        f"Show how bravery changes a conflict between {params.hero}, {params.companion}, and {tale['giant']}.",
        "End with a concrete image and a clear lesson about careful courage.",
    ]
    story_qa = [
        QAItem(
            question=f"What gigantic problem did {params.hero} find on the canal path?",
            answer=f"{params.hero} found {tale['giant']}. {tale['arrival']}",
        ),
        QAItem(
            question="What caused the conflict to seem worse at first?",
            answer=f"The conflict seemed worse because {tale['conflict'].rstrip('.')}.",
        ),
        QAItem(
            question=f"What did {params.hero} notice before acting?",
            answer=f"{params.hero} noticed that {tale['clue']}",
        ),
        QAItem(
            question="How did bravery help solve the problem?",
            answer=f"The children {tale['action']}. Their brave but careful action meant that {tale['result']}.",
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer=f"The fable taught that {tale['lesson']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a canal path?",
            answer="A canal path is a walkway beside a canal, where people can travel while boats or water move nearby.",
        ),
        QAItem(
            question="What does bravery mean in this story?",
            answer="Bravery means noticing fear and still choosing a careful, helpful action.",
        ),
        QAItem(
            question="Why should people look for causes during a conflict?",
            answer="Looking for causes can replace blame with understanding and reveal a safer way to solve the problem.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"  {entity.id}: {entity.kind}; label={entity.label}; "
                f"meters={entity.meters}; memes={entity.memes}; location={entity.location}"
            )
        for event in sample.world.trace:
            print(f"  event: {event}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams("canal path", "Luna", "Milo", "steady"),
    StoryParams("willow canal path", "Tess", "Pip", "careful"),
    StoryParams("mill canal path", "Mara", "Jonah", "curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print(asp.atoms(model, "valid_story"))
        return

    rng = random.Random(args.seed)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen = set()
        for index in range(max(1, args.n)):
            params = resolve_params(args, random.Random(rng.randrange(2**63)))
            params.seed = (args.seed if args.seed is not None else 0) + index
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
