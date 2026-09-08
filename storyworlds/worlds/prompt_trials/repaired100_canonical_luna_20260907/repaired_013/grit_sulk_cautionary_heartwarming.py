#!/usr/bin/env python3
"""
A cautionary, heartwarming story world about grit, sulking, and learning to ask
for help before a small problem becomes a lonely one.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "the little hill village"
    hero: str = "Luna"
    friend: str = "Pip"
    helper: str = "Grandma Fern"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "the little hill village": {
        "tags": {"village", "garden", "heartwarming"},
        "mood": "sunny and close-knit",
    },
    "the windy harbor": {
        "tags": {"harbor", "rope", "heartwarming"},
        "mood": "bright and breezy",
    },
    "the lantern meadow": {
        "tags": {"meadow", "lanterns", "heartwarming"},
        "mood": "soft and golden",
    },
}

NAMES = ["Luna", "Milo", "Nia", "Tess", "Ollie"]
FRIENDS = ["Pip", "Juno", "Bea", "Rafi", "Moss"]
HELPERS = ["Grandma Fern", "Uncle Sol", "Auntie May"]


@dataclass(frozen=True)
class Arc:
    title: str
    premise: str
    problem: str
    dialogue: str
    choice: str
    action: str
    result: str
    ending: str
    problem_answer: str
    choice_answer: str
    result_answer: str


ARCS = [
    Arc(
        title="The Kite on the Tall Fence",
        premise="Luna had promised to hang a bright red kite above the village fair.",
        problem="When the wind caught it, the kite tangled on the tallest fence, and Luna's first pull only tightened the knot.",
        dialogue="\"I can fix it alone,\" Luna said. \"You do not have to,\" Pip replied. \"But you can stand beside me while I try.\"",
        choice="Luna began to sulk behind the tool shed, yet she heard Pip's gentle answer and admitted that the knot frightened her.",
        action="They gathered a short ladder, a soft cloth, and Grandma Fern's patient advice, then loosened one loop at a time.",
        result="The kite came free without a tear, and Luna learned that grit meant trying again with care, not pretending she never needed help.",
        ending="the red kite fluttered above the fair while Luna and Pip held the ladder together",
        problem_answer="A gust tangled Luna's red kite tightly on the tallest fence.",
        choice_answer="Luna stopped sulking, told Pip she was worried, and accepted careful help instead of pulling harder alone.",
        result_answer="With a ladder, cloth, and patient teamwork, the friends freed the kite and understood that grit can include asking for help.",
    ),
    Arc(
        title="The Garden Gate That Stuck",
        premise="Luna wanted to open the garden gate before the thirsty seedlings drooped.",
        problem="The wooden gate had swollen after rain, and every angry shove made the latch scrape more deeply.",
        dialogue="\"The gate is being mean,\" Luna grumbled. \"The gate is only stuck,\" Pip said. \"Let us listen to it together.\"",
        choice="Luna crossed her arms and sulked, but then she noticed the smallest seedlings bending toward the dry soil.",
        action="She asked Grandma Fern for oil and a wedge, while Pip cleared pebbles from the hinge and Luna pushed only when the wood gave a little.",
        result="The gate opened smoothly, the seedlings received water, and Luna discovered that steady grit works better than a stormy temper.",
        ending="fresh water shone in every garden row as the gate rested open",
        problem_answer="Rain-swollen wood made the garden gate stick, and force made its latch scrape worse.",
        choice_answer="Luna left her sulk, asked for supplies, and worked gently with Pip rather than shoving in anger.",
        result_answer="Careful teamwork opened the gate and saved the thirsty seedlings.",
    ),
    Arc(
        title="The Bell Beneath the Blanket",
        premise="Luna found a little silver bell that was meant to lead lost lambs home.",
        problem="The bell slipped beneath a heavy hay blanket, and Luna could hear it but could not reach it.",
        dialogue="\"I will never find it,\" Luna whispered. \"Then we will search by sound,\" said Pip. \"One small ring at a time.\"",
        choice="Luna started to sulk because the search was slow, but Pip invited her to ring a spoon whenever she felt ready to begin again.",
        action="They marked each quiet patch with twigs and lifted the blanket from opposite sides while Grandma Fern listened near the floor.",
        result="The bell appeared in a fold, and Luna learned that grit can be quiet, patient, and shared.",
        ending="the silver bell chimed from the lamb's neck as it followed Luna home",
        problem_answer="A silver bell became buried beneath a heavy hay blanket.",
        choice_answer="Luna replaced her sulk with a patient search and used Pip's small spoon signal to begin again.",
        result_answer="By searching slowly from both sides, the friends found the bell and returned it to the lamb.",
    ),
    Arc(
        title="The Soup That Needed Waiting",
        premise="Luna was cooking a welcome soup for neighbors arriving after a long walk.",
        problem="She tasted the pot too soon, frowned at its plain flavor, and sulked when the vegetables did not change at once.",
        dialogue="\"It is a failure,\" Luna said. \"It is still cooking,\" Pip answered. \"What if we give it time and one kind idea?\"",
        choice="Instead of throwing the soup away, Luna asked Grandma Fern which herb might make the broth warm and bright.",
        action="They added beans, thyme, and a little water, then stirred while the pot simmered slowly.",
        result="The soup became delicious, and Luna learned that grit sometimes means waiting long enough for good work to become itself.",
        ending="neighbors warmed their hands around full bowls while Luna smiled at the patient pot",
        problem_answer="Luna judged the soup too early and became upset when its flavor needed more time.",
        choice_answer="She stopped sulking, asked for advice, and improved the soup instead of discarding it.",
        result_answer="Waiting and adding thoughtful ingredients turned the plain broth into a welcome meal.",
    ),
    Arc(
        title="The Bridge of Three Boards",
        premise="Luna and Pip needed to carry a basket of apples across a narrow stream.",
        problem="One board cracked under the basket, and Luna sat down in a sulk while apples rolled toward the water.",
        dialogue="\"The bridge is broken,\" Luna sighed. \"Only one board is broken,\" said Pip. \"That leaves three clues about how to mend it.\"",
        choice="Luna wiped her eyes, asked what was safe to carry, and chose to solve the problem before chasing every apple.",
        action="They moved the apples to a dry stone, tested the remaining boards, and tied a spare plank in place with harbor rope.",
        result="The basket crossed safely, and Luna learned that grit begins when a person turns a setback into the next small step.",
        ending="apple slices were shared on the far bank beside the sturdy little bridge",
        problem_answer="A board cracked while the friends carried apples, sending some apples toward the stream.",
        choice_answer="Luna stopped sulking, secured the apples, and helped make a safe plan instead of rushing after everything.",
        result_answer="The friends tested the bridge and repaired it with a spare plank and rope.",
    ),
    Arc(
        title="The Window for the Small Bird",
        premise="A tiny bird flew into the bakery and could not find the open window.",
        problem="Luna tried to guide it with a towel, but the frightened bird fluttered higher and Luna began to sulk.",
        dialogue="\"I made it worse,\" Luna said. \"You noticed the bird needs calm,\" Pip replied. \"That is useful knowledge.\"",
        choice="Luna lowered the towel, asked everyone to whisper, and listened for the bird's soft wingbeats.",
        action="Together they darkened the other windows, opened the widest one, and placed crumbs along a gentle path.",
        result="The bird followed the light outside, and Luna learned that grit can mean changing a plan when the first plan fails.",
        ending="the bird perched on the bakery sign while warm bread scented the quiet street",
        problem_answer="A frightened bird was trapped inside the bakery and flew higher when Luna used a towel.",
        choice_answer="Luna stopped sulking, made the room calm, and changed her plan to guide the bird toward the open window.",
        result_answer="The quiet bakery and crumb path helped the bird find the open window.",
    ),
    Arc(
        title="The Lantern with No Spark",
        premise="Luna wanted to light the first lantern for the evening walk.",
        problem="The lantern wick would not catch, and each hurried strike made the flint colder.",
        dialogue="\"The spark hates me,\" Luna muttered. \"Maybe it needs a calmer hand,\" Pip said. \"Let us ask Grandma Fern.\"",
        choice="Luna nearly hid the lantern in a box, but she told the truth about her frustration and listened to the repair lesson.",
        action="Grandma Fern trimmed the wick, Luna dried the flint, and Pip shielded the tiny flame from the breeze.",
        result="The lantern glowed at last, and Luna learned that honest words can make room for useful help.",
        ending="one small lantern led the whole evening path through the warm meadow",
        problem_answer="The lantern would not light because its wick and flint needed care.",
        choice_answer="Luna admitted her frustration instead of hiding the lantern and accepted a repair lesson.",
        result_answer="A trimmed wick, dry flint, and sheltered flame made the lantern glow.",
    ),
    Arc(
        title="The Lost Button Promise",
        premise="Luna had sewn a blue button onto Pip's festival coat.",
        problem="The button popped off before the parade, and Luna sulked because she feared Pip would be disappointed.",
        dialogue="\"I am sorry,\" Luna said. \"I am disappointed about the button, not about you,\" Pip answered.",
        choice="Luna stopped hiding behind the curtain and asked whether Pip wanted a quick repair or a new design.",
        action="They found a wooden button, stitched it with thick thread, and added a tiny blue loop beside it.",
        result="The coat looked even brighter, and Luna learned that a mistake becomes lighter when it is named and repaired together.",
        ending="Pip marched proudly while the blue button bobbed beneath the parade flags",
        problem_answer="The blue button fell off Pip's festival coat before the parade.",
        choice_answer="Luna apologized honestly and offered to repair or redesign the coat instead of hiding in a sulk.",
        result_answer="A sturdy wooden button and blue loop repaired the coat and made it brighter.",
    ),
]


OPENINGS = [
    "{hero} lived in {setting}, where small jobs often grew into big lessons.",
    "In {setting}, {hero} was known for a bright smile and a stubborn little sulk.",
    "Every morning in {setting}, {hero} practiced one useful thing and one brave thing.",
    "The people of {setting} loved {hero}, even on days when grit felt far away.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.setting, params.hero, params.friend, params.helper))
    return sum((index + 1) * ord(char) for index, char in enumerate(text))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _facts(world: World) -> dict[str, object]:
    return world.facts


def _story_lines(world: World) -> list[str]:
    facts = _facts(world)
    arc: Arc = facts["arc"]
    opening = _fill(OPENINGS[facts["opening_variant"]], facts)
    premise = _fill(arc.premise, facts)
    problem = _fill(arc.problem, facts)
    dialogue = _fill(arc.dialogue, facts)
    choice = _fill(arc.choice, facts)
    action = _fill(arc.action, facts)
    result = _fill(arc.result, facts)
    ending = _fill(arc.ending, facts)

    structures = [
        [
            f"{opening} This is the cautionary tale of \"{arc.title}.\"",
            f"{premise} {problem}",
            dialogue,
            choice,
            action,
            f"{result} At sunset, {ending}.",
        ],
        [
            opening,
            f"\"What should I do?\" {facts['hero']} asked. {premise}",
            _cap(problem),
            dialogue,
            f"{choice} Then {action[0].lower() + action[1:]}",
            f"{result} By evening, {ending}.",
        ],
        [
            f"People still tell \"{arc.title}\" whenever a child begins to sulk. {opening}",
            premise,
            f"The trouble began quietly: {problem[0].lower() + problem[1:]}",
            dialogue,
            f"{choice} With {facts['friend']} beside {facts['hero']}, {action[0].lower() + action[1:]}",
            f"{result} The proof was simple: {ending}.",
        ],
        [
            opening,
            f"At first, {facts['hero']} thought grit meant never stopping and never asking. {problem}",
            f"{facts['helper']} said, \"A brave heart may speak before it works.\" {dialogue}",
            choice,
            action,
            f"That day, {result} And so {ending}.",
        ],
        [
            f"The final picture of \"{arc.title}\" shows {ending}.",
            f"It began when {facts['hero']} and {facts['friend']} were together in {facts['setting']}. {premise}",
            f"Then {problem}",
            dialogue,
            choice,
            f"Careful work followed: {action} {result}",
        ],
    ]
    return structures[facts["structure_variant"]]


ASP_RULES = r"""
setting(little_hill_village).
setting(windy_harbor).
setting(lantern_meadow).
feature(cautionary).
virtue(grit).
feeling(sulk).

story_ready(S) :- setting(S), feature(cautionary), virtue(grit), feeling(sulk).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for setting in SETTING_REGISTRY:
        key = setting.replace("the ", "").replace(" ", "_")
        lines.append(asp.fact("setting", key))
    lines.extend(
        [
            asp.fact("feature", "cautionary"),
            asp.fact("virtue", "grit"),
            asp.fact("feeling", "sulk"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A cautionary, heartwarming story world about grit and sulking."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--helper")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice(FRIENDS)
    helper = args.helper or rng.choice(HELPERS)
    if hero == friend:
        raise StoryError("The hero and friend must be different characters.")
    if hero == helper or friend == helper:
        raise StoryError("The helper must be a different character from the children.")
    return StoryParams(setting=setting, hero=hero, friend=friend, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING_REGISTRY:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.hero == params.friend:
        raise StoryError("The hero and friend must be different characters.")
    if params.hero == params.helper or params.friend == params.helper:
        raise StoryError("The helper must be separate from the children.")

    seed = _stable_seed(params)
    arc = ARCS[seed % len(ARCS)]
    world = World(setting=params.setting)

    hero = world.add(
        Entity(
            name=params.hero,
            kind="child",
            meters={"energy": 0.8, "task_progress": 0.15},
            memes={"grit": 0.7, "sulk": 0.35, "trust": 0.75},
        )
    )
    friend = world.add(
        Entity(
            name=params.friend,
            kind="friend",
            meters={"energy": 0.85},
            memes={"patience": 0.9, "kindness": 0.9},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="helper",
            meters={"tools": 1.0},
            memes={"wisdom": 1.0, "warmth": 1.0},
        )
    )
    world.add(
        Entity(
            name="the unfinished task",
            kind="challenge",
            meters={"difficulty": 0.7, "progress": 0.15},
            memes={"lesson": 1.0},
        )
    )
    world.add(
        Entity(
            name="the shared courage",
            kind="feeling",
            meters={"strength": 0.25},
            memes={"hope": 0.8, "connection": 0.9},
        )
    )

    hero.memes["sulk"] = 0.05
    hero.memes["grit"] = 1.0
    hero.meters["task_progress"] = 1.0
    world.entities["the unfinished task"].meters["progress"] = 1.0
    world.entities["the shared courage"].meters["strength"] = 1.0

    world.facts.update(
        hero=params.hero,
        friend=params.friend,
        helper=params.helper,
        setting=params.setting,
        arc=arc,
        opening_variant=(seed // len(ARCS)) % len(OPENINGS),
        structure_variant=(seed // (len(ARCS) * len(OPENINGS))) % 5,
        theme="grit, honest asking, and kindness",
        problem=_fill(arc.problem, vars(params)),
        choice=_fill(arc.choice, vars(params)),
        resolution=_fill(arc.result, vars(params)),
        ending_image=_fill(arc.ending, vars(params)),
    )

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a cautionary but heartwarming story about {params.hero} learning grit in {params.setting}.",
        f"Tell a child-facing story in which {params.hero} stops a sulk and accepts help from {params.friend}.",
        "Write a gentle story showing that asking for help can be part of being brave.",
    ]
    story_qa = [
        QAItem(
            question=f"What problem did {params.hero} face in \"{arc.title}\"?",
            answer=arc.problem_answer,
        ),
        QAItem(
            question=f"How did {params.hero} move beyond the sulk?",
            answer=arc.choice_answer,
        ),
        QAItem(
            question=f"What did grit and teamwork change for {params.hero}?",
            answer=arc.result_answer,
        ),
        QAItem(
            question=f"What final image closes \"{arc.title}\"?",
            answer=f"The story closes with {world.facts['ending_image']}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is grit?",
            answer="Grit is the courage to keep working through difficulty while learning and adjusting.",
        ),
        QAItem(
            question="What is a sulk?",
            answer="A sulk is a quiet, unhappy mood in which someone withdraws instead of explaining what is wrong.",
        ),
        QAItem(
            question="Why can asking for help be brave?",
            answer="Asking for help can be brave because it admits a problem and invites people to solve it safely together.",
        ),
        QAItem(
            question="What makes a cautionary story useful?",
            answer="A cautionary story shows a mistake or risky choice and helps readers notice a kinder, wiser path.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def _python_valid() -> set[tuple[str]]:
    return {
        (setting.replace("the ", "").replace(" ", "_"),)
        for setting in SETTING_REGISTRY
    }


def _asp_valid() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program("#show story_ready/1."))
    return set(asp.atoms(model, "story_ready"))


def asp_verify() -> int:
    python_answers = _python_valid()
    asp_answers = _asp_valid()
    if python_answers == asp_answers:
        print(f"OK: clingo gate matches python ({len(python_answers)} settings).")
        for index, setting in enumerate(SETTING_REGISTRY):
            params = StoryParams(
                setting=setting,
                hero="Luna",
                friend="Pip",
                helper="Grandma Fern",
                seed=index,
            )
            sample = generate(params)
            if not sample.story.strip() or "{" in sample.story or "}" in sample.story:
                print("Generated story validation failed.")
                return 1
        print("OK: generated stories are populated and resolved.")
        return 0
    print("MISMATCH between clingo and python:")
    print("python only:", sorted(python_answers - asp_answers))
    print("clingo only:", sorted(asp_answers - python_answers))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ready/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in sorted(_asp_valid()):
            print(item[0])
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, setting in enumerate(SETTING_REGISTRY):
            params = StoryParams(
                setting=setting,
                hero="Luna",
                friend="Pip",
                helper="Grandma Fern",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
