#!/usr/bin/env python3
"""
A standalone Storyweavers world about a friendship mystery and a careful machine.

Premise:
- Luna and her friend solve a mystery when a tiny garden mechanism stops working.
- A tempting shortcut causes a cautionary twist.
- Friendship and patient testing reveal the real cause.
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
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "the moonlit garden"
SEED_WORDS = {"mechanism"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""
    carried_by: Optional[str] = None

    def __post_init__(self) -> None:
        for key in ("distance", "looseness", "water", "light", "risk"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "trust", "curiosity", "courage", "patience", "joy"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    friend: str = "Milo"
    mystery: int = 0
    telling: int = 0
    twist: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    project: str
    trouble: str
    clue: str
    false_lead: str
    shortcut: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


CASES = [
    Case(
        project="a lantern path for the evening moths",
        trouble="the brass mechanism that opened the lantern shutters clicked once and froze",
        clue="a silver thread caught beneath the winding wheel",
        false_lead="a dark footprint beside the flower bed",
        shortcut="pull the shutter hard before the moon rose",
        discovery="found a tiny leaf wedged behind the wheel",
        cause="a gust had carried the leaf into the gear while Milo tested the handle",
        repair="removed the leaf with a twig, tightened the axle, and turned the handle slowly",
        proof="the shutters opened in a smooth circle and the lanterns shone along the path",
        lesson="A shortcut can hide a small danger; careful friends test a mechanism before forcing it.",
        ending="The moths floated through the glowing path while Luna and Milo watched side by side.",
    ),
    Case(
        project="a rain bell beside the herb beds",
        trouble="the little mechanism that lifted the bell rope stopped halfway",
        clue="a blue bead resting inside the wooden gear box",
        false_lead="a trail of wet paw marks leading toward the shed",
        shortcut="shake the whole box until the bell dropped",
        discovery="spotted a bead pinning the lifting cord against the gear",
        cause="Luna had placed the bead nearby for decoration, and a bump rolled it into the box",
        repair="opened the cover, freed the cord, and moved every loose decoration into a tray",
        proof="the bell rose and rang without rubbing the gear",
        lesson="When something is stuck, learn what is blocking it before making the whole machine move.",
        ending="The rain bell gave one bright note, and the garden seemed to smile with them.",
    ),
    Case(
        project="a seed sorter for the community garden",
        trouble="the wooden mechanism sorted every seed into the same bowl",
        clue="one cracked peg lying beneath the green lever",
        false_lead="a squirrel's hidden acorn pile near the fence",
        shortcut="push the lever faster so the seeds would separate",
        discovery="found the cracked peg keeping the sorting flap open",
        cause="a hurried push had bent the peg while Milo tried to finish before supper",
        repair="replaced the peg with a smooth spare and marked the safe stopping point",
        proof="round seeds rolled left, flat seeds rolled right, and none were crushed",
        lesson="More force cannot fix a part that needs careful attention.",
        ending="The two bowls filled neatly as Luna and Milo shared the first handful with the gardeners.",
    ),
    Case(
        project="a turning star map under the old oak",
        trouble="the star-map mechanism spun backward whenever the pointer reached the moon",
        clue="a knot in the red cord behind the map",
        false_lead="a bright beetle that kept circling the stand",
        shortcut="tie the pointer down so it could not move",
        discovery="traced the cord and found it looped around the turning pin",
        cause="the cord had slipped when Luna and Milo moved the stand together",
        repair="unwound the knot, reset the pin, and agreed to lift the stand by its handles",
        proof="the map turned forward and pointed to the real moon",
        lesson="A problem may begin during teamwork, but honest teamwork can also solve it.",
        ending="The map stopped beneath the moon, and neither friend needed to pretend they had known the answer alone.",
    ),
    Case(
        project="a tiny bridge for the water beetles",
        trouble="the bridge-lifting mechanism rose only on one side",
        clue="a wet reed tucked between two wooden teeth",
        false_lead="a missing pebble beside the stream",
        shortcut="press down on the high side until the bridge leveled",
        discovery="saw the reed wedged inside the lower gear",
        cause="the stream had carried the reed under the bridge during a sudden splash",
        repair="blocked the water, removed the reed, and placed a small guard beside the gear",
        proof="both sides lifted together and the beetles crossed safely",
        lesson="A gentle pause can protect a small machine and the living things around it.",
        ending="The beetles crossed the little bridge while the friends made a promise to watch the water first.",
    ),
]


@dataclass
class World:
    hero: Entity
    friend: Entity
    mechanism: Entity
    garden: Entity
    clue_object: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_world(params: StoryParams) -> World:
    hero = Entity(params.hero, "character", "child", params.hero, location="garden")
    friend = Entity(params.friend, "character", "child", params.friend, location="garden")
    mechanism = Entity(
        "garden_mechanism",
        "device",
        "mechanism",
        "the garden mechanism",
        location="garden",
    )
    garden = Entity("moonlit_garden", "place", "garden", "the moonlit garden")
    clue_object = Entity("clue", "thing", "clue", "the physical clue")
    return World(hero, friend, mechanism, garden, clue_object)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    h, f, m = world.hero, world.friend, world.mechanism
    case = CASES[params.mystery % len(CASES)]

    h.memes["curiosity"] += 1
    h.memes["worry"] += 1
    f.memes["trust"] += 1
    m.meters["risk"] = 1.0
    m.meters["looseness"] = 0.4
    m.location = "garden"
    world.clue_object.label = case.clue

    openings = [
        f"At dusk in {THEME}, {h.id} and {f.id} prepared {case.project}.",
        f"The moon was rising over {THEME} when {h.id} and {f.id} checked {case.project}.",
        f"{h.id} had invited {f.id} to help with {case.project} in {THEME}.",
        f"Silver light spilled over {THEME} as the two friends worked on {case.project}.",
    ]
    world.say(openings[params.telling % len(openings)])
    world.say(f"Then {case.trouble}. The unfinished project could not safely continue.")

    world.para()
    world.say(f"Near the device, they noticed {case.clue}. At the same time, {case.false_lead}.")
    world.say(f"{h.id} crouched beside the mechanism and studied the marks instead of guessing.")
    world.say(
        f"'{case.shortcut.capitalize()}?' asked {f.id}. "
        f"'{h.id}, that might damage the mechanism,' said {h.id}. "
        f"'Let's find out what is stopping it first.'"
    )
    h.memes["patience"] += 1
    f.memes["trust"] += 1
    world.say(f"They agreed that friendship meant telling the truth about the risk, even when a quick fix sounded exciting.")

    world.para()
    world.say(f"{h.id} followed the clue while {f.id} held a lantern. The false lead explained the {case.false_lead.split(' near')[0].lower()}, but it did not touch the machine.")
    world.say(f"Just as {f.id} reached for the handle, the cautionary twist appeared: {case.shortcut.capitalize()} made the mechanism shudder.")
    m.meters["risk"] = 2.0
    f.memes["worry"] += 1
    world.say(f"'{h.id}, stop!' cried {f.id}. 'The shortcut is making it worse.'")
    world.say(f"'{f.id}, thank you for warning me,' said {h.id}. 'We will undo that choice and look more closely.'")
    h.memes["courage"] += 1
    f.memes["courage"] += 1

    world.para()
    world.say(f"Together they {case.discovery}.")
    world.say(f"The mystery had a simple cause: {case.cause}.")
    m.meters["risk"] = 0.0
    m.meters["looseness"] = 0.0
    m.meters["water"] = 1.0
    world.say(f"'{case.cause.capitalize()}. I should have said what I was doing,' admitted {f.id}.")
    world.say(f"'{h.id}?' asked {f.id}. 'I am glad you told me before we broke it,' said {h.id}. 'Friends can fix mistakes when they share the truth.'")

    world.para()
    h.memes["joy"] += 2
    f.memes["joy"] += 2
    h.memes["trust"] += 2
    f.memes["trust"] += 2
    world.say(f"The friends {case.repair}.")
    world.say(f"They tested the result gently: {case.proof}.")
    world.say(f"Their lesson was clear: {case.lesson}")
    world.say(case.ending)

    world.facts.update(
        project=case.project,
        trouble=case.trouble,
        clue=case.clue,
        false_lead=case.false_lead,
        shortcut=case.shortcut,
        discovery=case.discovery,
        cause=case.cause,
        repair=case.repair,
        proof=case.proof,
        lesson=case.lesson,
        ending=case.ending,
        resolved=True,
        friendship=True,
        cautionary=True,
        twist=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What mystery interrupted the friends' project?",
            answer=f"The garden mechanism stopped working while they were preparing {f['project']}.",
        ),
        QAItem(
            question="What clue helped Luna and her friend solve the mystery?",
            answer=f"They followed {f['clue']}, which led them to the part blocking the mechanism.",
        ),
        QAItem(
            question="What was the cautionary twist?",
            answer=f"The quick idea to {f['shortcut']} made the mechanism shudder, showing that forcing it could cause more harm.",
        ),
        QAItem(
            question="What caused the mechanism to fail?",
            answer=f"The friends discovered that {f['cause']}.",
        ),
        QAItem(
            question="How did friendship help solve the problem?",
            answer=f"They warned each other, admitted what happened, and then {f['repair']}.",
        ),
        QAItem(
            question="How did they know the repair worked?",
            answer=f"They tested it gently and saw that {f['proof']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of parts that work together to make something move or perform a job.",
        ),
        QAItem(
            question="Why should people avoid forcing a stuck mechanism?",
            answer="Forcing a stuck mechanism can bend, crack, or break its parts. It is safer to find what is blocking it first.",
        ),
        QAItem(
            question="What does friendship mean in this story?",
            answer="Friendship means caring about someone, sharing the truth, listening to warnings, and helping repair mistakes.",
        ),
        QAItem(
            question="What is a cautionary lesson?",
            answer="A cautionary lesson warns us about a risky choice so we can make a safer choice next time.",
        ),
        QAItem(
            question="What is a twist in a mystery?",
            answer="A twist is a surprising change in what the characters think is happening, often caused by a new clue.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly mystery in {THEME} where friends investigate a broken mechanism while preparing {world.facts['project']}.",
        f"Include this physical clue: {world.facts['clue']}. Add a cautionary twist in which a shortcut creates extra risk.",
        "Show friendship through honest dialogue, careful listening, and a shared repair. End with a concrete image proving the mechanism works.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
    for entity in (world.hero, world.friend, world.mechanism, world.garden, world.clue_object):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:16} ({entity.kind:10}) "
            f"location={entity.location or '-'} meters={meters} memes={memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(moonlit_garden).
feature(friendship).
feature(cautionary).
feature(twist).
seed_word(mechanism).

valid_story :-
    setting(moonlit_garden),
    feature(friendship),
    feature(cautionary),
    feature(twist),
    seed_word(mechanism).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "moonlit_garden"),
            asp.fact("feature", "friendship"),
            asp.fact("feature", "cautionary"),
            asp.fact("feature", "twist"),
            asp.fact("seed_word", "mechanism"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program())
    asp_ok = any(atom.name == "valid_story" for atom in models)
    params = StoryParams(seed=17)
    sample = generate(params)
    required = ("mechanism", "friend", "careful", "mystery")
    prose_ok = all(word in sample.story.lower() for word in required)
    qa_ok = len(sample.story_qa) >= 4 and all(item.answer for item in sample.story_qa)
    if asp_ok and prose_ok and qa_ok:
        print("OK: ASP/Python parity and generated-story checks passed.")
        return 0
    print("MISMATCH: verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Friendship mystery about a mechanism in a moonlit garden."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--friend", default=None)
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


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nia", "Pia", "Mara", "Tess"])
    friend = args.friend or rng.choice(["Milo", "Oren", "Kai", "Juno", "Sol"])
    if hero == friend:
        raise StoryError("The hero and friend must have different names.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        friend=friend,
        mystery=offset % len(CASES),
        telling=(offset // len(CASES)) % 4,
        twist=(offset // (len(CASES) * 4)) % 3,
        ending=(offset // (len(CASES) * 4 * 3)) % 3,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(hero="Luna", friend="Milo", mystery=0),
    StoryParams(hero="Nia", friend="Oren", mystery=1),
    StoryParams(hero="Pia", friend="Kai", mystery=2),
    StoryParams(hero="Mara", friend="Juno", mystery=3),
    StoryParams(hero="Tess", friend="Sol", mystery=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
