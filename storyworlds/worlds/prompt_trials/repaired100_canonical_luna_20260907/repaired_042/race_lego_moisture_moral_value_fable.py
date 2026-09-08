#!/usr/bin/env python3
"""
A small fable about a LEGO race, a bead of moisture, and the moral value of
careful kindness.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class RaceTrack:
    name: str
    surface: str
    finish: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Luna"
    rival_name: str = "Pip"
    track: str = "the moonlit table"
    brick_color: str = "golden"
    scenario_id: int = 0
    telling_mode: int = 0
    detail_variant: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    track: Optional[RaceTrack] = None
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


CHILD_NAMES = ["Luna", "Mara", "Nia", "Tess", "Ollie", "Sora"]
RIVAL_NAMES = ["Pip", "Bram", "Milo", "Kip", "Jo"]
TRACKS = [
    RaceTrack("the moonlit table", "a smooth wooden board", "a blue ribbon"),
    RaceTrack("the window ledge", "a narrow painted sill", "a silver button"),
    RaceTrack("the garden bench", "a warm plank beneath the ivy", "a red cup"),
    RaceTrack("the library rug", "a thick woven path", "a paper star"),
]
BRICK_COLORS = ["golden", "green", "red", "blue", "purple"]

SCENARIOS = [
    {
        "title": "the shining shortcut",
        "opening": "Luna built a little LEGO racer with a golden nose and two bright wheels",
        "moisture": "a bead of moisture slipped from a watering can and shone across the track",
        "danger": "the bead made the shortcut slick and could send either racer into a pile of loose bricks",
        "temptation": "Luna noticed that Pip had not seen the wet place",
        "choice": "hide the moisture beneath a card and win before Pip noticed",
        "help": "point to the wet board and pause the race",
        "repair": "Luna dried the track with a cloth while Pip moved the loose bricks aside",
        "lesson": "a victory is not worth another person's hurt",
        "ending": "the racers crossed the dry finish together, their LEGO wheels clicking like tiny bells",
    },
    {
        "title": "the damp bridge",
        "opening": "Pip made a LEGO bridge so racers could leap over a line of books",
        "moisture": "moisture gathered beneath a cool glass and darkened three bridge bricks",
        "danger": "the damp bricks might loosen when a racer rolled over them",
        "temptation": "Luna could have started the race quickly and let the bridge fail behind her",
        "choice": "keep the damp place secret so her racer would gain a lead",
        "help": "warn Pip and rebuild the bridge with dry LEGO bricks",
        "repair": "they replaced the darkened pieces and tested the bridge with a gentle push",
        "lesson": "honesty is a stronger bridge than a secret advantage",
        "ending": "the rebuilt LEGO bridge held firm while both racers rolled beneath the smiling window",
    },
    {
        "title": "the wet wheel",
        "opening": "Luna polished a tiny LEGO racer and challenged Pip to a race around the toy village",
        "moisture": "a splash of moisture rested inside Luna's wheel well",
        "danger": "the wet wheel wobbled and could scatter the village houses",
        "temptation": "Luna could pretend not to notice and claim the fastest finish",
        "choice": "start the race before anyone saw the trembling wheel",
        "help": "tell Pip the truth and dry the wheel before racing",
        "repair": "Luna dried the wheel, and Pip gave her a spare axle from his own LEGO box",
        "lesson": "asking for help protects both the game and the friends who play it",
        "ending": "the two racers finished safely, and the tiny village stood smiling around them",
    },
]


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed if params.seed is not None else 17)
    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    track = next(t for t in TRACKS if t.name == params.track)
    world = World(track=track)

    child = world.add(Entity(
        "child",
        "child",
        params.child_name,
        meters={"care": 0.5, "race_time": 0.0},
        memes={"pride": 0.4, "kindness": 0.6, "worry": 0.0},
    ))
    rival = world.add(Entity(
        "rival",
        "friend",
        params.rival_name,
        meters={"race_time": 0.0},
        memes={"trust": 0.7, "hope": 0.6},
    ))
    racer = world.add(Entity(
        "racer",
        "LEGO racer",
        f"the {params.brick_color} LEGO racer",
        meters={"dryness": 1.0, "stability": 1.0},
        memes={"promise": 0.5},
    ))

    opening_variants = [
        f"On {track.name}, {scenario['opening']}.",
        f"At dawn, the children prepared a race on {track.name}. {scenario['opening'].capitalize()}.",
        f"The small racers waited beside {track.name}, and {scenario['opening'].lower()}.",
    ]
    world.say(opening_variants[params.telling_mode % len(opening_variants)])
    world.say(
        f"{child.label} loved the bright {params.brick_color} bricks, while {rival.label} checked the finish line at {track.finish}."
    )

    world.para()
    world.say(f"Then {scenario['moisture']}.")
    world.say(f"{scenario['danger'].capitalize()}.")
    child.memes["worry"] += 0.7
    racer.meters["dryness"] -= 0.5
    racer.meters["stability"] -= 0.3
    world.say(
        f'"The race is ready!" {rival.label} cried. "{child.label}, shall we count to three?"'
    )
    world.say(
        f'"Wait," {child.label} replied. "I see moisture where our wheels must go."'
    )
    world.say(
        f"{child.label} could {scenario['choice']}, but the Moral Value of the game mattered more than a quick prize."
    )

    world.para()
    world.say(f"{child.label} chose to {scenario['help']}.")
    world.say(
        f'"Thank you for telling me," {rival.label} said. "A fair race needs a safe track."'
    )
    world.say(
        f'"And a good friend does not win by letting a hidden danger wait," {child.label} answered.'
    )
    world.say(f"{scenario['repair'].capitalize()}.")
    racer.meters["dryness"] = 1.0
    racer.meters["stability"] = 1.0
    child.meters["care"] = 1.0
    child.memes["kindness"] = 1.0
    child.memes["pride"] = 0.2
    rival.memes["trust"] = 1.0

    world.para()
    world.say(f"The lesson was clear: {scenario['lesson'].capitalize()}.")
    world.say(
        f"{child.label} learned that Moral Value is not a trophy or a number; it is the good choice made when nobody would blame you for choosing badly."
    )
    endings = [
        f"At last, {scenario['ending']}.",
        f"When the sun warmed the room, {scenario['ending']}.",
        f"After the moisture was gone, {scenario['ending']}.",
    ]
    world.say(endings[(params.detail_variant + rng.randrange(3)) % len(endings)])

    world.facts.update(
        child=child,
        rival=rival,
        racer=racer,
        scenario=scenario,
        moral_value="Choose fairness and care over an unfair advantage.",
        resolved=True,
    )
    return world


WORLD_KNOWLEDGE = [
    QAItem(
        "What is LEGO?",
        "LEGO is a building toy made from small pieces that can connect to form models and structures.",
    ),
    QAItem(
        "What is moisture?",
        "Moisture is a small amount of water or another liquid found in or on something.",
    ),
    QAItem(
        "What is a moral value?",
        "A moral value is a belief about the kind and right way to act, such as being honest or fair.",
    ),
    QAItem(
        "Why can moisture be dangerous for a race track?",
        "Moisture can make a surface slippery or weaken pieces, so racers may wobble, fall, or break something.",
    ),
]


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    return [
        "Write a child-friendly fable about a LEGO race, hidden moisture, and a moral value.",
        f"Tell a fable in which {world.facts['child'].label} chooses fairness when {scenario['danger']}.",
        "Create a story where a race is delayed because caring for a friend matters more than winning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    rival = world.facts["rival"]
    racer = world.facts["racer"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            f"What did {child.label} notice before the race?",
            f"{child.label} noticed moisture on or near the track. It could have made the LEGO racer unsafe and caused the loose pieces or bridge to fail.",
        ),
        QAItem(
            f"Why did {child.label} pause the race?",
            f"{child.label} paused the race because {scenario['danger']}. The pause gave the friends time to make the track safe.",
        ),
        QAItem(
            f"How did {rival.label} respond?",
            f"{rival.label} thanked {child.label}, helped with the repair, and agreed that a fair race needs a safe track.",
        ),
        QAItem(
            "What Moral Value does the fable teach?",
            f"The fable teaches that {scenario['lesson']}. Fairness and care matter more than gaining a secret advantage.",
        ),
        QAItem(
            "How did the ending show that the problem was solved?",
            f"The moisture was removed or avoided, the LEGO racer became stable again, and {scenario['ending'].lower()}",
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


ASP_RULES = r"""
safe_race :- track_dry, racer_stable.
fair_choice :- tells_truth, helps_friend.
valid_story :- safe_race, fair_choice.
#show valid_story/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join([
        asp.fact("track_dry"),
        asp.fact("racer_stable"),
        asp.fact("tells_truth"),
        asp.fact("helps_friend"),
    ])


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable(params: StoryParams) -> None:
    if params.child_name == params.rival_name:
        raise StoryError("The two racers need different names.")
    if params.track not in {track.name for track in TRACKS}:
        raise StoryError("Choose a known race track.")
    if not params.child_name or not params.rival_name:
        raise StoryError("Both racers need names.")


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    found = bool(asp.atoms(model, "valid_story"))
    if not found:
        print("MISMATCH: ASP did not find a valid fair race.")
        return 1
    for scenario_id in range(len(SCENARIOS)):
        params = StoryParams(scenario_id=scenario_id)
        python_reasonable(params)
        sample = generate(params)
        if "Moral Value" not in sample.story:
            print("MISMATCH: generated story omitted Moral Value.")
            return 1
        if "moisture" not in sample.story.lower():
            print("MISMATCH: generated story omitted moisture.")
            return 1
        if "LEGO" not in sample.story:
            print("MISMATCH: generated story omitted LEGO.")
            return 1
    print("OK: ASP gate and generated stories pass.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A LEGO race fable about moisture and Moral Value.")
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--rival-name", choices=RIVAL_NAMES)
    ap.add_argument("--track", choices=[track.name for track in TRACKS])
    ap.add_argument("--brick-color", choices=BRICK_COLORS)
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
    child = args.child_name or rng.choice(CHILD_NAMES)
    rival = args.rival_name or rng.choice(RIVAL_NAMES)
    params = StoryParams(
        seed=None,
        child_name=child,
        rival_name=rival,
        track=args.track or rng.choice([track.name for track in TRACKS]),
        brick_color=args.brick_color or rng.choice(BRICK_COLORS),
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(3),
        detail_variant=rng.randrange(9),
    )
    python_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=list(WORLD_KNOWLEDGE),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    if world.track:
        lines.append(f"  track: {world.track.name}, surface={world.track.surface}")
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: type={entity.type}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  resolved: {world.facts.get('resolved')}")
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
    StoryParams(child_name="Luna", rival_name="Pip", track="the moonlit table", brick_color="golden", scenario_id=0),
    StoryParams(child_name="Mara", rival_name="Bram", track="the window ledge", brick_color="green", scenario_id=1),
    StoryParams(child_name="Nia", rival_name="Milo", track="the garden bench", brick_color="red", scenario_id=2),
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
        print("valid fair race:", bool(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
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
