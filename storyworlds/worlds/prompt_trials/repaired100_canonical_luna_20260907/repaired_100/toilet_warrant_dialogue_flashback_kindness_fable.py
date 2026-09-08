#!/usr/bin/env python3
"""
A small fable-like storyworld about a toilet, a warrant, a remembered promise,
and the kindness needed to repair a frightened mistake.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_repo_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_repo_root))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Washroom:
    name: str
    toilet_count: int
    clean: bool = True
    door_stuck: bool = False


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None


@dataclass
class World:
    washroom: Washroom
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


SETTINGS = {
    "schoolhouse": Washroom("the schoolhouse washroom", 2, True, False),
    "garden_hall": Washroom("the garden hall washroom", 1, True, False),
    "moon_fair": Washroom("the moon-fair washroom", 3, True, False),
}

NAMES = ["Luna", "Pip", "Mina", "Toby", "Ivy", "Milo", "Sage", "Nell"]

INCIDENTS = [
    {
        "premise": "the little toilet began to splash water onto the floor before the evening story circle",
        "conflict": "a paper warrant on the caretaker's desk said the first person who caused a mess must answer for it",
        "mistake": "Luna picked up the warrant and hurried toward her friend before asking what had happened",
        "clue": "the toilet handle was crooked, and a blue thread from the caretaker's cleaning cloth was caught beneath it",
        "repair": "they closed the water valve, dried the floor with towels, and showed the caretaker the crooked handle and blue thread",
        "ending": "the repaired toilet shone beside a small blue kindness ribbon",
        "lesson": "a warrant may ask for careful attention, but it is not proof that a frightened neighbor is guilty",
    },
    {
        "premise": "the only toilet in the garden hall refused to flush during the busiest part of the picnic",
        "conflict": "a signed warrant asked the finder to report whoever had used it last",
        "mistake": "Luna treated the warrant like a verdict and accused her friend beside the washbasin",
        "clue": "a fallen leaf covered the flush sensor, while the visitor book showed several families had used the toilet",
        "repair": "they moved the leaf, washed their hands, and asked the hall keeper to inspect the sensor instead of blaming one person",
        "ending": "the clean toilet flushed softly while the visitor book gained a page titled KIND QUESTIONS",
        "lesson": "shared trouble needs shared care, not a hasty accusation",
    },
    {
        "premise": "a small toy boat slipped into the toilet bowl during a game of pretend sailing",
        "conflict": "the toy's owner feared the warrant on the wall would make someone pay for the mistake",
        "mistake": "Luna hid the boat and let her friend believe that telling the truth would bring punishment",
        "clue": "a flashback returned to the moment when the caretaker had promised, 'Tell me early, and I can help safely'",
        "repair": "Luna told the truth, and the children called the caretaker, who removed the boat with a safe tool",
        "ending": "the toy boat sailed again in a basin while the toilet stayed clear and quiet",
        "lesson": "kind honesty gives helpers time to prevent a small accident from growing",
    },
    {
        "premise": "rainwater dripped through the roof above the washroom toilet",
        "conflict": "the warrant warned that careless people must not leave wet floors behind",
        "mistake": "Luna blamed her friend for the puddle because the friend was standing nearest the toilet",
        "clue": "a flashback showed the same roof drip from the previous storm, before either child had entered",
        "repair": "they placed a warning sign, kept everyone away from the puddle, and fetched the hall keeper to mend the roof",
        "ending": "the dry floor reflected a yellow sign that read THANK YOU FOR LOOKING CLOSELY",
        "lesson": "kindness begins when we search for the true cause",
    },
    {
        "premise": "the washroom door stuck while a nervous visitor waited inside",
        "conflict": "a warrant about keeping the washroom safe made Luna worry that opening the door would make the trouble worse",
        "mistake": "she pulled hard without speaking, which made the visitor more frightened",
        "clue": "a flashback reminded her that the caretaker had taught, 'Knock, speak calmly, and get an adult when a door is stuck'",
        "repair": "Luna spoke through the door, asked the visitor to step back, and called the caretaker, who opened it safely",
        "ending": "the door swung freely, and a hand-painted KINDNESS arrow pointed toward the help bell",
        "lesson": "gentle words and the right helper are stronger than a frightened tug",
    },
    {
        "premise": "a paper star fell into the toilet just before the lantern parade",
        "conflict": "the caretaker's warrant requested a report about anything that might block the pipes",
        "mistake": "Luna reached in with a stick before telling anyone",
        "clue": "a flashback recalled the caretaker explaining that tools and pipes needed adult hands",
        "repair": "Luna stopped, warned others away, and asked the caretaker to remove the star with proper equipment",
        "ending": "the rescued star glittered on the parade banner while the toilet remained ready for everyone",
        "lesson": "kindness protects people by stopping unsafe help as well as by offering help",
    },
]

OPENINGS = [
    "At dawn,",
    "On the day of the village fair,",
    "Just before the story circle,",
    "While lanterns were being hung,",
    "After a warm rain,",
    "Near the end of a busy afternoon,",
]

DIALOGUE_LINES = [
    ("Please tell me what you saw before we decide who is responsible.", "I saw the trouble, but I did not see who caused it."),
    ("The warrant asks us to report carefully, not to point at a friend.", "Then let us look for a fact that can help."),
    ("I was scared and hurried. Can we begin again?", "Yes. Kindness means we can repair a rushed mistake."),
]

REFLECTIONS = [
    "The friends learned that a rule can protect a place, while kindness protects the people inside it.",
    "After that day, they read warnings slowly and asked questions before making guesses.",
    "The warrant stayed useful because nobody treated it as a weapon.",
    "Their small washroom became safer because truth, patience, and help worked together.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable-like toilet and warrant storyworld.")
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--name")
    parser.add_argument("--friend")
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    hero = args.name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != hero]
    friend = args.friend or rng.choice(choices)
    if hero == friend:
        raise StoryError("hero and friend must have different names")
    return StoryParams(setting, hero, friend)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError(f"unknown setting: {params.setting}")
    if params.hero_name == params.friend_name:
        raise StoryError("hero and friend must have different names")

    template = SETTINGS[params.setting]
    washroom = Washroom(template.name, template.toilet_count, template.clean, template.door_stuck)
    world = World(washroom)
    hero = world.add(Entity(params.hero_name, "character", "rabbit", params.hero_name))
    friend = world.add(Entity(params.friend_name, "character", "badger", params.friend_name))
    toilet = world.add(Entity("toilet", "object", "toilet", "the toilet"))
    warrant = world.add(Entity("warrant", "document", "warrant", "the warrant"))

    rng = random.Random(params.seed or 0)
    incident = rng.choice(INCIDENTS)
    dialogue = rng.choice(DIALOGUE_LINES)
    reflection = rng.choice(REFLECTIONS)

    hero.meters.update(care=0.4, haste=0.8)
    friend.meters.update(worry=0.8)
    hero.memes.update(impatience=1, kindness=0)
    friend.memes.update(fear=1, trust=0)

    world.say(
        f"{OPENINGS[rng.randrange(len(OPENINGS))]} {hero.id} was helping near {world.washroom.name}. "
        f"{friend.id} was nearby, carrying a basket of clean towels."
    )
    world.say(f"Then {incident['premise']}. A caretaker had posted {warrant.label}, asking everyone to keep the place safe.")
    world.para()

    world.say(f"The trouble grew because {incident['conflict']}. {incident['mistake']}.")
    world.say(f'"{dialogue[0]}" {hero.id} said.')
    world.say(f'"{dialogue[1]}" {friend.id} answered.')
    world.say(f"That exchange changed Luna's plan: instead of accusing anyone, the friends searched for evidence.")
    world.say(f"They found this clue: {incident['clue']}.")

    world.para()
    world.say(
        f"A flashback came to {hero.id}: the caretaker had once said, "
        f'"A rule is a lantern. It helps us see what to do, but it does not tell us to stop caring."'
    )
    world.say(f'"I was scared and hurried. Can we begin again?" {hero.id} asked.')
    world.say(f'"Yes," {friend.id} said. "Kindness means we can repair a rushed mistake."')
    world.say(f"Together, they {incident['repair']}.")

    hero.meters["haste"] = 0.0
    hero.memes["impatience"] = 0
    hero.memes["kindness"] = 1
    friend.meters["worry"] = 0.1
    friend.memes["fear"] = 0
    friend.memes["trust"] = 1

    world.para()
    world.say(f"The warrant had helped them remember safety, but kindness had helped them remember one another.")
    world.say(f"{reflection} The lesson was that {incident['lesson']}.")
    world.say(f"At sunset, {incident['ending']}.")

    world.facts.update(
        hero=hero,
        friend=friend,
        toilet=toilet,
        warrant=warrant,
        incident=incident,
        reflection=reflection,
        setting=world.washroom,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    return [
        f"Write a child-friendly fable involving a toilet and a warrant where {incident['premise']}.",
        "Include dialogue, a flashback, and kindness that changes a hurried decision.",
        f"End with a concrete image showing that {incident['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    incident = f["incident"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        QAItem(
            question=f"What caused the problem involving {hero.label} and {friend.label}?",
            answer=f"The problem began because {incident['conflict']}. {hero.label} then made a hurried mistake: {incident['mistake']}.",
        ),
        QAItem(
            question="What did the warrant mean in the story?",
            answer="The warrant was a request to report carefully and protect the washroom. It was not proof that a particular friend was guilty.",
        ),
        QAItem(
            question="How did the dialogue change what the friends did?",
            answer=f"They spoke honestly instead of accusing one another. After {friend.label} asked for facts, they searched together and found that {incident['clue']}.",
        ),
        QAItem(
            question="What did the flashback teach the friends?",
            answer="The flashback reminded them to use the safe method they had learned before and to ask a trusted adult when the trouble required adult help.",
        ),
        QAItem(
            question="How did kindness repair the situation?",
            answer=f"They stopped blaming and {incident['repair']}. This protected both the washroom and the feelings of the people using it.",
        ),
        QAItem(
            question="What showed that the problem was resolved?",
            answer=f"At the end, {incident['ending']}. That image showed that their careful action had made a lasting difference.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toilet?",
            answer="A toilet is a fixture used to carry away human waste safely and hygienically.",
        ),
        QAItem(
            question="What is a warrant?",
            answer="A warrant is a formal written authorization or request. In this fable, it asked people to report a safety concern; it was not evidence of guilt by itself.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a moment in a story that returns to something that happened earlier.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating others with care, respect, and helpful attention, especially when someone is worried or has made a mistake.",
        ),
        QAItem(
            question="Why should people ask for help with unsafe washroom problems?",
            answer="A trusted adult or trained helper may know how to protect people, avoid damage, and repair pipes or fixtures safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---", f"setting: {world.washroom.name}"]
    for entity in world.entities.values():
        lines.append(f"{entity.label}: meters={entity.meters} memes={entity.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
feature(dialogue).
feature(flashback).
feature(kindness).
object(toilet).
document(warrant).
safe_rule :- feature(kindness), object(toilet), document(warrant).
#show feature/1.
#show object/1.
#show document/1.
#show safe_rule/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "flashback"),
            asp.fact("feature", "kindness"),
            asp.fact("object", "toilet"),
            asp.fact("document", "warrant"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show feature/1.\n#show object/1.\n#show document/1.\n#show safe_rule/0."))
    features = set(asp.atoms(model, "feature"))
    objects = set(asp.atoms(model, "object"))
    documents = set(asp.atoms(model, "document"))
    safe = asp.atoms(model, "safe_rule")
    expected = {("dialogue",), ("flashback",), ("kindness",)}
    if features != expected or objects != {("toilet",)} or documents != {("warrant",)} or safe != [()]:
        print("Mismatch in ASP verification.")
        return 1

    rng = random.Random(17)
    params = resolve_params(build_parser().parse_args([]), rng)
    params.seed = 17
    sample = generate(params)
    required = ("toilet", "warrant", "flashback", "kindness")
    if not all(word in sample.story.lower() for word in required):
        print("Generated story is missing a required narrative instrument.")
        return 1
    if len(sample.story_qa) < 4:
        print("Generated story lacks sufficient story QA.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show feature/1.\n#show object/1.\n#show document/1.\n#show safe_rule/0."))
        print(sorted(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(sorted(SETTINGS)):
            params = StoryParams(setting, "Luna", "Pip", base_seed + index)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 30)
        while len(samples) < args.n and index < limit:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
