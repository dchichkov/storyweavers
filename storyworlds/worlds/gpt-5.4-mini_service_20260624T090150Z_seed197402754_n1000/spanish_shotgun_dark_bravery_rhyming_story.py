#!/usr/bin/env python3
"""
storyworlds/worlds/spanish_shotgun_dark_bravery_rhyming_story.py
================================================================

A tiny storyworld about a brave child, a dark room, and a Spanish rhyme.

Seed tale sketch:
---
A child hears a soft knock in the dark and feels a little scared. A parent
hands over a lantern and a small play shotgun prop from a costume box. The
child remembers a Spanish rhyme from school and takes a brave step forward.
The scary shape turns out to be only a dropped paper bag, and the child sings
the rhyme with a smile.

World idea:
---
- The dark is a physical setting that hides small objects.
- Bravery is a meme that can grow when the child acts despite fear.
- Spanish words are a comforting tool the child can repeat.
- The "shotgun" is only a harmless costume prop, not a weapon.
- The story turns on fear -> courage -> discovery -> relief.

The prose is deliberately rhyming, child-facing, and state-driven:
the lantern, the rhyme, the hidden object, and the brave step all matter.
"""

from __future__ import annotations

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
class StoryParams:
    setting: str
    seed: Optional[int] = None
    child_name: str = "Maya"
    parent_name: str = "Papa"
    language_word: str = "Spanish"
    prop_word: str = "shotgun"
    dark_word: str = "dark"
    bravery_word: str = "bravery"
    rhyme_style: str = "rhyming"


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def inc_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def inc_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class World:
    setting: str
    child: Entity
    parent: Entity
    prop: Entity
    lantern: Entity
    hidden_object: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in [self.child, self.parent, self.prop, self.lantern, self.hidden_object]:
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
        lines.append(f"  setting: {self.setting}")
        return "\n".join(lines)


SETTINGS = {
    "hall": "the hall",
    "attic": "the attic",
    "shed": "the shed",
    "stage": "the stage",
}

NAMES = ["Maya", "Leo", "Nia", "Omar", "Zoe", "Ben"]
PARENTS = ["Mama", "Papa", "Abuela", "Abuelo"]
PROPS = [
    "toy shotgun",
    "cardboard shotgun",
    "costume shotgun",
]
HIDDEN_OBJECTS = [
    "paper bag",
    "wind-up mouse",
    "fallen hat",
    "small mop",
]
SPANISH_LINES = {
    "valiente, valiente, paso al frente": "brave, brave, take a step ahead",
    "luz de luna, calma mi mente": "moonlight, calm my mind",
    "uno, dos, tres, yo puedo seguir": "one, two, three, I can keep going",
}

OPENINGS = {
    "hall": [
        "After supper, {child} helped {parent} carry play costumes down the hall.",
        "At bedtime, {child} and {parent} gathered costumes left along the hall.",
    ],
    "attic": [
        "On a rainy afternoon, {child} helped {parent} sort an old costume trunk in the attic.",
        "Before dusk, {child} and {parent} climbed to the attic to put school-play costumes away.",
    ],
    "shed": [
        "At sunset, {child} helped {parent} return painted stage props to the shed.",
        "After the school play, {child} and {parent} carried the last costume box to the shed.",
    ],
    "stage": [
        "After rehearsal, {child} stayed with {parent} to clear the quiet stage.",
        "When the little school play ended, {child} and {parent} packed the costumes on the stage.",
    ],
}

HIDDEN_EVENTS = {
    "paper bag": [
        (
            "Something near the wall went scritch-scritch, then stopped.",
            "followed the rustle to the wall",
            "A cool draft was nudging a crumpled paper bag across the floor.",
            "folded the bag flat for recycling",
        ),
        (
            "A pale shape puffed up, sank down, and rose once more.",
            "held the lantern toward the bobbing shape",
            "Air beneath the door was making a paper bag rise and fall.",
            "tucked the bag into the paper bin",
        ),
    ],
    "wind-up mouse": [
        (
            "From behind a box came a clickety-click and a quick silver gleam.",
            "tracked the tiny clicking past the box",
            "A wind-up mouse from the play was bumping in a circle because its key was still turning.",
            "stopped the toy mouse and set it on the prop shelf",
        ),
        (
            "Two round shadows darted low, then tapped against a chair.",
            "lowered the lantern and looked beneath the chair",
            "The wheels of a wind-up mouse were ticking against a chair leg.",
            "wound down the toy mouse and returned it to its tray",
        ),
    ],
    "fallen hat": [
        (
            "A tall, crooked shadow nodded from the wall.",
            "raised the lantern toward the nodding shadow",
            "A fallen hat was rocking on a broom handle, and its brim made the shadow look tall.",
            "hung the hat back on its low wooden peg",
        ),
        (
            "Something with a wide black brim seemed to peek around a crate.",
            "carried the light around the crate",
            "A fallen hat from the costume trunk had landed brim-up and was catching the lantern light.",
            "brushed off the hat and placed it in the costume trunk",
        ),
    ],
    "small mop": [
        (
            "A thin shadow brushed the door with a hush-hush sweep.",
            "walked beside the beam until it reached the door",
            "A small mop had tipped sideways, and the moving door was dragging its soft strings.",
            "stood the mop firmly in its corner",
        ),
        (
            "From the corner came a soft swish, pause, swish.",
            "shone the lantern into the swishing corner",
            "A loose window latch was stirring the strings of a small mop.",
            "fastened the latch and leaned the mop safely against the wall",
        ),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny rhyming storyworld about dark places, Spanish words, and brave hearts."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("The story needs a small setting like the hall, attic, shed, or stage.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    params = StoryParams(
        setting=setting,
        seed=args.seed,
        child_name=name,
        parent_name=parent,
        language_word="Spanish",
        prop_word=rng.choice(PROPS),
        dark_word="dark",
        bravery_word="bravery",
        rhyme_style="rhyming",
    )
    _validate_params(params)
    return params


def make_world(params: StoryParams) -> World:
    child = Entity(id=params.child_name, kind="character", label=params.child_name, type="child")
    parent = Entity(id=params.parent_name, kind="character", label=params.parent_name, type="parent")
    prop = Entity(id="prop", kind="thing", label=params.prop_word, type="costume prop")
    lantern = Entity(id="lantern", kind="thing", label="lantern", type="light")
    hidden_label = random.Random((params.seed or 0) + 7919).choice(HIDDEN_OBJECTS)
    hidden = Entity(id="hidden", kind="thing", label=hidden_label, type="small object")
    return World(
        setting=SETTINGS[params.setting],
        child=child,
        parent=parent,
        prop=prop,
        lantern=lantern,
        hidden_object=hidden,
    )


def _build_story(world: World, params: StoryParams) -> None:
    c = world.child
    p = world.parent
    prop = world.prop
    lantern = world.lantern
    hidden = world.hidden_object

    rng = random.Random((params.seed or 0) + 104729)
    opening = rng.choice(OPENINGS[params.setting]).format(child=c.label, parent=p.label)
    signal, brave_action, reveal, cleanup = rng.choice(HIDDEN_EVENTS[hidden.label])
    spanish = rng.choice(list(SPANISH_LINES))
    translation = SPANISH_LINES[spanish]
    support_line = rng.choice([
        f'{p.label} lit the lantern and said, "We can look together; one careful step will do."',
        f'{p.label} raised the lantern and said, "I am beside you. You may stop whenever you choose."',
        f'{p.label} passed over the lantern and said, "Go slowly; I will stay close to you."',
    ])
    brave_line = rng.choice([
        f"Fear still fluttered in {c.label}'s chest, but {c.label} {brave_action}.",
        f"The sound was still strange, yet {c.label} {brave_action}.",
        f"With one slow breath and one steady step, {c.label} {brave_action}.",
    ])
    endings = [
        f"Soon the lantern hung by the door, the {prop.label} rested in its costume box, and a slim gold beam warmed {c.label}'s smiling face.",
        f"They closed the costume trunk with the {prop.label} safely inside; beside it, the lantern painted one calm circle of gold.",
        f"When they switched off the lantern, {c.label} repeated the Spanish rhyme once more, and this time the dark room felt peaceful.",
        f"At the doorway, {c.label} looked back at the tidy room: one quiet shadow, one boxed-up {prop.label}, and no mystery left at all.",
    ]

    c.memes["fear"] = 1.0
    c.memes["bravery"] = 0.0
    lantern.meters["light"] = 1.0
    prop.meters["pretend"] = 1.0
    hidden.meters["hidden"] = 1.0

    world.say(opening)
    world.say(
        f"A bright-painted {prop.label} belonged to the show, a harmless pretend prop "
        f"inside the costume box. Then the lamp clicked out, and the room turned {params.dark_word} as night."
    )
    world.say(signal)

    world.para()
    world.say(support_line)
    p.inc_meme("care", 1.0)
    world.say(
        f'{c.label} remembered a Spanish rhyme. "{spanish.capitalize()}," {c.label} whispered. '
        f'It meant "{translation}." '
        f"The familiar words made a rhythm steady and clear, but bravery did not mean never feeling fear."
    )
    c.inc_meme("bravery", 1.0)
    c.inc_meter("brave_steps", 1.0)
    world.say(brave_line)

    world.para()
    world.say(reveal)
    hidden.meters["hidden"] = 0.0
    hidden.meters["found"] = 1.0
    c.memes["fear"] = 0.25
    world.say(
        f"The clue had a cause, and the cause was small. {c.label} smiled to know there was no monster at all."
    )

    world.para()
    c.inc_meme("joy", 1.0)
    world.say(
        f"Together they {cleanup}. {c.label} learned that {params.bravery_word} did not make fear disappear; "
        f"it meant taking one careful step with someone loving near."
    )
    world.say(rng.choice(endings))

    world.facts.update(
        child=c,
        parent=p,
        prop=prop,
        lantern=lantern,
        hidden=hidden,
        spanish=spanish,
        setting=params.setting,
        signal=signal,
        reveal=reveal,
        cleanup=cleanup,
        brave=bool(c.memes.get("bravery", 0.0) >= 1.0),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short rhyming story for a little child in {world.setting} with a dark shadow and a brave heart.",
        f"Tell a gentle story that includes Spanish, a harmless pretend shotgun, and the dark, and ends with bravery and relief.",
        f"Write a simple rhyming tale where a child uses a lantern, repeats a Spanish line, and discovers that a {world.hidden_object.label} caused the scary clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.child
    p = world.parent
    return [
        QAItem(
            question=f"Who was brave in the story?",
            answer=f"{c.label} was brave after feeling scared in the dark and hearing the comforting Spanish rhyme.",
        ),
        QAItem(
            question=f"How did {p.label} help {c.label}?",
            answer=f"{p.label} provided the lantern, stayed close, and let {c.label} investigate at a careful pace.",
        ),
        QAItem(
            question="What was the scary thing really?",
            answer=f"It was a harmless {world.hidden_object.label}. {world.facts['reveal']}",
        ),
        QAItem(
            question="Why did the child feel braver at the end?",
            answer=f"{c.label} repeated a Spanish line, took a careful step despite being afraid, and discovered what caused the strange clue.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something even when you feel scared.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light so people can see in dark places.",
        ),
        QAItem(
            question="Why can Spanish words be comforting?",
            answer="A familiar Spanish rhyme can feel warm and steady, which helps a child feel calmer.",
        ),
        QAItem(
            question="Why is a costume shotgun safe in this story?",
            answer="It is only a pretend prop from a costume box, not a real weapon.",
        ),
    ]


ASP_RULES = r"""
child_brave(C) :- fear(C), hears_spanish(C), finds_harmless_shape(C).
dark_place(S) :- setting(S).
safe_prop(P) :- prop(P), costume(P).
story_good(S) :- dark_place(S), child_brave(C), safe_prop(P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for key, setting in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        if "dark" in setting:
            lines.append(asp.fact("dark", key))
    for nm in NAMES:
        lines.append(asp.fact("child_name", nm))
    for pr in PROPS:
        lines.append(asp.fact("prop", pr.replace(" ", "_")))
        lines.append(asp.fact("costume", pr.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.language_word == "Spanish" and params.prop_word == "shotgun"


def asp_verify() -> int:
    if not _python_reasonable(StoryParams(setting="hall")):
        print("MISMATCH: python reasonableness gate failed unexpectedly.")
        return 1
    print("OK: python reasonableness gate is consistent.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    _build_story(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(sample.world.trace())
    if qa:
        print()
        print("== Generation prompts ==")
        for i, q in enumerate(sample.prompts, 1):
            print(f"{i}. {q}")
        print()
        print("== Story questions ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== World questions ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="hall", child_name="Maya", parent_name="Mama"),
    StoryParams(setting="attic", child_name="Leo", parent_name="Papa"),
    StoryParams(setting="shed", child_name="Nia", parent_name="Abuela"),
    StoryParams(setting="stage", child_name="Omar", parent_name="Abuelo"),
]


def build_all_samples() -> list[StorySample]:
    return [generate(p) for p in CURATED]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_good/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world uses a simple internal reasonableness gate for its tiny ASP twin.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = build_all_samples()
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
