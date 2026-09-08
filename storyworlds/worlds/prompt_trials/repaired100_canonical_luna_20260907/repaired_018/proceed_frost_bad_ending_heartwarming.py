#!/usr/bin/env python3
"""
A small heartwarming storyworld about proceeding through frost, a bad ending
that almost happens, and a gentle repair that brings warmth back.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "results.py").is_file()
)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


PLACES = [
    "the hilltop garden",
    "the little footbridge",
    "the village square",
    "the orchard path",
    "the blue-painted porch",
]
HEROES = ["Luna", "Mira", "Theo", "Nell", "Ari", "Pia"]
HELPERS = ["Grandma June", "Uncle Sol", "Mr. Rowan", "Aunt Bea"]
GIFTS = ["a red scarf", "a jar of honey", "a paper lantern", "a wool hat", "a warm loaf"]
ANIMALS = ["a small robin", "a sleepy hedgehog", "a white rabbit", "a shy fox"]

@dataclass
class StoryParams:
    hero: str
    helper: str
    place: str
    gift: str
    animal: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Arc:
    purpose: str
    frost_problem: str
    bad_ending: str
    mistaken_belief: str
    clue: str
    dialogue_helper: str
    dialogue_hero: str
    test: str
    hero_action: str
    helper_action: str
    repair: str
    result: str
    ending: str


ARCS = [
    Arc(
        purpose="carry a red scarf to a shivering robin",
        frost_problem="a hard frost sealed the garden gate",
        bad_ending="the robin would spend the cold night without its nest blanket",
        mistaken_belief="the gate was simply too stuck for anyone to open",
        clue="a thin sunny line shone beneath the latch",
        dialogue_helper="We should turn back before the path becomes dangerous.",
        dialogue_hero="Let us proceed slowly, and look for what the frost is telling us.",
        test="held the scarf near the latch and watched one loose ice crystal melt",
        hero_action="wrapped the scarf around the cold metal latch",
        helper_action="pressed the gate gently while the frost softened",
        repair="they cleared the hinge with a warm cloth instead of forcing it",
        result="the gate opened with a quiet creak",
        ending="the robin tucked its beak beneath the red scarf while the garden glittered with safe, melting frost",
    ),
    Arc(
        purpose="bring honey to a sleepy hedgehog",
        frost_problem="the orchard path was white and slippery",
        bad_ending="the hedgehog would miss its warm supper",
        mistaken_belief="the path could not be crossed at all",
        clue="a row of dry stepping stones showed beneath the pale frost",
        dialogue_helper="This looks like a road made of glass.",
        dialogue_hero="Then we will proceed stone by stone, with our hands ready to help.",
        test="tapped each stone with a mitten before stepping forward",
        hero_action="marked the safe stones with little pinecones",
        helper_action="carried the honey jar with both hands",
        repair="they laid a path of straw over the slickest places",
        result="they reached the hedgehog without spilling a drop",
        ending="the hedgehog licked honey from a leaf as warm straw made a golden trail through the frost",
    ),
    Arc(
        purpose="hang a paper lantern for a lonely neighbor",
        frost_problem="the lantern string snapped in the freezing wind",
        bad_ending="the porch would remain dark and the neighbor might feel forgotten",
        mistaken_belief="the lantern itself had been ruined",
        clue="the paper shade was whole, but one knot had loosened",
        dialogue_helper="The evening is almost here. We may have lost our chance.",
        dialogue_hero="A loose knot is not the same as a lost lantern. We can proceed together.",
        test="pulled the string lightly and found the break at one small knot",
        hero_action="held the lantern steady against the wind",
        helper_action="tied a new loop with wool yarn",
        repair="they added a second knot and sheltered the string behind the porch rail",
        result="the lantern glowed before the first star appeared",
        ending="the neighbor opened the door to a warm circle of light, and the frost shone like sugar",
    ),
    Arc(
        purpose="deliver a wool hat to a tired fox",
        frost_problem="snowy branches bent across the forest path",
        bad_ending="the fox would stay cold beneath the fallen branches",
        mistaken_belief="the forest had become completely closed",
        clue="tiny paw prints continued beneath one low branch",
        dialogue_helper="The woods say stop.",
        dialogue_hero="Perhaps they say go low. We can proceed where the paw prints lead.",
        test="crawled beneath the branch and checked that the ground was firm",
        hero_action="held the hat above the fox's den",
        helper_action="moved only the light branches away from the path",
        repair="they made a small tunnel and left the heavy branches undisturbed",
        result="the hat reached the fox safely",
        ending="the fox curled beneath the wool hat while frost feathers sparkled on the quiet trees",
    ),
    Arc(
        purpose="share a warm loaf with a neighbor at the footbridge",
        frost_problem="the bridge boards were coated with slippery frost",
        bad_ending="the loaf might fall into the stream and the neighbor might wait alone",
        mistaken_belief="the only choice was to rush across",
        clue="the handrail was dry where sunlight touched it",
        dialogue_helper="If we hurry, we could lose both our balance and our bread.",
        dialogue_hero="Then we will proceed by the sunny rail, one careful step at a time.",
        test="rubbed a small board with a mitten and found solid wood beneath the ice",
        hero_action="kept the loaf tucked close to the chest",
        helper_action="held the handrail and offered a steady arm",
        repair="they brushed the frost away from a narrow walking line",
        result="the loaf arrived warm and whole",
        ending="three friends shared the bread beside the bridge while the stream carried tiny stars of frost downstream",
    ),
]


OPENINGS = [
    "One frosty morning, {hero} pulled on warm boots and looked toward {place}.",
    "At dawn, {hero} found {place} sparkling under a blanket of frost.",
    "The first cold light touched {place}, and {hero} tucked a careful gift under one arm.",
    "{hero} and {helper} stood at the edge of {place}, where every leaf wore a rim of frost.",
]

HUMOR = [
    "{helper} said the scarf looked ready to become a very small superhero cape.",
    "The hedgehog's nose twitched as if it had heard the honey jar from miles away.",
    "The lantern bobbed like a tiny moon wearing a woolen belt.",
    "The fox blinked at the hat, as though deciding whether it was fashionable enough for winter.",
    "The loaf gave off such a good smell that even the bridge seemed to lean closer.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heartwarming frost-and-proceed storyworld.")
    parser.add_argument("--hero")
    parser.add_argument("--helper")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--gift", choices=GIFTS)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        gift=args.gift or rng.choice(GIFTS),
        animal=args.animal or rng.choice(ANIMALS),
    )


def build_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different characters")
    world = World(params)
    world.add(Entity("hero", "character", params.hero, "child", memes={"kindness": 1.0}))
    world.add(Entity("helper", "character", params.helper, "adult", memes={"care": 1.0}))
    world.add(Entity("gift", "thing", params.gift, "gift", meters={"warmth": 0.5}))
    world.add(Entity("frost", "thing", "frost", "weather", meters={"cold": 1.0}))
    world.add(Entity("animal", "creature", params.animal, "neighbor", memes={"hope": 0.5}))
    return world


def story_variation(params: StoryParams) -> int:
    text = "|".join([params.hero, params.helper, params.place, params.gift, params.animal])
    base = params.seed if params.seed is not None else sum((i + 1) * ord(c) for i, c in enumerate(text))
    return (base * 97 + 11) % (len(ARCS) * len(OPENINGS))


def generate_story(world: World) -> None:
    p = world.params
    hero = world.entities["hero"]
    helper = world.entities["helper"]
    frost = world.entities["frost"]
    variation = story_variation(p)
    arc = ARCS[variation % len(ARCS)]
    opening = OPENINGS[(variation // len(ARCS)) % len(OPENINGS)].format(
        hero=p.hero, helper=p.helper, place=p.place
    )

    world.say(opening)
    world.say(
        f"{p.hero} carried {p.gift}, because the plan was to {arc.purpose}. "
        f"{p.helper} came along with a warm smile and two careful pairs of hands."
    )
    world.para()
    world.say(f"But {arc.frost_problem}.")
    world.say(
        f"If they stopped, {arc.bad_ending}; if they rushed, someone could get hurt. "
        f"For a moment, {p.hero} believed {arc.mistaken_belief}."
    )
    frost.meters["cold"] = 1.0
    hero.memes["worry"] = 1.0
    world.facts["bad_ending"] = arc.bad_ending
    world.say(f'{p.helper} said, "{arc.dialogue_helper}"')
    world.say(f'{p.hero} answered, "{arc.dialogue_hero}"')
    world.para()
    world.say(f"Then {p.hero} noticed {arc.clue}.")
    world.say(f"To learn more, {p.hero} {arc.test}.")
    world.say(f"The clue showed that they could proceed safely if they worked gently.")
    world.say(HUMOR[ARCS.index(arc)])
    hero.memes["curiosity"] = 1.0
    helper.memes["trust"] = 1.0
    world.facts["clue"] = arc.clue
    world.facts["test"] = arc.test
    world.para()
    world.say(f"{p.hero} {arc.hero_action}, while {p.helper} {arc.helper_action}.")
    world.say(f"Together, they {arc.repair}.")
    world.say(f"At last, {arc.result}.")
    world.say(f"The bad ending slipped away, because kindness had made another ending possible: {arc.ending}.")
    frost.meters["cold"] = 0.25
    hero.memes["joy"] = 2.0
    helper.memes["joy"] = 1.0
    world.facts.update(
        purpose=arc.purpose,
        frost_problem=arc.frost_problem,
        mistaken_belief=arc.mistaken_belief,
        hero_action=arc.hero_action,
        helper_action=arc.helper_action,
        repair=arc.repair,
        result=arc.result,
        ending=arc.ending,
        proceed=True,
        heartwarming=True,
        settled=True,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a heartwarming children's story about {p.hero} proceeding through frost at {p.place} to deliver {p.gift}.",
        f"Tell a gentle story where {p.hero} and {p.helper} avoid a bad ending by noticing a clue and helping {p.animal}.",
        "Create a child-facing story using the words proceed and frost, with dialogue, a careful turn, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"Why did {p.hero} go to {p.place}?",
            answer=f"{p.hero} went there to {f['purpose']}. The gift mattered because leaving the journey unfinished could have led to {f['bad_ending']}.",
        ),
        QAItem(
            question=f"What did {p.hero} notice in the frost?",
            answer=f"{p.hero} noticed that {f['clue']}. After testing it by {f['test']}, the two friends understood how to proceed safely.",
        ),
        QAItem(
            question=f"How did {p.hero} and {p.helper} solve the problem?",
            answer=f"{p.hero} {f['hero_action']}, while {p.helper} {f['helper_action']}. Together, they {f['repair']}.",
        ),
        QAItem(
            question="How did the story avoid its bad ending?",
            answer=f"The bad ending was avoided through patience and teamwork. {p.hero} and {p.helper} proceeded carefully, so {f['result']}.",
        ),
        QAItem(
            question=f"What warm picture ended {p.hero}'s journey?",
            answer=f"The story ended with {f['ending']}. The frost no longer felt like only a barrier; it made the warm act of helping shine brighter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is frost?",
            answer="Frost is a thin layer of ice that forms when water in the air freezes on a cold surface.",
        ),
        QAItem(
            question="What does it mean to proceed?",
            answer="To proceed means to continue moving or acting, usually after deciding how to do something safely.",
        ),
        QAItem(
            question="Why is patience useful in cold weather?",
            answer="Patience helps people notice slippery places, protect one another, and choose a safe way forward instead of rushing.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:9}) {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for gift in GIFTS:
        lines.append(asp.fact("gift", gift))
    for animal in ANIMALS:
        lines.append(asp.fact("animal", animal))
    lines.extend(
        [
            asp.fact("feature", "proceed"),
            asp.fact("feature", "frost"),
            asp.fact("feature", "bad_ending"),
            asp.fact("style", "heartwarming"),
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
journey(P,G,A) :- place(P), gift(G), animal(A), feature(proceed).
frosty(P) :- place(P), feature(frost).
bad_ending_risk(P) :- frosty(P), feature(bad_ending).
heartwarming(P,G,A) :- journey(P,G,A), style(heartwarming).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(
            asp_program(
                "#show journey/3.\n"
                "#show frosty/1.\n"
                "#show bad_ending_risk/1.\n"
                "#show heartwarming/3."
            )
        )
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    journeys = set(asp.atoms(model, "journey"))
    frosty = set(asp.atoms(model, "frosty"))
    risks = set(asp.atoms(model, "bad_ending_risk"))
    warm = set(asp.atoms(model, "heartwarming"))
    want_journeys = {(p, g, a) for p in PLACES for g in GIFTS for a in ANIMALS}
    ok = (
        journeys == want_journeys
        and frosty == {(p,) for p in PLACES}
        and risks == {(p,) for p in PLACES}
        and warm == want_journeys
    )
    if not ok:
        print("Mismatch between ASP and Python registries.")
        return 1
    for params in [
        StoryParams("Luna", "Grandma June", PLACES[0], GIFTS[0], ANIMALS[0]),
        StoryParams("Mira", "Uncle Sol", PLACES[1], GIFTS[1], ANIMALS[1]),
    ]:
        sample = generate(params)
        if not sample.story or "proceed" not in sample.story or "frost" not in sample.story:
            print("Generated story exercise failed.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("Luna", "Grandma June", PLACES[0], GIFTS[0], ANIMALS[0]),
    StoryParams("Mira", "Uncle Sol", PLACES[1], GIFTS[1], ANIMALS[1]),
    StoryParams("Theo", "Mr. Rowan", PLACES[2], GIFTS[2], ANIMALS[2]),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"P{index}: {prompt}")
        print()
        for item in sample.story_qa + sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show journey/3.\n"
            "#show frosty/1.\n"
            "#show bad_ending_risk/1.\n"
            "#show heartwarming/3."
        ))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(
                asp_program(
                    "#show journey/3.\n"
                    "#show frosty/1.\n"
                    "#show bad_ending_risk/1.\n"
                    "#show heartwarming/3."
                )
            )
        except Exception as exc:
            raise StoryError(f"ASP mode unavailable: {exc}") from exc
        print(f"journey={len(asp.atoms(model, 'journey'))}")
        print(f"frosty={len(asp.atoms(model, 'frosty'))}")
        print(f"bad_ending_risk={len(asp.atoms(model, 'bad_ending_risk'))}")
        print(f"heartwarming={len(asp.atoms(model, 'heartwarming'))}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n * 30, 30)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
        header = ""
        if args.all:
            header = f"### {sample.params.hero} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
