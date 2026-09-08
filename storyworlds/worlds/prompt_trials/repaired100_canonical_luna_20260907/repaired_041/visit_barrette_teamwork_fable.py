#!/usr/bin/env python3
"""
A standalone Storyweavers world: a gentle fable about a visit, a lost barrette,
and the teamwork that helps a small woodland community prepare a welcome.
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


THEME = "a woodland visit"
SEED_WORDS = {"visit", "barrette"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("distance", "looseness", "shine", "mud", "warmth"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "joy", "curiosity", "kindness", "teamwork", "pride"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    visitor: str = "Mara"
    helper: str = "Pip"
    trial: int = 0
    telling: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    guest: str
    welcome_task: str
    trouble: str
    clue: str
    false_lead: str
    question: str
    search: str
    discovery: str
    cause: str
    repair: str
    proof: str
    moral: str
    ending: str


TRIALS = [
    Trial(
        guest="a robin who had flown from the far hill",
        welcome_task="a leaf-table supper beneath the elder tree",
        trouble="the visitor's bright barrette slipped away while a gust scattered the welcome ribbons",
        clue="a blue thread caught on a thorn beside the path",
        false_lead="a magpie's shiny nest seemed the obvious place for anything bright",
        question="The nest is tempting, but what object touched the barrette before it vanished?",
        search="follow the blue thread while Pip checked the ribbon basket",
        discovery="found the barrette tucked under a curled fern beside the path",
        cause="had caught the barrette on the thorn while carrying ribbons and hurried on without noticing",
        repair="freed the thread, smoothed the ribbons, and placed a little basket beside the path for loose things",
        proof="the ribbons stayed tied and the basket held the barrette safely",
        moral="A shiny guess may sparkle, but careful teamwork follows the clue that explains the whole story.",
        ending="When the robin arrived, the blue barrette shone in Luna's hair beside the welcoming ribbons.",
    ),
    Trial(
        guest="a young fox from the berry meadow",
        welcome_task="a wreath of clover and golden grass",
        trouble="the visitor's red barrette disappeared when the wreath rolled down a small slope",
        clue="three red hairs were caught in the wreath's grass braid",
        false_lead="a red berry stain on a stone made the streambank look suspicious",
        question="The stain tells where a berry fell, but what touched the barrette?",
        search="steady the wreath while Mara inspected the grass braid",
        discovery="pulled the barrette gently from the center of the rolled wreath",
        cause="had set the barrette on the wreath while tying a knot, then lifted the wreath too quickly",
        repair="rebuilt the wreath around a firm twig and made a marked resting place for hair things",
        proof="the wreath stayed round when lifted and the barrette rested in its marked place",
        moral="When every helper shares what they noticed, an accident becomes easier to mend.",
        ending="The fox wore the red barrette under the clover wreath, and the meadow seemed to smile.",
    ),
    Trial(
        guest="a turtle who had walked all morning",
        welcome_task="a shady reading nook by the pond",
        trouble="the visitor's silver barrette went missing when a stack of story leaves toppled",
        clue="a silver glint showed between the largest leaves",
        false_lead="a fish's flashing scales distracted everyone near the water",
        question="The fish is bright, but where did the barrette's own glint appear?",
        search="hold the pond reeds aside while Pip lifted the leaves one at a time",
        discovery="found the barrette beneath the bottom story leaf",
        cause="had placed it on the leaf stack before bending to greet the turtle",
        repair="re-stacked the leaves with a flat stone nearby and set up a small bowl for personal things",
        proof="the reading leaves stood firmly and nothing slid into the pond",
        moral="A calm search can notice the small truth that a noisy distraction hides.",
        ending="The turtle opened the first story while the silver barrette gleamed beside the pond.",
    ),
    Trial(
        guest="a mouse carrying a tiny suitcase",
        welcome_task="a warm doorway welcome with cinnamon seeds",
        trouble="the visitor's yellow barrette vanished when the suitcase tipped against the welcome mat",
        clue="a yellow tooth of the barrette showed beneath one folded corner of the mat",
        false_lead="crumbs led toward the pantry and made the hungry badger look guilty",
        question="The crumbs explain a hungry path, but what does the yellow edge explain?",
        search="sweep the crumbs into a bowl while Luna lifted the mat carefully",
        discovery="slid the barrette from beneath the welcome mat",
        cause="had set it beside the suitcase, then nudged it under the mat while making room at the doorway",
        repair="moved the suitcase to a shelf, washed the mat, and hung a bright hook for visiting guests",
        proof="the doorway stayed clear and the hook held the barrette without a wobble",
        moral="It is kinder to describe what happened than to blame the nearest hungry creature.",
        ending="The mouse stepped through the clean doorway, its yellow barrette bright as a little sun.",
    ),
    Trial(
        guest="a deer from the quiet north grove",
        welcome_task="a garland of soft moss flowers",
        trouble="the visitor's green barrette slipped away while the garland was carried through tall grass",
        clue="a green clasp clicked against a hollow acorn near the trail",
        false_lead="hoofprints pointed toward the river, far from the welcome clearing",
        question="The hoofprints show who passed by, but what sound points to the missing barrette?",
        search="mark the hoofprints while Mara listened beside the hollow acorn",
        discovery="lifted the barrette from inside the acorn",
        cause="had used the acorn as a temporary pocket while tying the garland and forgotten it there",
        repair="returned the acorn to the trail and tied a small pouch to the garland basket",
        proof="the pouch stayed attached as the garland traveled from the grass to the clearing",
        moral="Good teamwork separates clues about movement from clues about hiding places.",
        ending="The deer wore the green barrette as moss flowers swayed gently around the welcome path.",
    ),
]


@dataclass
class World:
    hero: Entity
    visitor: Entity
    helper: Entity
    barrette: Entity
    path: Entity
    basket: Entity
    tree: Entity
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


def new_entity(
    eid: str,
    kind: str,
    type_: str,
    label: str,
    *,
    owner: Optional[str] = None,
    location: Optional[str] = None,
) -> Entity:
    return Entity(
        id=eid,
        kind=kind,
        type=type_,
        label=label,
        owner=owner,
        location=location,
    )


def build_world(params: StoryParams) -> World:
    hero = new_entity(params.hero, "character", "child", "the host")
    visitor = new_entity(params.visitor, "character", "visitor", "the visitor")
    helper = new_entity(params.helper, "character", "helper", "the helper")
    barrette = new_entity(
        "barrette",
        "thing",
        "hair_clasp",
        "the barrette",
        owner=visitor.id,
        location="visitor_hair",
    )
    path = new_entity("path", "place", "trail", "the woodland path")
    basket = new_entity("basket", "thing", "basket", "the welcome basket")
    tree = new_entity("tree", "place", "tree", "the elder tree")
    return World(
        hero=hero,
        visitor=visitor,
        helper=helper,
        barrette=barrette,
        path=path,
        basket=basket,
        tree=tree,
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero, visitor, helper = world.hero, world.visitor, world.helper
    barrette = world.barrette
    trial = TRIALS[params.trial % len(TRIALS)]

    hero.memes["worry"] = 1
    hero.memes["curiosity"] = 1
    visitor.memes["joy"] = 1
    helper.memes["pride"] = 1
    barrette.meters["shine"] = 2
    barrette.meters["looseness"] = 1
    barrette.location = "lost"
    world.facts["resolved"] = False

    openings = [
        f"In the woodland, {hero.id} prepared {trial.welcome_task} because {trial.guest} was coming for a visit.",
        f"Morning dew shone on the leaves as {hero.id}, {helper.id}, and {trial.guest} planned {trial.welcome_task}.",
        f"The animals of the grove were busy with one kind task: {hero.id} would welcome {trial.guest} with {trial.welcome_task}.",
        f"Before the visit began, {hero.id} checked every ribbon, leaf, and basket for {trial.welcome_task}.",
    ]
    world.say(openings[params.telling % len(openings)])
    world.say(
        f"{helper.id} carried the basket, while {hero.id} watched the path where the visitor would arrive."
    )
    world.say(f"Then {trial.trouble}.")
    world.say(
        f"The empty place beside {visitor.id}'s hair made the welcome feel unfinished."
    )

    world.para()
    world.say(f"Near the trail, {trial.clue}.")
    world.say(f"At the same time, {trial.false_lead}.")
    world.say(
        f"{hero.id} took a slow breath and asked, \"{trial.question}\""
    )
    dialogue = [
        f"{helper.id} said, \"I will check the basket, and you can follow the thread.\"",
        f"\"We should not blame anyone yet,\" said {hero.id}. \"Let's let the objects tell us what happened.\"",
        f"{visitor.id} said, \"I remember touching the ribbons. Perhaps that is where we should begin.\"",
        f"\"Two pairs of eyes are better than one,\" said {helper.id}. \"We can search different places and share what we learn.\"",
    ]
    world.say(dialogue[(params.telling + params.ending) % len(dialogue)])
    world.say(f"Together, they decided to {trial.search}.")

    world.para()
    search_turns = [
        "The first glance found nothing. The team changed places instead of giving up.",
        "One clue led nowhere, but the helpers compared it with the stronger clue and tried again.",
        "They moved slowly, naming each discovery so no useful detail was lost.",
        "The search became clearer when each helper watched a different part of the path.",
    ]
    world.say(search_turns[params.telling % len(search_turns)])
    world.say(f"At last, {hero.id} and {helper.id} {trial.discovery}.")
    barrette.location = "found"
    barrette.meters["looseness"] = 0
    hero.memes["joy"] += 1
    helper.memes["curiosity"] += 1

    world.say(
        f"{visitor.id} touched the barrette and said, \"Now I remember. I {trial.cause}.\""
    )
    world.say(
        f"{hero.id} answered, \"Thank you for telling us. An accident is easier to fix when everyone knows the truth.\""
    )

    world.para()
    hero.memes["teamwork"] += 2
    helper.memes["teamwork"] += 2
    visitor.memes["teamwork"] += 1
    world.say(f"The three friends {trial.repair}.")
    world.say(f"They tested their plan: {trial.proof}.")
    world.say(
        f"{helper.id} smiled. \"The visit can be joyful now, because we solved the problem together.\""
    )
    world.say(f"{hero.id} replied, \"That is the strength of teamwork.\"")
    world.say(f"The woodland animals remembered this rule: {trial.moral}")

    world.para()
    world.say(trial.ending)
    world.facts.update(
        trial=trial,
        project=trial.welcome_task,
        trouble=trial.trouble,
        clue=trial.clue,
        false_lead=trial.false_lead,
        question=trial.question,
        search=trial.search,
        discovery=trial.discovery,
        cause=trial.cause,
        repair=trial.repair,
        proof=trial.proof,
        moral=trial.moral,
        ending=trial.ending,
        visitor=visitor,
        hero=hero,
        helper=helper,
        barrette=barrette,
        resolved=True,
    )
    world.facts["resolved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].id
    visitor = f["visitor"].id
    helper = f["helper"].id
    styles = [
        (
            f"What happened during {visitor}'s visit?",
            f"{f['trouble'].capitalize()}. The missing barrette interrupted the welcome.",
        ),
        (
            "Why did the welcome pause?",
            f"The barrette went missing when {f['trouble'].split('when ', 1)[-1]}.",
        ),
        (
            f"What problem did {hero} notice?",
            f"{hero} noticed that {visitor}'s barrette was missing while the woodland friends prepared the visit.",
        ),
    ]
    clue_questions = [
        (
            "Which clue helped the friends find the barrette?",
            f"They followed {f['clue']}, because it showed where the barrette had touched something.",
        ),
        (
            f"How did {hero} and {helper} solve the search?",
            f"They worked together to {f['search']}; then they {f['discovery']}.",
        ),
        (
            "Why was the false lead not enough?",
            f"The false lead did not explain the barrette's path. The stronger clue was {f['clue']}.",
        ),
    ]
    cause_questions = [
        (
            f"What did {visitor} explain about the missing barrette?",
            f"{visitor} explained that they {f['cause']}.",
        ),
        (
            "Was the barrette hidden on purpose?",
            f"No. It was an accident: the visitor explained that they {f['cause']}.",
        ),
        (
            "How did the friends learn what happened?",
            f"They asked careful questions and connected the physical clue with the visitor's memory.",
        ),
    ]
    repair_questions = [
        (
            "How did teamwork help?",
            f"The friends {f['repair']}. They checked the result by seeing that {f['proof']}.",
        ),
        (
            f"What did {hero}, {helper}, and {visitor} do after finding the barrette?",
            f"They {f['repair']}.",
        ),
        (
            "What proved that their repair worked?",
            f"They saw that {f['proof']}.",
        ),
    ]
    selected = params_style = world.facts["trial"]
    index = TRIALS.index(selected) % 3
    return [
        QAItem(*styles[index]),
        QAItem(*clue_questions[index]),
        QAItem(*cause_questions[index]),
        QAItem(*repair_questions[index]),
        QAItem(
            "What lesson did the woodland friends learn?",
            f"They learned that {f['moral']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a visit?",
            "A visit is time spent going to see someone or welcoming someone who comes to see you.",
        ),
        QAItem(
            "What is a barrette?",
            "A barrette is a small clasp or clip used to hold hair in place.",
        ),
        QAItem(
            "What is teamwork?",
            "Teamwork means people share jobs, listen to one another, and combine their efforts to solve a problem.",
        ),
        QAItem(
            "Why should people check clues before blaming someone?",
            "Checking clues helps people understand what happened fairly instead of making a guess that may hurt someone.",
        ),
        QAItem(
            "What is a fable?",
            "A fable is a short story that often uses animals or nature to teach a clear lesson.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly fable about a visit where {world.facts['barrette'].label} goes missing.",
        f"Tell a woodland story in which teamwork follows this clue: {world.facts['clue']}.",
        "Create a gentle fable using the words visit and barrette, with dialogue and a concrete ending image.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for number, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{number}. {prompt}")
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
    entities = [
        world.hero,
        world.visitor,
        world.helper,
        world.barrette,
        world.path,
        world.basket,
        world.tree,
    ]
    for entity in entities:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.owner:
            bits.append(f"owner={entity.owner}")
        if entity.location:
            bits.append(f"location={entity.location}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) {' '.join(bits)}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
setting(woodland_visit).
requires(woodland_visit, visit).
requires(woodland_visit, barrette).
feature(woodland_visit, teamwork).
style(woodland_visit, fable).

valid_story(S) :-
    setting(S),
    requires(S, visit),
    requires(S, barrette),
    feature(S, teamwork),
    style(S, fable).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("setting", "woodland_visit"),
            asp.fact("requires", "woodland_visit", "visit"),
            asp.fact("requires", "woodland_visit", "barrette"),
            asp.fact("feature", "woodland_visit", "teamwork"),
            asp.fact("style", "woodland_visit", "fable"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = any(atom.name == "valid_story" for atom in model)
    if not asp_ok:
        print("MISMATCH: ASP rules rejected the required story domain.")
        return 1

    for index, params in enumerate(
        [
            StoryParams(hero="Luna", visitor="Mara", helper="Pip", trial=index)
            for index in range(len(TRIALS))
        ]
    ):
        sample = generate(params)
        if not sample.story or "visit" not in sample.story.lower():
            print(f"MISMATCH: generated sample {index + 1} lacks the visit premise.")
            return 1
        if "barrette" not in sample.story.lower():
            print(f"MISMATCH: generated sample {index + 1} lacks the barrette.")
            return 1
        if "teamwork" not in sample.story.lower():
            print(f"MISMATCH: generated sample {index + 1} lacks teamwork.")
            return 1
        if len(sample.story_qa) < 4:
            print(f"MISMATCH: generated sample {index + 1} lacks story QA.")
            return 1

    print("OK: ASP and Python recognize the woodland visit, barrette, teamwork, and fable domain.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a fable about a woodland visit and a missing barrette."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--visitor", default=None)
    parser.add_argument("--helper", default=None)
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
    hero = args.hero or rng.choice(["Luna", "Nia", "Tala", "Mira", "Suri"])
    visitor = args.visitor or rng.choice(["Mara", "Robin", "Fenn", "Clover", "Pico"])
    helper = args.helper or rng.choice(["Pip", "Bram", "Tavi", "Ollie", "Wren"])

    if len({hero, visitor, helper}) != 3:
        raise StoryError("The hero, visitor, and helper must have different names.")

    offset = sample_seed - base_seed
    trial = offset % len(TRIALS)
    telling = (offset // len(TRIALS)) % 4
    ending = (offset // (len(TRIALS) * 4)) % 4
    return StoryParams(
        hero=hero,
        visitor=visitor,
        helper=helper,
        trial=trial,
        telling=telling,
        ending=ending,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    if not params.hero or not params.visitor or not params.helper:
        raise StoryError("Every story needs a hero, a visitor, and a helper.")
    if len({params.hero, params.visitor, params.helper}) != 3:
        raise StoryError("The hero, visitor, and helper must have different names.")
    if not 0 <= params.trial < len(TRIALS):
        raise StoryError("The selected woodland trial is out of range.")

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
    StoryParams(hero="Luna", visitor="Mara", helper="Pip", trial=0),
    StoryParams(hero="Nia", visitor="Clover", helper="Bram", trial=1),
    StoryParams(hero="Tala", visitor="Fenn", helper="Wren", trial=2),
    StoryParams(hero="Mira", visitor="Pico", helper="Tavi", trial=3),
    StoryParams(hero="Suri", visitor="Robin", helper="Ollie", trial=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
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

    if not samples:
        raise StoryError("No story samples could be generated.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(
                json.dumps(
                    [sample.to_dict() for sample in samples],
                    indent=2,
                    ensure_ascii=False,
                )
            )
        return

    for index, sample in enumerate(samples):
        header = (
            f"### variant {index + 1}"
            if len(samples) > 1 and not args.all
            else ""
        )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
