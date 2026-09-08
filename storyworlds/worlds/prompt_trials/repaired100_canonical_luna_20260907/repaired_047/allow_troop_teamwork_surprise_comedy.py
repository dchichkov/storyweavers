#!/usr/bin/env python3
"""
A standalone storyworld about a comic troop learning to allow teamwork and
make a surprise performance succeed.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
reasonable_story :- has_teamwork, has_surprise, has_comedy.
useful_prop(P) :- prop(P), portable(P).
good_plan :- reasonable_story, allows_listening, shared_timing.
"""

PLACE = "the old town square"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def bump_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def bump_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount


@dataclass
class StoryParams:
    leader: str
    troop: str
    prop: str
    surprise: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    trouble: str
    failed_try: str
    clue: str
    line_one: str
    line_two: str
    repair: str
    result: str
    ending: str


@dataclass
class World:
    place: str = PLACE
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

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
        for entity in self.entities.values():
            bits = []
            if entity.meters:
                bits.append(f"meters={dict(entity.meters)}")
            if entity.memes:
                bits.append(f"memes={dict(entity.memes)}")
            if entity.label:
                bits.append(f"label={entity.label!r}")
            lines.append(
                f"  {entity.id:10} ({entity.kind:9}) {' '.join(bits)}"
            )
        lines.append(f"  facts: {self.facts}")
        return "\n".join(lines)


SCENARIOS = [
    Scenario(
        key="backward_parade",
        premise="was rehearsing a surprise parade for the mayor's birthday",
        trouble="The troop marched backward into the lemonade stand and sent three lemons rolling like tiny yellow drums.",
        failed_try="pretending nothing happened made the drummer march backward into the same stand",
        clue="the parade map had arrows pointing in opposite directions",
        line_one='"The arrows are arguing," said Pippa.',
        line_two='"Then we should let each marcher choose a direction," said Milo.',
        repair="turned the map around, let each performer name a safe place, and counted the steps together",
        result="The troop reached the square without bumping a single cup",
        ending="the mayor opened the surprise curtain just as a lemon rolled forward and bowed",
    ),
    Scenario(
        key="giant_hat",
        premise="was hiding a giant hat for a surprise bow",
        trouble="The hat was so large that it covered the prop cart, the lantern, and nearly the troop leader.",
        failed_try="pushing it from one side only made the hat spin around the square",
        clue="the hat had four loops beneath its brim",
        line_one='"There are four loops," said Niko. "That sounds like four helpers."',
        line_two='"I will allow everyone to pull," said the leader, "but only when we count."',
        repair="placed one performer at each loop and pulled gently on the shared count",
        result="The hat settled on its stand instead of sailing into the fountain",
        ending="when the curtain rose, the hat wore a tiny flower and everyone laughed",
    ),
    Scenario(
        key="silent_trumpet",
        premise="was preparing a secret trumpet fanfare",
        trouble="The trumpet made no sound except a soft sneeze whenever the player blew.",
        failed_try="blowing harder made the trumpet sneeze three times and frighten a pigeon",
        clue="the mouthpiece was resting upside down in the prop basket",
        line_one='"May I look too?" asked Tula.',
        line_two='"Yes," said the player. "I should allow another pair of eyes."',
        repair="shared the basket, turned the mouthpiece the right way, and practiced the opening note together",
        result="The trumpet sang a bright call that made the pigeon dance instead of flee",
        ending="the surprise began with one clear note and ended with the pigeon taking a bow",
    ),
    Scenario(
        key="runaway_ribbons",
        premise="was tying colorful ribbons around the square for a surprise celebration",
        trouble="A gust lifted the ribbons and wrapped them around the troop's ankles.",
        failed_try="everyone tugged at once and made one enormous ribbon knot",
        clue="the loose ends all pointed toward the same fence",
        line_one='"Let us stop pulling," said Bea. "The ribbons are telling us where they went."',
        line_two='"I will allow a calm untangler to lead," said the leader.',
        repair="followed the loose ends, gave each performer one strand, and untied the knot from the fence inward",
        result="The ribbons flew above the square in neat loops",
        ending="the surprise guests arrived beneath a rainbow that tickled everyone's noses",
    ),
    Scenario(
        key="sleepy_dragon",
        premise="was practicing a surprise puppet show about a brave dragon",
        trouble="The dragon puppet fell asleep halfway through every roar.",
        failed_try="shouting into its cloth mouth made the puppet hiccup instead",
        clue="one puppet string was caught around the dragon's tail",
        line_one='"The dragon is tangled, not tired," said Jun.',
        line_two='"Good spotting," said the leader. "I will allow your plan to lead."',
        repair="held the dragon steady while Jun freed the string and the rest of the troop rehearsed a softer roar",
        result="The dragon roared on cue and politely sneezed smoke-colored confetti",
        ending="the audience gasped at the surprise, then laughed when the dragon bowed too low",
    ),
    Scenario(
        key="mixed_up_cues",
        premise="was planning a surprise comedy routine with three secret entrances",
        trouble="The cue cards had been shuffled, so the clown entered whenever someone said 'banana.'",
        failed_try="saying 'banana' less often only made the clown wait beside the wrong door",
        clue="each card carried a different colored dot",
        line_one='"The dots can sort the doors," said Rosa.',
        line_two='"And we can allow one caller to give every cue," said the clown.',
        repair="sorted the cards by color, chose one caller, and practiced the entrances in a shared rhythm",
        result="The clown appeared at the correct door with a banana balanced on one shoe",
        ending="the secret routine surprised everyone, including the clown",
    ),
    Scenario(
        key="backwards_banner",
        premise="was hanging a surprise banner across the square",
        trouble="The banner read 'WELCOME' backward, which made the visiting baker think it said 'EMOCLEW.'",
        failed_try="turning it around while everyone held one end made the banner wrap around a lamppost",
        clue="the picture of a smiling sun was printed on the outside edge",
        line_one='"The sun should face the guests," said Ada.',
        line_two='"Then I will allow the tallest and shortest helpers to work together," said the leader.',
        repair="let the tall performer lift while the short performer guided the bottom edge around the post",
        result="The banner stretched straight and welcomed the baker properly",
        ending="the baker read the message, then offered the troop a cake shaped like a backward word",
    ),
    Scenario(
        key="drumroll_rain",
        premise="was hiding a surprise drumroll beneath a covered stage",
        trouble="A quick rain shower filled the drum with water and turned the roll into a glug-glug.",
        failed_try="shaking it upside down splashed the leader's shoes and one very serious duck",
        clue="the stage cover had a dry corner near the old bench",
        line_one='"We need dry hands before loud hands," said Sol.',
        line_two='"Agreed," said the leader. "Everyone may help, but nobody needs to hurry."',
        repair="carried the drum to the dry corner, emptied it carefully, and shared cloths for the final drops",
        result="The drum made a proud rolling thunder instead of a watery burp",
        ending="the surprise ended with applause, rain boots, and the duck keeping perfect time",
    ),
    Scenario(
        key="vanishing_cake",
        premise="was guarding a surprise cake for the troop's final bow",
        trouble="The cake disappeared from the table just before the guests arrived.",
        failed_try="accusing the smallest performer made everyone search the wrong side of the square",
        clue="a trail of sugar crumbs led behind the painted scenery",
        line_one='"We should follow the crumbs, not guesses," said Kit.',
        line_two='"You are right. I will allow the whole troop to search in pairs," said the leader.',
        repair="searched in pairs and found the cake balanced safely on the scenery's hidden shelf",
        result="The cake reached the table with only one frosting mustache missing",
        ending="the guest of honor cut the cake and gave the frosting mustache to the troop leader",
    ),
    Scenario(
        key="tumbling_stools",
        premise="was arranging stools for a surprise circle of jokes",
        trouble="The stools wobbled and sent each performer sitting down a moment too early.",
        failed_try="stacking them higher made the first stool sneeze sawdust",
        clue="one leg on every stool faced the same cracked paving stone",
        line_one='"The ground is the trouble," said Mira.',
        line_two='"Then let us allow the square to help us," said the leader, pointing to the smooth stones.',
        repair="moved the circle onto smooth paving and tested each stool with one careful tap",
        result="The performers sat at the proper time and no one landed in the flower box",
        ending="the surprise jokes began together, while the flower box kept one extra stool for a laughing guest",
    ),
]


NAMES = ["Luna", "Pip", "Milo", "Pippa", "Niko", "Tula", "Bea", "Jun", "Rosa", "Ada"]
TROOPS = ["the Moonbeam Players", "the Wiggly Whistles", "the Pocket Parade", "the Laughing Lanterns"]
PROPS = ["hat", "trumpet", "ribbon", "puppet", "banner", "drum", "cake", "stool"]
SURPRISES = ["birthday bow", "secret parade", "comedy show", "hidden fanfare"]


def reasonableness_gate(params: StoryParams) -> None:
    if not params.leader.strip():
        raise StoryError("The troop needs a named leader.")
    if params.troop not in TROOPS:
        raise StoryError("The troop must be a small, friendly performance group.")
    if params.prop not in PROPS:
        raise StoryError("The prop must be a simple, safe performance object.")
    if params.surprise not in SURPRISES:
        raise StoryError("The surprise must be a cheerful performance event.")


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("has_teamwork"),
        asp.fact("has_surprise"),
        asp.fact("has_comedy"),
        asp.fact("allows_listening"),
        asp.fact("shared_timing"),
    ]
    for prop in PROPS:
        lines.append(asp.fact("prop", prop))
        lines.append(asp.fact("portable", prop))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_params(rng: random.Random) -> StoryParams:
    return StoryParams(
        leader=rng.choice(NAMES),
        troop=rng.choice(TROOPS),
        prop=rng.choice(PROPS),
        surprise=rng.choice(SURPRISES),
        seed=rng.randrange(2**31),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Comedy storyworld about a teamwork-minded performance troop."
    )
    parser.add_argument("--leader")
    parser.add_argument("--troop", choices=TROOPS)
    parser.add_argument("--prop", choices=PROPS)
    parser.add_argument("--surprise", choices=SURPRISES)
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
    params = valid_params(rng)
    if args.leader:
        params.leader = args.leader
    if args.troop:
        params.troop = args.troop
    if args.prop:
        params.prop = args.prop
    if args.surprise:
        params.surprise = args.surprise
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    world = World()
    world.add(Entity(id="leader", kind="character", label=params.leader))
    world.add(Entity(id="troop", kind="group", label=params.troop))
    world.add(Entity(id="prop", kind="prop", label=params.prop))
    world.add(Entity(id="surprise", kind="event", label=params.surprise))
    world.facts.update(
        place=PLACE,
        teamwork=True,
        surprise=True,
        comedy=True,
        leader=params.leader,
        troop=params.troop,
        prop=params.prop,
        surprise_name=params.surprise,
    )
    return world


def tell_story(world: World, params: StoryParams) -> None:
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = rng.choice(SCENARIOS)
    leader = world.get("leader")
    troop = world.get("troop")
    prop = world.get("prop")

    leader.bump_meme("responsibility")
    troop.bump_meme("teamwork")
    prop.bump_meter("importance")

    world.say(
        f"In {PLACE}, {leader.label} led {troop.label}, a comedy troop famous for "
        f"surprises, wobbly entrances, and one very determined {prop.label}."
    )
    world.say(
        f"They were preparing a {params.surprise} when {leader.label} {scenario.premise}."
    )
    world.para()

    leader.bump_meme("worry")
    world.say(scenario.trouble)
    world.say(f"At first, {leader.label} tried to fix it alone, but {scenario.failed_try}.")
    world.say(
        f"{leader.label} stopped and said, 'I will allow everyone to look closely before we try again.'"
    )
    world.para()

    troop.bump_meme("curiosity")
    world.say(f"Then the troop noticed that {scenario.clue}.")
    world.say(scenario.line_one)
    world.say(scenario.line_two)
    world.say(
        "The performers listened to one another, because a good surprise needs room "
        "for every useful idea."
    )
    world.para()

    leader.bump_meme("trust")
    troop.bump_meter("shared_actions")
    world.say(f"Together, they {scenario.repair}.")
    world.say(
        f"They counted, waited, and moved as one. Soon {scenario.result}."
    )
    world.para()

    leader.bump_meme("joy")
    troop.bump_meme("joy")
    world.facts.update(
        scenario=scenario.key,
        trouble=scenario.trouble,
        failed_try=scenario.failed_try,
        clue=scenario.clue,
        line_one=scenario.line_one,
        line_two=scenario.line_two,
        repair=scenario.repair,
        result=scenario.result,
        ending=scenario.ending,
        resolved=True,
    )
    world.say(
        f"The audience arrived just in time for the surprise. {scenario.ending}."
    )
    world.say(
        f"{leader.label} smiled and said, 'When we allow teamwork, even a muddle can become a marvelous joke.'"
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly comedy about {facts['leader']} leading {facts['troop']} in {PLACE}.",
        "Use the words allow and troop in a story where teamwork saves a surprise.",
        f"Tell a funny performance story involving a {facts['prop']} and a shared solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    return [
        QAItem(
            question="What problem interrupted the troop's surprise?",
            answer=str(facts["trouble"]),
        ),
        QAItem(
            question="What clue helped the performers understand the problem?",
            answer=f"They noticed that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did {facts['troop']} use teamwork?",
            answer=f"Together, they {facts['repair']}.",
        ),
        QAItem(
            question="What changed after the troop worked together?",
            answer=str(facts["result"]) + ".",
        ),
        QAItem(
            question="What showed that the surprise ended happily?",
            answer=str(facts["ending"]) + ".",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share ideas and actions to solve something together.",
        ),
        QAItem(
            question="What does allow mean?",
            answer="Allow means to let someone do something or to make room for a choice.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something prepared or discovered that someone did not expect.",
        ),
        QAItem(
            question="What is a comedy?",
            answer="A comedy is a story or performance made to bring laughter and cheerful feelings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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


def asp_verify() -> int:
    import asp

    program = asp_program(
        "#show reasonable_story/0.\n#show useful_prop/1.\n#show good_plan/0."
    )
    model = asp.one_model(program)
    found = set()
    for symbol in model:
        if symbol.name == "reasonable_story" and not symbol.arguments:
            found.add(("reasonable_story", ()))
        elif symbol.name == "good_plan" and not symbol.arguments:
            found.add(("good_plan", ()))
        elif symbol.name == "useful_prop":
            args = tuple(
                arg.name if arg.type != 4 else arg.string
                for arg in symbol.arguments
            )
            found.add(("useful_prop", args))

    expected = {
        ("reasonable_story", ()),
        ("good_plan", ()),
    }
    expected.update(("useful_prop", (prop,)) for prop in PROPS)

    if found == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(found))
    print("PY :", sorted(expected))
    return 1


def asp_list() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_plan/0.\n#show useful_prop/1."))
    result = []
    for symbol in model:
        if symbol.name == "good_plan" and not symbol.arguments:
            result.append(("good_plan",))
        elif symbol.name == "useful_prop":
            result.append(
                (
                    "useful_prop",
                    symbol.arguments[0].name
                    if symbol.arguments[0].type != 4
                    else symbol.arguments[0].string,
                )
            )
    return sorted(result)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    tell_story(world, params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        leader="Luna",
        troop="the Moonbeam Players",
        prop="hat",
        surprise="birthday bow",
        seed=17,
    ),
    StoryParams(
        leader="Pip",
        troop="the Wiggly Whistles",
        prop="trumpet",
        surprise="secret parade",
        seed=31,
    ),
    StoryParams(
        leader="Milo",
        troop="the Laughing Lanterns",
        prop="puppet",
        surprise="comedy show",
        seed=53,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonable_story/0.\n#show good_plan/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP-compatible teamwork comedy facts:")
        for item in asp_list():
            print(item)
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1.")

    rng = random.Random(
        args.seed if args.seed is not None else random.randrange(2**31)
    )

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(100, args.n * 100):
            params = resolve_params(
                args, random.Random(rng.randrange(2**31))
            )
            sample = generate(params)
            attempts += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

        if len(samples) < args.n:
            raise SystemExit("Could not generate enough distinct stories.")

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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
