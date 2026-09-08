#!/usr/bin/env python3
"""
A small mythic story world about an athletic washer who learns that a gamble
with a dangerous machine must be shared, not hidden.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
STORYWORLDS_ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(STORYWORLDS_ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    dialogue_turns: list[tuple[str, str]] = field(default_factory=list)

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


@dataclass
class StoryParams:
    washer_name: str
    runner_name: str
    elder_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    place: str
    athletic_task: str
    gamble: str
    danger: str
    sound: str
    warning: str
    sharing_action: str
    washer_action: str
    result: str
    lesson: str
    ending: str


WASHER_NAMES = ["Luna", "Mira", "Sable", "Nera", "Tala"]
RUNNER_NAMES = ["Pax", "Jori", "Ari", "Kito", "Bram"]
ELDER_NAMES = ["Oren", "Veya", "Ilya", "Sorin", "Maeve"]

TRIALS = [
    Trial(
        place="the Moonlit Laundry of the Hill People",
        athletic_task="race with a basket of silver linens",
        gamble="Luna bet she could spin the old washer faster than the wind",
        danger="the washer's heavy drum could break loose and hurt everyone nearby",
        sound="CLANK-CLANK, whirrrrr, and a deep GONG",
        warning="A brave heart does not make a broken machine safe.",
        sharing_action="told every runner and villager to step behind the stone line",
        washer_action="pulled the red cord and waited for the drum to become still",
        result="the race paused, the drum was secured, and nobody was hurt",
        lesson="courage grows wiser when it shares danger before facing it",
        ending="the quiet washer shone beneath the moon like a sleeping silver giant",
    ),
    Trial(
        place="the Cedar Valley Games",
        athletic_task="leap over three woven ropes",
        gamble="Luna wagered her golden ribbon that she could wash the team flags in one wild cycle",
        danger="the washer was packed too full, and its lid was shaking",
        sound="BUMP-BUMP, squeak, and a rattling RRRRUM",
        warning="A prize is never worth hiding a peril.",
        sharing_action="called the other athletes to carry the flags out and clear the floor",
        washer_action="switched off the washer before the shaking lid could spring open",
        result="the flags were washed safely in smaller loads",
        lesson="sharing a warning protects more treasures than winning a wager",
        ending="the clean flags rose together in the evening breeze",
    ),
    Trial(
        place="the River-Stone Arena",
        athletic_task="run around the arena before the river bell rang",
        gamble="Luna claimed she could power the ancient washer by running its wheel alone",
        danger="the wheel was cracked, and its sharp spoke might fly free",
        sound="KREEK, KREEK, then a sudden SNAP",
        warning="Do not ask a machine to carry a secret burden.",
        sharing_action="showed the crack to the whole team and asked for the repair rope",
        washer_action="braced the wheel with a wooden peg until the keeper arrived",
        result="the wheel stayed still, and the athletes finished their race on a safe path",
        lesson="a shared truth can stop a hidden break from becoming a disaster",
        ending="the river bell rang over the mended wheel and the cheering runners",
    ),
    Trial(
        place="the Sun Orchard Festival",
        athletic_task="throw bright scarves across the orchard",
        gamble="Luna gambled that one huge washer load could clean every scarf before sunset",
        danger="the wet scarves might tangle around the spinning drum",
        sound="SPLASH, thud, and a nervous tick-tick-tick",
        warning="Speed is a poor bargain when it leaves others in danger.",
        sharing_action="divided the scarves among the families and placed a watcher beside the machine",
        washer_action="stopped the drum when the first scarf twisted around the axle",
        result="the scarves were cleaned in gentle loads and no one reached into the machine",
        lesson="sharing work makes a task safer as well as faster",
        ending="scarves of every color fluttered above the orchard like small suns",
    ),
    Trial(
        place="the High Pass Athletic Shrine",
        athletic_task="climb the steps while carrying a basin of clean water",
        gamble="Luna dared the washer to finish a cycle before the mountain echo returned",
        danger="the washer's stone door had not latched",
        sound="WHOOM, rattle-rattle, and a hollow BOOM",
        warning="An echo can repeat a mistake, but a friend can stop it.",
        sharing_action="shouted the warning across the shrine so every climber could move away",
        washer_action="used the long wooden handle to close the door from a safe distance",
        result="the latch held, and the basin race continued without a reckless shortcut",
        lesson="warnings become powerful when they travel from one person to another",
        ending="the mountain returned their safe cheers in a long golden echo",
    ),
]

OPENINGS = [
    "In the first age, when machines still listened to the moon, a washer lived among the hill people.",
    "Long ago, the village athletes gathered where clean water ran beneath the stars.",
    "Before bells had names, the people held games beside an enormous iron washer.",
    "The old tales say that every useful machine has a spirit that must be treated with care.",
    "At dawn, the village prepared for a festival of running, lifting, and clean bright cloth.",
]

DIALOGUES = [
    (
        "Luna, will you gamble with a machine you have not inspected?",
        "I will not hide the risk. I will listen before I leap.",
        "Then I will share what I see, and we will choose together.",
    ),
    (
        "Stop! That sound is a warning, not a song.",
        "You are right. A strong athlete must know when to pause.",
        "I will tell the others so nobody stands near the danger.",
    ),
    (
        "Who heard the washer groan?",
        "I did, and I should have spoken sooner.",
        "Speaking now can still keep our friends safe.",
    ),
    (
        "The wager can wait. What does the washer need?",
        "It needs stillness, space, and careful eyes.",
        "And it needs all of us to know the plan.",
    ),
]


ASP_RULES = r"""
#show risk/1.
#show safe_plan/1.
risk(washer) :- gamble(washer), athletic_trial(washer), warning_needed(washer).
safe_plan(washer) :- risk(washer), shared_warning(washer), machine_stopped(washer).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("gamble", "washer"),
            asp.fact("athletic_trial", "washer"),
            asp.fact("warning_needed", "washer"),
            asp.fact("shared_warning", "washer"),
            asp.fact("machine_stopped", "washer"),
        ]
    )


def asp_program(show: str = "#show risk/1.\n#show safe_plan/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic athletic washer cautionary-sharing story world.")
    parser.add_argument("--washer-name", choices=WASHER_NAMES)
    parser.add_argument("--runner-name", choices=RUNNER_NAMES)
    parser.add_argument("--elder-name", choices=ELDER_NAMES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    washer = args.washer_name or rng.choice(WASHER_NAMES)
    runner = args.runner_name or rng.choice([name for name in RUNNER_NAMES if name != washer])
    elder = args.elder_name or rng.choice(ELDER_NAMES)
    if washer == runner or washer == elder or runner == elder:
        raise StoryError("The three story roles must have different names.")
    return StoryParams(washer_name=washer, runner_name=runner, elder_name=elder)


def _dialogue(world: World, speaker: Entity, line: str) -> None:
    world.dialogue_turns.append((speaker.name, line))
    world.say(f'{speaker.name} said, "{line}"')


def _setup_world(params: StoryParams) -> World:
    world = World()
    washer = world.add(Entity("washer", params.washer_name, "athletic washer"))
    runner = world.add(Entity("runner", params.runner_name, "teammate"))
    elder = world.add(Entity("elder", params.elder_name, "village elder"))
    washer.memes.update(courage=1.0, pride=0.8, caution=0.2)
    runner.memes.update(observation=0.8, trust=0.7)
    elder.memes.update(wisdom=1.0, care=0.9)
    world.facts.update(washer=washer, runner=runner, elder=elder)
    return world


def generate_story(world: World, params: StoryParams) -> None:
    washer: Entity = world.facts["washer"]
    runner: Entity = world.facts["runner"]
    elder: Entity = world.facts["elder"]

    key = params.seed if params.seed is not None else sum(ord(c) for c in params.washer_name + params.runner_name)
    trial = TRIALS[key % len(TRIALS)]
    opening = OPENINGS[(key // len(TRIALS)) % len(OPENINGS)]
    warning, reply, share_reply = DIALOGUES[(key // (len(TRIALS) * len(OPENINGS))) % len(DIALOGUES)]

    world.facts.update(trial=trial, opening=opening, warning=warning, dialogue_reply=reply, sharing_reply=share_reply)
    world.say(opening)
    world.say(
        f"{washer.name} was both a washer and an athletic champion. "
        f"At {trial.place}, {washer.name} prepared to {trial.athletic_task}."
    )
    world.say(f"{trial.gamble.capitalize()}. The wager glittered, but {trial.danger.capitalize()}.")

    washer.meters["risk"] = 1.0
    washer.memes["caution"] = 0.2
    world.para()
    _dialogue(world, elder, warning)
    _dialogue(world, washer, reply)
    world.say(f"Then the great washer cried, {trial.sound}.")
    _dialogue(world, runner, share_reply)
    world.say(f"{runner.name} noticed that the danger was not only {washer.name}'s problem; {trial.danger.capitalize()}.")

    world.para()
    world.say(f"First, {runner.name} {trial.sharing_action}.")
    world.say(f"Next, {washer.name} {trial.washer_action}.")
    washer.meters["risk"] = 0.0
    washer.memes["caution"] = 1.0
    elder.memes["trust"] = 1.0
    world.say(f"{elder.name} watched the machine settle. {trial.result.capitalize()}.")
    _dialogue(world, elder, "A warning shared in time is a gift to everyone.")
    _dialogue(world, washer, "I thought winning meant daring more. Now I know it can mean protecting more.")
    world.say(f"The village remembered that {trial.lesson}.")
    world.say(f"At sunset, {trial.ending}.")
    world.facts["resolved"] = True


def story_qa(world: World) -> list[QAItem]:
    washer: Entity = world.facts["washer"]
    runner: Entity = world.facts["runner"]
    elder: Entity = world.facts["elder"]
    trial: Trial = world.facts["trial"]
    return [
        QAItem(
            question=f"Who was {washer.name}, and what gamble did the athletic washer make?",
            answer=f"{washer.name} was an athletic washer who gambled that {trial.gamble.split(' that ', 1)[-1]}.",
        ),
        QAItem(
            question=f"What sound warned {runner.name} and {elder.name} that the washer was dangerous?",
            answer=f"The washer made the warning sound {trial.sound}.",
        ),
        QAItem(
            question=f"How did {runner.name} share the danger?",
            answer=f"{runner.name} {trial.sharing_action}.",
        ),
        QAItem(
            question="What changed by the end of the myth?",
            answer=f"The risk was stopped, {trial.result}, and the village learned that {trial.lesson}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should people stop a washer when it shakes or makes a strange sound?",
            answer="They should stop it because a shaking or noisy washer may be unsafe, and checking it can prevent injury.",
        ),
        QAItem(
            question="Why is sharing a warning important?",
            answer="Sharing a warning lets everyone move away from danger and helps the group make a safer choice.",
        ),
        QAItem(
            question="What does athletic mean?",
            answer="Athletic means connected with physical skill, strength, speed, or training.",
        ),
        QAItem(
            question="What is a gamble?",
            answer="A gamble is a risky choice whose result is uncertain.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    washer: Entity = world.facts["washer"]
    runner: Entity = world.facts["runner"]
    trial: Trial = world.facts["trial"]
    return [
        f"Write a child-friendly myth about {washer.name}, an athletic washer, making a gamble at {trial.place}.",
        f"Include the sound effect {trial.sound}, a cautionary warning, and {runner.name} sharing the danger with everyone.",
        f"End with this concrete mythic image: {trial.ending}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: name={entity.name} role={entity.role} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
    StoryParams("Luna", "Pax", "Oren"),
    StoryParams("Mira", "Jori", "Veya"),
    StoryParams("Sable", "Ari", "Ilya"),
]


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    risks = asp.atoms(model, "risk")
    safe_plans = asp.atoms(model, "safe_plan")
    if ("washer",) not in risks or ("washer",) not in safe_plans:
        print("MISMATCH: ASP did not derive the expected risk and safe plan.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if len(sample.world.dialogue_turns) < 4:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
    print("OK: ASP/Python parity and generated stories verified.")
    return 0


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
        print("risk:", asp.atoms(model, "risk"))
        print("safe_plan:", asp.atoms(model, "safe_plan"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(20, args.n * 20):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            index += 1
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

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
