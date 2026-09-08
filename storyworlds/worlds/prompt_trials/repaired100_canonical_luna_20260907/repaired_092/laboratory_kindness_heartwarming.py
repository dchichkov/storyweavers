#!/usr/bin/env python3
"""A heartwarming laboratory story about kindness, careful work, and a repaired friendship."""

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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.id


@dataclass(frozen=True)
class Laboratory:
    name: str
    feature: str
    safety_rule: str
    sound: str


@dataclass(frozen=True)
class Trial:
    key: str
    material: str
    problem: str
    worry: str
    kind_action: str
    test: str
    discovery: str
    repair: str
    final_image: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Dr. Mira"
    friend: str = "Pip"
    laboratory: str = "sunlit_lab"
    trial: str = "glowing_seed"
    mood: str = "gentle"
    opening_mode: int = 0
    dialogue_mode: int = 0
    turn_mode: int = 0


class World:
    def __init__(self, laboratory: Laboratory) -> None:
        self.laboratory = laboratory
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


LABORATORIES = {
    "sunlit_lab": Laboratory(
        name="the Little Lantern Laboratory",
        feature="wide windows filled the room with warm morning light",
        safety_rule="children worked behind the marked line and adults handled the hot equipment",
        sound="glass clicked softly and a small fan hummed",
    ),
    "garden_lab": Laboratory(
        name="the Garden Room Laboratory",
        feature="herbs grew in trays beneath the bright glass roof",
        safety_rule="everyone wore goggles and kept every sample in its labeled dish",
        sound="water drops tapped gently on the leaf trays",
    ),
    "river_lab": Laboratory(
        name="the Riverbank Laboratory",
        feature="blue water shone through the windows beside the worktables",
        safety_rule="spills were reported at once and no one hurried near the wet floor",
        sound="the river whispered beyond the open vents",
    ),
}

TRIALS = {
    "glowing_seed": Trial(
        key="glowing_seed",
        material="a tiny moonflower seed",
        problem="the seed stopped glowing inside its glass dish",
        worry="Pip thought the experiment had failed because of a careless mistake",
        kind_action="Luna listened to Pip without laughing and invited Pip to help check the setup",
        test="compare the dish with the notes, then place it beside a fresh lamp for one quiet minute",
        discovery="the lamp had been turned toward an empty shelf, so the seed had not received enough light",
        repair="they shared the lamp, moved the dish safely, and recorded the change together",
        final_image="the moonflower opened one silver petal while Pip and Luna smiled at the same notebook",
        lesson="Kindness makes room for the truth, especially when someone is already worried.",
    ),
    "color_water": Trial(
        key="color_water",
        material="a cup of clear water",
        problem="the water turned cloudy before the class could study it",
        worry="Pip whispered that everyone would blame the newest helper",
        kind_action="Luna thanked Pip for speaking up and asked everyone to search for a cause instead of a culprit",
        test="check the clean cups, read the labels, and gently compare the water with the control cup",
        discovery="a little flour from the nearby craft table had floated into the unlidded cup",
        repair="they covered the samples, cleaned the table, and made a fresh cup for Pip to examine",
        final_image="the clear cup caught the window light as Pip proudly wrote the first observation",
        lesson="Kindness turns an embarrassing accident into a chance to learn.",
    ),
    "echo_box": Trial(
        key="echo_box",
        material="a small wooden echo box",
        problem="the box made no sound during the listening test",
        worry="Pip feared that the group would laugh at the quiet result",
        kind_action="Luna told Pip that a quiet result was still useful and asked Pip to choose the next safe test",
        test="feel the box for a loose panel while Dr. Mira checks it with a cool, empty probe",
        discovery="a soft cloth had slipped between the panel and the box, muffling the sound",
        repair="they removed the cloth, thanked Pip for noticing the change, and repeated the test",
        final_image="a bright little note rang out, and Pip's laugh joined it beneath the laboratory lights",
        lesson="Kindness helps people share ideas before they feel perfectly sure.",
    ),
    "warm_stone": Trial(
        key="warm_stone",
        material="a smooth heat-storing stone",
        problem="the stone felt cold after the warming cycle",
        worry="Pip assumed Luna would be disappointed by the failed demonstration",
        kind_action="Luna said that mistakes belonged to the whole team and gave Pip the first careful observation",
        test="read the timer, inspect the insulated tray, and compare the stone with the covered sample",
        discovery="the tray lid had been closed before the cycle began, so warm air never reached the stone",
        repair="Dr. Mira reset the safe timer while Luna and Pip made a bright reminder card",
        final_image="the stone warmed in Pip's hands through its cloth wrap as the reminder card hung above it",
        lesson="Sharing responsibility can make a mistake feel smaller and a friendship feel stronger.",
    ),
}

HEROES = ("Luna", "Nia", "Sol", "Milo")
HELPERS = ("Dr. Mira", "Professor Imani", "Auntie Jo", "Mr. Vale")
FRIENDS = ("Pip", "Tavi", "Bea", "Oren")
MOODS = ("gentle", "hopeful", "bright", "quiet")

OPENINGS = (
    "The laboratory woke before the town did.",
    "Morning light slipped across the laboratory tables.",
    "In the kindest room Luna knew, every question was welcome.",
    "The little laboratory hummed softly as a new experiment began.",
    "A glass door opened, and warm air carried the smell of clean paper and growing herbs.",
)

DIALOGUES = (
    '"We can be careful and kind at the same time," said Dr. Mira.',
    '"Tell me what you noticed," Luna said. "You do not have to solve it alone."',
    '"A result is not a failure just because it surprised us," said Dr. Mira.',
    '"I was afraid to say something," Pip admitted. "Thank you for asking."',
    '"Let us help the experiment, and let us help one another," Luna promised.',
)

TURNS = (
    "That gentle question changed the experiment.",
    "Once Pip felt safe enough to speak, the missing clue came into view.",
    "The problem did not need a scolding; it needed patience and a closer look.",
    "Their kind pause became the turning point.",
    "The laboratory grew quieter, but the team's thinking grew clearer.",
)

ASP_RULES = r"""
laboratory(L) :- laboratory_fact(L).
trial(T) :- trial_fact(T).
kind_action(T) :- trial_fact(T), kindness(T).
safe_trial(T) :- trial_fact(T), supervised(T).
resolved(T) :- trial_fact(T), kindness(T), supervised(T).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("laboratory_fact", key) for key in LABORATORIES]
    lines += [asp.fact("trial_fact", key) for key in TRIALS]
    lines += [asp.fact("kindness", key) for key in TRIALS]
    lines += [asp.fact("supervised", key) for key in TRIALS]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a heartwarming laboratory story about kindness."
    )
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--friend")
    parser.add_argument("--laboratory", choices=sorted(LABORATORIES))
    parser.add_argument("--trial", choices=sorted(TRIALS))
    parser.add_argument("--mood", choices=sorted(MOODS))
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
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    friend = args.friend or rng.choice(FRIENDS)
    if hero == friend:
        friend = rng.choice([name for name in FRIENDS if name != hero])
    return StoryParams(
        seed=args.seed,
        hero=hero,
        helper=helper,
        friend=friend,
        laboratory=args.laboratory or rng.choice(list(LABORATORIES)),
        trial=args.trial or rng.choice(list(TRIALS)),
        mood=args.mood or rng.choice(MOODS),
        opening_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        turn_mode=rng.randrange(len(TURNS)),
    )


def tell(params: StoryParams) -> World:
    if params.laboratory not in LABORATORIES:
        raise StoryError(f"Unknown laboratory: {params.laboratory}")
    if params.trial not in TRIALS:
        raise StoryError(f"Unknown trial: {params.trial}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")

    laboratory = LABORATORIES[params.laboratory]
    trial = TRIALS[params.trial]
    world = World(laboratory)

    hero = world.add(Entity(params.hero, kind="character", type="child", location=laboratory.name))
    helper = world.add(Entity(params.helper, kind="character", type="adult", location=laboratory.name))
    friend = world.add(Entity(params.friend, kind="character", type="child", location=laboratory.name))
    sample = world.add(
        Entity(
            "sample",
            kind="experiment",
            type="sample",
            label=trial.material,
            location=laboratory.name,
            meters={"stability": 0.7},
        )
    )

    world.say(OPENINGS[params.opening_mode])
    world.say(
        f"On a {params.mood} morning, {hero.id}, {friend.id}, and {helper.id} worked in "
        f"{laboratory.name}, where {laboratory.feature}; {laboratory.sound}."
    )
    world.say(
        f"Today they were studying {sample.label}, but {trial.problem}. "
        f"{laboratory.safety_rule.capitalize()}."
    )
    world.para()

    world.say(f"{trial.worry.capitalize()}.")
    world.say(f"{DIALOGUES[params.dialogue_mode]}")
    world.say(f"{hero.id} chose to {trial.kind_action}.")
    world.say(f"Together they decided to {trial.test}.")
    world.say(f"The careful check showed that {trial.discovery}.")
    world.say(TURNS[params.turn_mode])

    world.para()
    world.say(f"{helper.id} helped them {trial.repair}.")
    world.say(
        f'"I thought I had ruined everything," {friend.id} said. '
        f'"You helped us notice what happened," {hero.id} replied.'
    )
    world.say(f"{trial.final_image}.")
    world.say(trial.lesson)

    hero.memes.update(kindness=2.0, courage=1.0, curiosity=1.0)
    friend.memes.update(trust=2.0, courage=1.0)
    sample.meters["stability"] = 1.0
    world.facts.update(
        hero=hero,
        helper=helper,
        friend=friend,
        sample=sample,
        laboratory=laboratory,
        trial=trial,
        resolved=True,
        kind=True,
        safe=True,
    )
    world.trace.extend(
        (
            f"laboratory:{laboratory.name}",
            f"trial:{trial.key}",
            f"problem:{trial.problem}",
            f"kind_action:{trial.kind_action}",
            f"discovery:{trial.discovery}",
            f"repair:{trial.repair}",
            "resolved:true",
        )
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    trial: Trial = world.facts["trial"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a heartwarming laboratory story about {hero.id} showing kindness to {friend.id}.",
            f"Include the experiment with {trial.material} and reveal the cause: {trial.discovery}.",
            "Use warm dialogue in which kindness changes what a worried character decides to do.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    trial: Trial = world.facts["trial"]
    laboratory: Laboratory = world.facts["laboratory"]
    return [
        QAItem(
            question=f"What were {hero.id} and {friend.id} studying?",
            answer=f"They were studying {trial.material} in {laboratory.name}.",
        ),
        QAItem(
            question=f"Why was {friend.id} worried?",
            answer=f"{friend.id} worried because {trial.worry}.",
        ),
        QAItem(
            question=f"How did {hero.id} show kindness?",
            answer=f"{hero.id} showed kindness by {trial.kind_action}.",
        ),
        QAItem(
            question="What did the careful test reveal?",
            answer=f"The test revealed that {trial.discovery}.",
        ),
        QAItem(
            question="How did the friends repair the problem?",
            answer=f"They repaired it when they {trial.repair}.",
        ),
        QAItem(
            question="What lesson did the laboratory teach them?",
            answer=trial.lesson,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    laboratory: Laboratory = world.facts["laboratory"]
    return [
        QAItem(
            question="Why should children follow laboratory safety rules?",
            answer=f"They should follow safety rules because {laboratory.safety_rule}.",
        ),
        QAItem(
            question="Why is kindness useful during an experiment?",
            answer="Kindness helps people speak honestly about mistakes, so the whole team can find evidence and solve the problem safely.",
        ),
        QAItem(
            question="What is a good response when an experiment surprises you?",
            answer="Stay calm, describe what happened, check the notes, and try a safe test instead of blaming someone.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {entry}" for entry in world.trace)
    for entity in world.entities.values():
        details = []
        if entity.location:
            details.append(f"location={entity.location}")
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.id} ({entity.kind}/{entity.type}) {' '.join(details)}")
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(trial="glowing_seed"),
    StoryParams(
        hero="Nia",
        helper="Professor Imani",
        friend="Bea",
        laboratory="garden_lab",
        trial="color_water",
        mood="bright",
        opening_mode=2,
        dialogue_mode=1,
        turn_mode=2,
    ),
    StoryParams(
        hero="Milo",
        helper="Auntie Jo",
        friend="Oren",
        laboratory="river_lab",
        trial="echo_box",
        mood="hopeful",
        opening_mode=3,
        dialogue_mode=3,
        turn_mode=4,
    ),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    show = (
        "#show laboratory/1.\n"
        "#show trial/1.\n"
        "#show kind_action/1.\n"
        "#show safe_trial/1.\n"
        "#show resolved/1.\n"
    )
    symbols = asp.one_model(asp_program(show))
    if not symbols:
        print("ASP produced no model.")
        return 1
    required = {"laboratory", "trial", "kind_action", "safe_trial", "resolved"}
    found = {symbol.name for symbol in symbols}
    if not required.issubset(found):
        print("ASP parity check failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated-story verification failed.")
            return 1
    print("OK: ASP program solved and generated stories passed.")
    return 0


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
    show = (
        "#show laboratory/1.\n"
        "#show trial/1.\n"
        "#show kind_action/1.\n"
        "#show safe_trial/1.\n"
        "#show resolved/1.\n"
    )

    if args.show_asp:
        print(asp_program(show))
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        symbols = asp.one_model(asp_program(show))
        print("\n".join(str(symbol) for symbol in symbols))
        return
    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise SystemExit("-n must be at least 1")
        samples = []
        for offset in range(args.n):
            local_seed = base_seed + offset
            params = resolve_params(args, random.Random(local_seed))
            params.seed = local_seed
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
