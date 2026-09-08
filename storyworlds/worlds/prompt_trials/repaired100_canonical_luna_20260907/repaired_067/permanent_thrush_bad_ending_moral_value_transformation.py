#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a permanent mark, a thrush, and a
transformation from a bad ending into a wiser one.

The seed asks for a permanent thrush, a Bad Ending, Moral Value, and
Transformation.  The world treats these as concrete story state: a thrush
makes a lasting mark, a careless choice points toward a bad ending, and a
truthful repair transforms the mark into a promise.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
permanent_mark(M) :- thrush(T), marks(T,M), lasting(M).
bad_ending_risk(T) :- thrush(T), sees_shortcut(T), ignores_warning(T).
moral_value(T) :- thrush(T), tells_truth(T), repairs(T), shares(T).
transformation(T) :- thrush(T), permanent_mark(M), moral_value(T), changes_meaning(M).
good_ending(T) :- transformation(T), not bad_ending(T).
"""


THRUSH_NAMES = ["Luna", "Pip", "Merry", "Dawn", "Bramble", "Tilly"]
HELPERS = ["the hedgehog", "the mouse", "the robin", "the old oak"]
PLACES = ["the garden gate", "the berry lane", "the moonlit hill", "the village green"]
MARKS = ["a blue berry stain", "a silver ink star", "a golden paint feather", "a green leaf print"]
OBJECTS = ["a rhyme book", "a red ribbon", "a basket of cherries", "a little bell"]


@dataclass(frozen=True)
class Trial:
    title: str
    object_name: str
    danger: str
    shortcut: str
    warning: str
    bad_ending: str
    truth: str
    repair: str
    sharing: str
    transformed: str
    moral: str
    ending: str
    joke: str


TRIALS = [
    Trial(
        title="the berry-red rhyme book",
        object_name="a rhyme book",
        danger="the open book lay beside a puddle where one careless step could soak every page",
        shortcut="hop over the puddle while carrying the book with one wing",
        warning="a thin ripple reached the book's lower corner",
        bad_ending="the pages would have blurred into a sad, unreadable mush",
        truth="I nearly ruined the book because I hurried",
        repair="lifted the book onto a dry stone, pressed the damp corner flat, and asked the gardener for a cloth",
        sharing="read the saved rhyme aloud so every small listener could hear it",
        transformed="the permanent berry stain became a bright reminder to slow down near water",
        moral="telling the truth and repairing harm are kinder than hiding a mistake",
        ending="The marked page dried beneath a daisy, and the thrush sang the rhyme without a single soggy word",
        joke="That puddle wanted to be an author, but it only knew one wet sentence",
    ),
    Trial(
        title="the ribbon on the windy hill",
        object_name="a red ribbon",
        danger="the ribbon was tied to a loose twig above a nest",
        shortcut="snatch the ribbon quickly before the wind carried it away",
        warning="the twig bent toward three tiny eggs",
        bad_ending="the nest would have tumbled and the eggs would have cracked",
        truth="I pulled too close to the nest",
        repair="stepped back, called the robin, and used a long fallen reed to loosen the knot",
        sharing="wove the ribbon into a soft flag for the whole meadow",
        transformed="the permanent red mark on the thrush's feather became a sign to protect nests",
        moral="a lovely prize is never worth hurting a smaller neighbor",
        ending="The nest stayed snug while the red flag fluttered safely beyond the eggs",
        joke="The wind had tied a knot, but it had forgotten to learn how to untie one",
    ),
    Trial(
        title="the cherries by the gate",
        object_name="a basket of cherries",
        danger="the heavy basket rested on a gate that was beginning to swing",
        shortcut="grab the sweetest cherries and fly away first",
        warning="the gate hinge squeaked under the basket's weight",
        bad_ending="the basket would have fallen and scattered fruit into the mud",
        truth="I wanted the best cherries before anyone else",
        repair="moved the basket to the ground, steadied the gate, and counted the fruit with the hedgehog",
        sharing="gave one cherry to each neighbor and saved seeds for planting",
        transformed="the permanent purple spot on Luna's beak became a sign of fair sharing",
        moral="wanting first is less important than making sure everyone receives a fair part",
        ending="Purple cherry seeds lined the path, and no one went home with an empty paw",
        joke="Luna's beak wore jam so proudly that the cherries asked for autographs",
    ),
    Trial(
        title="the bell beneath the moon",
        object_name="a little bell",
        danger="the bell's cord crossed a dark path where a fox might trip",
        shortcut="ring it loudly and tug it free in one dash",
        warning="the cord shone across the fox's narrow trail",
        bad_ending="the frightened fox would have fallen into the bramble patch",
        truth="I saw the cord but thought the noise mattered more",
        repair="quietly moved the bell to a low branch and looped the cord away from the path",
        sharing="rang it gently to call every creature home for supper",
        transformed="the permanent silver mark on the bell became a reminder that sound needs care",
        moral="being useful means noticing who might be harmed by our actions",
        ending="The bell chimed softly above the safe path, and the fox trotted home unharmed",
        joke="The bell wanted a grand entrance, but the fox preferred a quiet encore",
    ),
]


OPENINGS = [
    "Sing a small song of {title}, where {hero} the thrush found a choice.",
    "Peep, peep, went {hero} at {place}, beside {title}.",
    "One bright morning, {hero} carried {object_name} through {place}.",
    "By moon and feather, {hero} reached {title} before breakfast.",
    "A little wing, a little song, and {title} began at once.",
]


@dataclass
class Character:
    id: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    name: str
    helper: str
    place: str
    mark: str
    object_name: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Character
    helper: Character
    mark: str
    object_name: str
    trial: Trial
    route: int
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme thrush tale with a permanent mark and moral transformation.")
    ap.add_argument("--name", choices=THRUSH_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
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


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("thrush", "luna"),
        asp.fact("marks", "luna", "permanent_mark"),
        asp.fact("lasting", "permanent_mark"),
        asp.fact("sees_shortcut", "luna"),
        asp.fact("ignores_warning", "luna"),
        asp.fact("tells_truth", "luna"),
        asp.fact("repairs", "luna"),
        asp.fact("shares", "luna"),
        asp.fact("changes_meaning", "permanent_mark"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show permanent_mark/1.\n#show moral_value/1.\n#show transformation/1.\n#show good_ending/1."))
    found = {
        "permanent_mark": set(asp.atoms(model, "permanent_mark")),
        "moral_value": set(asp.atoms(model, "moral_value")),
        "transformation": set(asp.atoms(model, "transformation")),
        "good_ending": set(asp.atoms(model, "good_ending")),
    }
    expected = {
        "permanent_mark": {("permanent_mark",)},
        "moral_value": {("luna",)},
        "transformation": {("luna",)},
        "good_ending": {("luna",)},
    }
    if found != expected:
        print("MISMATCH:", found, expected)
        return 1
    sample = generate(StoryParams("Luna", "the mouse", "the village green", "a blue berry stain", "a rhyme book"))
    if not sample.story or "permanent" not in sample.story.lower():
        print("MISMATCH: generated story did not exercise permanent transformation")
        return 1
    print("OK: ASP parity and generated story verified.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(THRUSH_NAMES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        mark=args.mark or rng.choice(MARKS),
        object_name=args.object_name or rng.choice(OBJECTS),
    )


def make_world(params: StoryParams) -> World:
    if not params.name or not params.helper or not params.place:
        raise StoryError("A thrush, helper, and place are required.")
    key = params.seed if params.seed is not None else sum(ord(c) for c in "|".join(vars(params).values() if False else [
        params.name, params.helper, params.place, params.mark, params.object_name
    ]))
    hero = Character(
        id=params.name,
        role="thrush",
        meters={"care": 0.4, "truth": 0.2, "sharing": 0.1},
        memes={"hope": 0.5, "worry": 0.3},
    )
    helper = Character(
        id=params.helper,
        role="helper",
        meters={"patience": 0.9, "kindness": 0.9},
        memes={"trust": 0.8},
    )
    return World(
        setting=Setting(params.place),
        hero=hero,
        helper=helper,
        mark=params.mark,
        object_name=params.object_name,
        trial=TRIALS[key % len(TRIALS)],
        route=(key // len(TRIALS)) % len(OPENINGS),
    )


def tell(world: World) -> None:
    h, helper, trial = world.hero, world.helper, world.trial
    opening = OPENINGS[world.route].format(
        title=trial.title,
        hero=h.id,
        place=world.setting.place,
        object_name=world.object_name,
    )
    world.say(f"{opening} {trial.danger.capitalize()}.")
    world.say(
        f"A permanent {world.mark} already colored one feather, so {h.id} knew that some marks stay. "
        f"Still, the little thrush noticed {trial.warning}."
    )
    world.para()
    world.say(
        f"{h.id} chirped, \"I could {trial.shortcut}.\" "
        f"{helper.id.capitalize()} answered, \"Listen first; a quick wing can make a long regret.\""
    )
    world.say(
        f"For a moment, the bad ending waited nearby: {trial.bad_ending.capitalize()}. "
        f"{h.id} took one breath, then said, \"{trial.truth.capitalize()}.\""
    )
    world.para()
    world.say(
        f"That brave truth changed the plan. Together, {h.id} and {helper.id} {trial.repair}. "
        f"Then they {trial.sharing}."
    )
    world.say(
        f"The permanent {world.mark} did not vanish. Instead, {trial.transformed.capitalize()}. "
        f"The mark became a transformation, changing a mistake into a promise."
    )
    world.para()
    world.say(
        f"\"{trial.joke},\" chirped {h.id}. {helper.id.capitalize()} laughed, and then said, "
        f"\"Your moral value is plain: {trial.moral}.\""
    )
    world.say(
        f"So the bad ending slipped away, replaced by a kinder song. "
        f"{trial.ending}. That was the thrush's new tune: tell the truth, repair what you can, and share the good."
    )
    world.hero.meters.update(care=1.0, truth=1.0, sharing=1.0)
    world.hero.memes.update(hope=1.0, worry=0.0)
    world.facts.update(
        hero=h,
        helper=helper,
        setting=world.setting,
        trial=trial,
        mark=world.mark,
        bad_ending=trial.bad_ending,
        truth=trial.truth,
        repair=trial.repair,
        transformed=trial.transformed,
        moral=trial.moral,
        ending=trial.ending,
    )


def generation_prompts(world: World) -> list[str]:
    trial = world.trial
    return [
        f"Write a child-friendly nursery rhyme about {world.hero.id} the thrush and {trial.title}, with a permanent mark, a bad ending risk, and a moral transformation.",
        f"Tell how {world.hero.id} avoids this bad ending: {trial.bad_ending}, by telling the truth and repairing the harm.",
        f"End with a concrete image proving that {trial.transformed}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    t, h = world.trial, world.hero
    return [
        QAItem(
            question=f"What bad ending did {h.id} the thrush nearly cause?",
            answer=f"The bad ending was that {t.bad_ending}. The danger came from trying to use a shortcut instead of listening to the warning.",
        ),
        QAItem(
            question=f"What warning did {h.id} notice?",
            answer=f"{h.id} noticed that {t.warning}. That small clue changed the bird's plan.",
        ),
        QAItem(
            question=f"What did {h.id} do after telling the truth?",
            answer=f"{h.id} and {world.helper.id} {t.repair}. Their repair stopped the bad ending from happening.",
        ),
        QAItem(
            question="What was the moral value in the story?",
            answer=f"The moral value was that {t.moral}. The thrush showed it by speaking honestly, fixing the trouble, and sharing.",
        ),
        QAItem(
            question="How did the permanent mark become a transformation?",
            answer=f"The permanent {world.mark} stayed, but {t.transformed}. It changed from a sign of error into a reminder to choose carefully.",
        ),
        QAItem(
            question="What proved that the ending had changed?",
            answer=f"The ending changed because {t.ending}. That peaceful image shows that the bad ending was avoided.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does permanent mean?",
            answer="Permanent means lasting for a very long time or not easily removed. In this story, the mark remains, but its meaning can become wiser.",
        ),
        QAItem(
            question="What is a thrush?",
            answer="A thrush is a small songbird. In this world, the thrush learns through noticing danger, speaking honestly, and repairing a mistake.",
        ),
        QAItem(
            question="Can a mistake be transformed?",
            answer="A mistake cannot always be erased, but it can be transformed when someone tells the truth, repairs the harm, and uses the lesson to act more kindly.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"hero={world.hero.id} role={world.hero.role}",
            f"hero_meters={world.hero.meters}",
            f"hero_memes={world.hero.memes}",
            f"helper={world.helper.id} role={world.helper.role}",
            f"place={world.setting.place}",
            f"object={world.object_name}",
            f"permanent_mark={world.mark}",
            f"trial={world.trial.title}",
            f"bad_ending={world.trial.bad_ending}",
            f"repair={world.trial.repair}",
            f"transformation={world.trial.transformed}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "the mouse", "the village green", "a blue berry stain", "a rhyme book"),
        StoryParams("Pip", "the robin", "the moonlit hill", "a silver ink star", "a little bell"),
        StoryParams("Merry", "the hedgehog", "the garden gate", "a purple berry stain", "a basket of cherries"),
        StoryParams("Dawn", "the old oak", "the berry lane", "a golden paint feather", "a red ribbon"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show permanent_mark/1.\n#show moral_value/1.\n#show transformation/1.\n#show good_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program(
                "#show permanent_mark/1.\n"
                "#show bad_ending_risk/1.\n"
                "#show moral_value/1.\n"
                "#show transformation/1.\n"
                "#show good_ending/1."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in curated()]
    else:
        base = args.seed if args.seed is not None else random.randrange(2**31)
        for i in range(args.n):
            rng = random.Random(base + i)
            params = resolve_params(args, rng)
            params.seed = base + i if args.seed is not None else None
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
