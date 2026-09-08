#!/usr/bin/env python3
"""
A standalone storyworld about a small superhero, a mysterious scar, and a
shake that becomes a brave signal.

The world is intentionally small: typed entities carry physical meters and
emotional memes, while the simulated state drives a complete child-facing
story.
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
class Place:
    key: str
    name: str
    phrase: str
    light: str


@dataclass
class Character:
    name: str
    kind: str
    power: str
    trait: str
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: Place
    hero: Optional[Character] = None
    scar: str = ""
    shake: str = ""
    danger: str = ""
    rescue: str = ""
    fixed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    name: str
    kind: str
    power: str
    trait: str
    place: str
    seed: Optional[int] = None


PLACES = {
    "rooftop": Place("rooftop", "the Moonbeam Rooftop", "on the Moonbeam Rooftop", "silver"),
    "harbor": Place("harbor", "Bright Harbor", "beside Bright Harbor", "golden"),
    "garden": Place("garden", "the Sky Garden", "in the Sky Garden", "green"),
}

KINDS = ["fox", "rabbit", "mouse", "cat", "small dragon"]
POWERS = ["glowing paws", "wind ears", "a stretchy tail", "a gentle thunder call", "a pocket-sized cape"]
TRAITS = ["brave", "kind", "clever", "patient", "hopeful"]

NAMES = {
    "fox": ["Luna", "Pip", "Mira"],
    "rabbit": ["Luna", "Tess", "Bram"],
    "mouse": ["Luna", "Nim", "Moss"],
    "cat": ["Luna", "Cleo", "Jett"],
    "small dragon": ["Luna", "Ember", "Roo"],
}

SCENES = [
    {
        "scar": "a pale scar across the old wooden sign",
        "shake": "the sign began to shake whenever the wind whispered",
        "danger": "a little delivery cart had rolled toward the roof's open edge",
        "rescue": "Luna caught the cart with her glowing paws and guided it back to safety",
        "clue": "the scar marked a loose hinge hidden behind the sign",
        "repair": "slid a bright ribbon through the hinge and tied it firmly to the railing",
        "ending": "the scar became a shining stripe beneath the ribbon",
        "lesson": "A mark from the past can point toward a brave new fix.",
    },
    {
        "scar": "a thin scar along the bell tower's blue paint",
        "shake": "the tower began to shake when the harbor bell rang",
        "danger": "three ducklings were stranded on a wobbling floating crate",
        "rescue": "Luna used her wind ears to send a calm breeze beneath the crate",
        "clue": "the scar ran straight toward a cracked support peg",
        "repair": "pressed a smooth wooden peg into the crack and wrapped it with golden cord",
        "ending": "the scar glimmered like a tiny lightning bolt",
        "lesson": "Careful heroes notice small clues before making big moves.",
    },
    {
        "scar": "a silver scar on the garden bridge",
        "shake": "the bridge began to shake beneath a basket of sleeping kittens",
        "danger": "the basket slid toward a gap between two planks",
        "rescue": "Luna stretched her tail across the gap and pulled the basket close",
        "clue": "the scar showed where one plank had split from its neighbor",
        "repair": "placed a flat board over the split and tied it with vines",
        "ending": "the scar looked like a silver road leading home",
        "lesson": "Being a superhero means helping first and boasting never.",
    },
    {
        "scar": "a dark scar on the old playground rocket",
        "shake": "the rocket began to shake as a gust pushed against it",
        "danger": "a red kite and its young flyer were tangled near the top rail",
        "rescue": "Luna climbed the rocket and freed the kite with her gentle thunder call",
        "clue": "the scar circled a loose bolt under the rocket's seat",
        "repair": "tightened the bolt with a small star-shaped wrench",
        "ending": "the scar shone like a badge on the rocket's side",
        "lesson": "A true hero turns fear into a careful next step.",
    },
]

OPENINGS = [
    "Luna was not the biggest hero in town, but she noticed things other heroes missed.",
    "Every morning, Luna practiced helping before practicing posing.",
    "The town knew Luna by her tiny cape and her enormous heart.",
    "Luna's cape fluttered proudly, though her knees sometimes wobbled underneath it.",
]

DIALOGUES = [
    ('"I hear the shake," Luna said. "Let us find what it is telling us."', '"A clue can become a plan," said her friend Sunny.'),
    ('"Do not worry," Luna said. "I will go slowly."', '"Slow is still brave," Sunny answered.'),
    ('"The scar is not something to hide," Luna said. "It may show us where to help."', '"Then we will look together," Sunny replied.'),
]

def valid_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.kind not in KINDS:
        raise StoryError(f"Unknown kind: {params.kind}")
    if params.power not in POWERS:
        raise StoryError(f"Unknown power: {params.power}")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait: {params.trait}")
    if not params.name.strip():
        raise StoryError("The superhero needs a name.")


def build_world(params: StoryParams) -> World:
    valid_params(params)
    choice = params.seed if params.seed is not None else sum(
        (i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values().__str__()))
    )
    scene = SCENES[choice % len(SCENES)]
    dialogue = DIALOGUES[(choice // len(SCENES)) % len(DIALOGUES)]
    world = World(PLACES[params.place])
    world.hero = Character(
        params.name,
        params.kind,
        params.power,
        params.trait,
        {"courage": 0.2, "worry": 0.4, "trust": 0.3},
    )
    world.scar = scene["scar"]
    world.shake = scene["shake"]
    world.danger = scene["danger"]
    world.rescue = scene["rescue"]
    world.meters = {"danger": 1.0, "stability": 0.2, "hero_courage": 0.2}
    world.memes = {"hope": 0.4, "relief": 0.0, "community_trust": 0.3}
    world.facts.update(scene=scene, dialogue=dialogue, opening=OPENINGS[choice % len(OPENINGS)])
    return world


def notice_shake(world: World) -> None:
    if "notice" in world.fired:
        return
    world.fired.add("notice")
    world.meters["danger"] = 1.5
    world.say(f"Then {world.shake}. The sound made every window go, shake-shake-shake.")


def hear_dialogue(world: World) -> None:
    if "dialogue" in world.fired:
        return
    world.fired.add("dialogue")
    first, second = world.facts["dialogue"]
    world.say(first)
    world.say(second)
    world.hero.memes["courage"] += 0.3
    world.hero.memes["worry"] -= 0.15


def investigate(world: World) -> None:
    if "investigate" in world.fired:
        return
    world.fired.add("investigate")
    scene = world.facts["scene"]
    world.say(
        f"Instead of rushing, {world.hero.name} followed the shake to the place where "
        f"{scene['clue']}."
    )
    world.facts["cause_found"] = True


def rescue(world: World) -> None:
    if "rescue" in world.fired:
        return
    if not world.facts.get("cause_found"):
        raise StoryError("The rescue cannot begin before the shaking is understood.")
    world.fired.add("rescue")
    world.say(f"Just then, {world.danger}.")
    world.say(f"{world.rescue}.")
    world.meters["danger"] = 0.5
    world.meters["hero_courage"] = 1.0
    world.memes["hope"] = 0.9


def repair(world: World) -> None:
    if "repair" in world.fired:
        return
    scene = world.facts["scene"]
    world.fired.add("repair")
    world.say(f"With Sunny holding the lantern, Luna {scene['repair']}.")
    world.fixed = True
    world.meters["stability"] = 1.0
    world.memes["relief"] = 1.0
    world.memes["community_trust"] = 1.0


def conclude(world: World) -> None:
    if "conclude" in world.fired:
        return
    world.fired.add("conclude")
    scene = world.facts["scene"]
    if not world.fixed:
        raise StoryError("A happy ending requires the danger and the shaking to be resolved.")
    world.say(
        f"The shaking stopped. {scene['ending']}. Everyone cheered, and Luna's little cape "
        f"fluttered in the calm air. {scene['lesson']}"
    )


def tell_story(world: World) -> None:
    hero = world.hero
    world.say(
        f"{world.facts['opening']} {hero.name} was a {hero.trait} little {hero.kind} superhero "
        f"with {hero.power}."
    )
    world.say(
        f"{hero.name} lived {world.place.phrase}, where friends knew that a small hero could "
        f"make a very large difference."
    )
    world.para()
    world.say(f"One bright day, {world.scar} caught {hero.name}'s eye.")
    notice_shake(world)
    hear_dialogue(world)
    world.para()
    investigate(world)
    rescue(world)
    repair(world)
    world.para()
    conclude(world)
    scene = world.facts["scene"]
    world.facts.update(
        problem=world.shake,
        cause=scene["clue"],
        repair=scene["repair"],
        ending=scene["ending"],
        lesson=scene["lesson"],
        resolved=world.fixed,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.hero
    return [
        f"Write a superhero story about {hero.name}, a {hero.kind} with {hero.power}, who notices a scar and a shake.",
        f"Tell a child-friendly Happy Ending story {world.place.phrase} where a superhero follows a scar to solve a danger.",
        f"Write a brave rescue story in which {hero.name} listens to a shake instead of ignoring it.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    scene = world.facts["scene"]
    return [
        QAItem(
            f"What did {hero.name} notice first?",
            f"{hero.name} noticed {world.scar}, and then heard that {world.shake}.",
        ),
        QAItem(
            "Why was the scar important?",
            f"The scar was important because {scene['clue']}; it pointed toward the part that needed help.",
        ),
        QAItem(
            f"How did {hero.name} help?",
            f"{hero.name} rescued someone from danger and then {scene['repair']}.",
        ),
        QAItem(
            "How did the story end?",
            f"The shaking stopped, {scene['ending']}, and everyone celebrated because the danger was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a scar?", "A scar is a mark left on skin or another surface after an old hurt has healed."),
        QAItem("What does shake mean?", "To shake means to move back and forth quickly."),
        QAItem("What is a superhero?", "A superhero is a brave helper with unusual abilities who protects others."),
        QAItem("Why should a hero investigate a strange sound?", "A strange sound can be a clue, so investigating carefully can reveal how to help safely."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "\n".join([
        "--- world model state ---",
        f"place={world.place.name}",
        f"hero={world.hero.name} ({world.hero.kind}, {world.hero.power})",
        f"scar={world.scar}",
        f"shake={world.shake}",
        f"danger={world.meters['danger']}",
        f"stability={world.meters['stability']}",
        f"fixed={world.fixed}",
        f"meters={world.meters}",
        f"memes={world.memes}",
        f"fired={sorted(world.fired)}",
    ])


ASP_RULES = r"""
place(P) :- place_name(P).
kind(K) :- kind_name(K).
power(X) :- power_name(X).
trait(T) :- trait_name(T).
valid(P,K,X,T) :- place(P), kind(K), power(X), trait(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for value in PLACES:
        lines.append(asp.fact("place_name", value))
    for value in KINDS:
        lines.append(asp.fact("kind_name", value))
    for value in POWERS:
        lines.append(asp.fact("power_name", value))
    for value in TRAITS:
        lines.append(asp.fact("trait_name", value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, k, x, t) for p in PLACES for k in KINDS for x in POWERS for t in TRAITS]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid/4."))
    cl = set(asp.atoms(model, "valid"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP valid combinations.")
    return 1


@dataclass
class _Args:
    place: Optional[str] = None
    kind: Optional[str] = None
    power: Optional[str] = None
    trait: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


CURATED = [
    StoryParams("Luna", "fox", "glowing paws", "brave", "rooftop"),
    StoryParams("Luna", "rabbit", "wind ears", "kind", "harbor"),
    StoryParams("Luna", "mouse", "a stretchy tail", "clever", "garden"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld about a scar, a shake, and a happy ending.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kind = args.kind or rng.choice(KINDS)
    return StoryParams(
        name=args.name or rng.choice(NAMES[kind]),
        kind=kind,
        power=args.power or rng.choice(POWERS),
        trait=args.trait or rng.choice(TRAITS),
        place=args.place or rng.choice(list(PLACES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} valid combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### {sample.params.name}: superhero variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
