#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/determine_spic_answer_transformation_animal_story.py
==============================================================================

A small storyworld about an animal child whose body begins to change. A bright
little firefly named Spic helps the child determine the answer to the mystery:
the change is a true transformation, and the child must wait in the right place
for it to happen safely.

The domain favors a few plausible metamorphosis tales over broad coverage.
Every generated sample has:
- a child-facing animal-story setup,
- a concrete body-change worry,
- a helper who understands the signs,
- a suitable resting place chosen by common sense,
- and an ending image that proves the body has changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/determine_spic_answer_transformation_animal_story.py
    python storyworlds/worlds/gpt-5.4/determine_spic_answer_transformation_animal_story.py --creature caterpillar --place twig
    python storyworlds/worlds/gpt-5.4/determine_spic_answer_transformation_animal_story.py --creature tadpole --place twig
    python storyworlds/worlds/gpt-5.4/determine_spic_answer_transformation_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/determine_spic_answer_transformation_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/determine_spic_answer_transformation_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from io import StringIO
from contextlib import redirect_stdout
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    habitat: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class CreatureForm:
    id: str
    hero_name: str
    start_kind: str
    end_kind: str
    habitat: str
    opening_place: str
    body_sign: str
    fear_image: str
    determine_line: str
    waiting_need: str
    wait_detail: str
    transform_image: str
    ending_image: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RestPlace:
    id: str
    label: str
    phrase: str
    habitat: str
    supports: set[str]
    comfort_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def suitable_place(creature: CreatureForm, place: RestPlace) -> bool:
    return creature.id in place.supports and creature.habitat == place.habitat


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for cid, creature in CREATURES.items():
        for pid, place in PLACES.items():
            if suitable_place(creature, place):
                out.append((cid, pid))
    return sorted(out)


def explain_rejection(creature: CreatureForm, place: RestPlace) -> str:
    if creature.habitat != place.habitat:
        return (
            f"(No story: {creature.start_kind}s in the {creature.habitat} do not make "
            f"their big change on {place.label} in the {place.habitat}. Pick a place "
            f"from the same habitat as the animal's transformation.)"
        )
    return (
        f"(No story: a {creature.start_kind} cannot complete this transformation on "
        f"{place.label}. The resting place must match the real kind of change the body needs.)"
    )


def introduce(world: World, hero: Entity, creature: CreatureForm) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {creature.opening_place}, {hero.id} the little {creature.start_kind} liked to "
        f"notice every bright thing and every soft breeze."
    )
    world.say(
        'One tiny drop landed nearby with a soft "spic," and the small sound made '
        f"{hero.id} stop and listen."
    )


def notice_change(world: World, hero: Entity, creature: CreatureForm) -> None:
    hero.meters["changing"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"But that day, {hero.id} felt different. {creature.body_sign}"
    )
    world.say(
        f"The feeling was so strange that {hero.pronoun()} almost forgot how to play. "
        f"{creature.fear_image}"
    )


def ask_spic(world: World, hero: Entity, creature: CreatureForm, guide: Entity) -> None:
    guide.memes["care"] += 1
    world.say(
        f"{guide.id}, a kind little firefly, drifted close with a lantern-green glow."
    )
    world.say(
        f'"Spic, can you determine the answer?" {hero.id} asked. "{creature.determine_line}"'
    )


def inspect_and_explain(world: World, hero: Entity, creature: CreatureForm,
                        guide: Entity, place: RestPlace) -> None:
    guide.memes["wisdom"] += 1
    hero.memes["trust"] += 1
    world.say(
        f'{guide.id} hovered once around {hero.id}, then once around {place.phrase}. '
        f'"I can," {guide.pronoun()} said gently. "You are not breaking. '
        f'You are getting ready to become a {creature.end_kind}."'
    )
    world.say(
        f'"To do that, you need {creature.waiting_need}, and {place.phrase} is the right place. '
        f'{place.comfort_line}"'
    )


def move_to_place(world: World, hero: Entity, creature: CreatureForm, place: RestPlace) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"{hero.id} was still a little afraid, but {hero.pronoun()} listened. "
        f"{hero.pronoun().capitalize()} went to {place.phrase} and grew very still."
    )
    world.say(
        creature.wait_detail
    )


def transform(world: World, hero: Entity, creature: CreatureForm, place: RestPlace) -> None:
    hero.meters["changing"] = 0.0
    hero.meters["transformed"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["wonder"] += 1
    hero.memes["joy"] += 1
    world.say(
        "At first, nothing seemed to happen but the slow passing of light and shade."
    )
    world.say(
        creature.transform_image
    )
    world.say(
        f"When the waiting was done, {hero.id} was not the same little creature as before. "
        f"{place.ending_line} {creature.ending_image}"
    )


def close_story(world: World, hero: Entity, creature: CreatureForm, guide: Entity) -> None:
    hero.memes["gratitude"] += 1
    world.say(
        f'{hero.id} looked for {guide.id} in the warm air and smiled. '
        f'"Now I know the answer," {hero.pronoun()} said. "{creature.lesson}"'
    )


def tell(creature: CreatureForm, place: RestPlace) -> World:
    world = World()
    hero = world.add(Entity(
        id=creature.hero_name,
        kind="character",
        type=creature.start_kind,
        label=creature.start_kind,
        role="hero",
        habitat=creature.habitat,
    ))
    guide = world.add(Entity(
        id="Spic",
        kind="character",
        type="firefly",
        label="firefly",
        role="guide",
        habitat=creature.habitat,
    ))
    perch = world.add(Entity(
        id="place",
        kind="thing",
        type="rest_place",
        label=place.label,
        habitat=place.habitat,
    ))

    introduce(world, hero, creature)
    notice_change(world, hero, creature)

    world.para()
    ask_spic(world, hero, creature, guide)
    inspect_and_explain(world, hero, creature, guide, place)

    world.para()
    move_to_place(world, hero, creature, place)
    transform(world, hero, creature, place)

    world.para()
    close_story(world, hero, creature, guide)

    world.facts.update(
        hero=hero,
        guide=guide,
        place=perch,
        creature=creature,
        place_cfg=place,
        transformed=hero.meters["transformed"] >= THRESHOLD,
    )
    return world


CREATURES = {
    "caterpillar": CreatureForm(
        "caterpillar",
        "Miri",
        "caterpillar",
        "butterfly",
        "garden",
        "a sunny garden under bean leaves",
        "Her skin felt too tight, and a sleepy, hanging sort of hush kept tugging at her.",
        "Was something wrong with her bright striped body?",
        "Why do I feel so tucked-up and slow today?",
        "a quiet place to hang while the change works",
        "She tucked herself close and let the garden sway around her instead of fighting the stillness.",
        "A neat case held her for a while, and inside it her old shape softened and opened into something new.",
        "Soon soft wings lifted where a small crawling body had been.",
        "Sometimes the right answer is to wait in the right place while your body changes.",
        tags={"metamorphosis", "butterfly", "garden"},
    ),
    "tadpole": CreatureForm(
        "tadpole",
        "Ploop",
        "tadpole",
        "froglet",
        "pond",
        "a round pond with reeds and floating pads",
        "Little legs were pushing out behind him, and his tail did not feel as strong as before.",
        "Was the pond trying to turn him into some other animal?",
        "Why are legs coming where only my tail used to swish?",
        "shallow, quiet water where growing legs can practice",
        "He rested in the warm shallows and let his new legs learn the bottom, one gentle kick at a time.",
        "Day by day the tail that had done all the work grew smaller, while legs and lungs became ready for the world above the water.",
        "At last he could hop from water to mud and back again.",
        "The answer was not danger at all. It was growing into the next true shape of his life.",
        tags={"metamorphosis", "frog", "pond"},
    ),
    "dragonfly_nymph": CreatureForm(
        "dragonfly_nymph",
        "Nim",
        "dragonfly nymph",
        "dragonfly",
        "pond",
        "a clear pond with cattails at the edge",
        "Her shell felt crowded, and a strong climbing wish kept rising through all six little legs.",
        "Why did the water suddenly feel too small for her old body?",
        "Why do I need to climb when I have always lived below the water?",
        "a firm stem above the water so the new body can open safely",
        "She climbed out of the pond and held fast while the breeze touched a body that had always known only water.",
        "The shell split along the back, and a bright new dragonfly slowly drew itself free and waited for its wings to dry wide.",
        "Soon four glassy wings caught the sun and hummed.",
        "Sometimes the answer to a strange feeling is that you are ready for the sky.",
        tags={"metamorphosis", "dragonfly", "pond"},
    ),
}

PLACES = {
    "twig": RestPlace(
        "twig",
        "a sturdy twig",
        "a sturdy twig under a leaf",
        "garden",
        {"caterpillar"},
        "The twig would hold you while you hang safely and let the change happen.",
        "The twig bent softly, then sprang light again.",
        tags={"twig", "garden"},
    ),
    "leaf_underside": RestPlace(
        "leaf_underside",
        "the underside of a leaf",
        "the underside of a broad green leaf",
        "garden",
        {"caterpillar"},
        "The leaf would shade you, hold you, and keep the wind from jostling you too hard.",
        "The leaf trembled once, and then a new small shadow opened beneath it.",
        tags={"leaf", "garden"},
    ),
    "shallow_reeds": RestPlace(
        "shallow_reeds",
        "the shallow reeds",
        "the shallow reeds near the warm edge",
        "pond",
        {"tadpole"},
        "The water there is quiet, and the mud is near enough for new legs to learn both swimming and pushing.",
        "The reeds whispered while a small green shape tested the mud for the first time.",
        tags={"reeds", "pond"},
    ),
    "lily_edge": RestPlace(
        "lily_edge",
        "the edge of a lily pad",
        "the edge of a lily pad in the shallows",
        "pond",
        {"tadpole"},
        "The pad gives shade above and shallow water below, just right for a careful change.",
        "The lily pad rocked once as tiny new feet touched its rim.",
        tags={"lily_pad", "pond"},
    ),
    "cattail_stem": RestPlace(
        "cattail_stem",
        "a cattail stem",
        "a tall cattail stem above the pond",
        "pond",
        {"dragonfly_nymph"},
        "That stem will lift you out of the water, where your new wings can open and dry.",
        "The cattail held still while a clear-winged creature faced the morning.",
        tags={"cattail", "pond"},
    ),
    "reed_stem": RestPlace(
        "reed_stem",
        "a reed stem",
        "a smooth reed stem at the pond edge",
        "pond",
        {"dragonfly_nymph"},
        "A reed is firm enough for climbing and high enough to keep your new wings clear of the water.",
        "The reed shimmered as a humming body gripped it with fresh strength.",
        tags={"reed", "pond"},
    ),
    "flat_rock": RestPlace(
        "flat_rock",
        "a flat rock",
        "a flat rock in the open",
        "shore",
        set(),
        "It is warm there, but warmth alone is not the right kind of help.",
        "The rock only sat there.",
        tags={"rock"},
    ),
}


@dataclass
class StoryParams:
    creature: str
    place: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "metamorphosis": [
        (
            "What is metamorphosis?",
            "Metamorphosis is a big body change that some animals go through as they grow. The animal does not turn into a different kind of life by magic; it grows into its next real form."
        )
    ],
    "butterfly": [
        (
            "How does a caterpillar become a butterfly?",
            "A caterpillar makes a case and stays still while its body changes inside. Later it comes out as a butterfly with wings."
        )
    ],
    "frog": [
        (
            "How does a tadpole become a frog?",
            "A tadpole grows legs and lungs while its tail shrinks. After that, it can live in water and on land."
        )
    ],
    "dragonfly": [
        (
            "How does a dragonfly nymph become a dragonfly?",
            "A dragonfly nymph climbs out of the water onto a stem. Its old shell opens, and the dragonfly comes out and waits for its wings to dry."
        )
    ],
    "garden": [
        (
            "Why do many insects use leaves and twigs?",
            "Leaves and twigs can hold small bodies safely while they rest or change. They also give some shade and shelter from bumps."
        )
    ],
    "pond": [
        (
            "Why is a pond edge good for many small animals?",
            "A pond edge has shallow water, plants, and quiet places to hide. That makes it helpful for young animals that are still growing."
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall pond plants with long stems. Small animals can hide beside them or climb on them."
        )
    ],
    "lily_pad": [
        (
            "What is a lily pad?",
            "A lily pad is a round leaf that floats on pond water. Frogs, bugs, and other little creatures often rest near it."
        )
    ],
    "cattail": [
        (
            "What is a cattail?",
            "A cattail is a tall wetland plant that grows beside ponds. Its stems can give small animals a place to climb."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "metamorphosis",
    "butterfly",
    "frog",
    "dragonfly",
    "garden",
    "pond",
    "reeds",
    "lily_pad",
    "cattail",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    creature: CreatureForm = f["creature"]
    place: RestPlace = f["place_cfg"]
    hero: Entity = f["hero"]
    return [
        'Write a gentle Animal Story for a 3-to-5-year-old that includes the words "determine", "spic", and "answer", and uses a real animal transformation.',
        f"Tell an animal story where {hero.id} the {creature.start_kind} feels a strange body change, asks Spic for help, and learns the answer by waiting at {place.phrase}.",
        f"Write a story about metamorphosis with a worried young animal, a kind firefly named Spic, and an ending image that proves the animal became a {creature.end_kind}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    creature: CreatureForm = f["creature"]
    place: RestPlace = f["place_cfg"]
    hero: Entity = f["hero"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {creature.start_kind}, and Spic the firefly. Spic notices the signs of change and helps {hero.id} feel less afraid."
        ),
        (
            f"Why was {hero.id} worried at the beginning?",
            f"{hero.id} felt a real body change and did not understand it yet. The strange feeling made {hero.pronoun()} wonder whether something was wrong, because the change had started before {hero.pronoun()} knew its purpose."
        ),
        (
            'What did Spic help determine?',
            f'Spic helped determine the answer to the mystery of {hero.id}\'s changing body. Spic explained that the change was a true transformation into a {creature.end_kind}, not an injury or a mistake.'
        ),
        (
            f"Why did {hero.id} need to go to {place.label}?",
            f"{hero.id} needed the right place for the transformation to work safely. {place.comfort_line} That is why the resting place mattered, not just being brave."
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                f"What changed by the end of the story?",
                f"By the end, {hero.id} had become a {creature.end_kind}. The ending proves the change with a new body image, showing that waiting in the right place let the transformation finish."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with understanding instead of fear. {hero.id} finally knew the answer to the strange feeling and could see that the body change had a good purpose."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["creature"].tags) | set(f["place_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.habitat:
            bits.append(f"habitat={ent.habitat}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:16}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("caterpillar", "twig"),
    StoryParams("caterpillar", "leaf_underside"),
    StoryParams("tadpole", "shallow_reeds"),
    StoryParams("tadpole", "lily_edge"),
    StoryParams("dragonfly_nymph", "cattail_stem"),
    StoryParams("dragonfly_nymph", "reed_stem"),
]


ASP_RULES = r"""
suitable(C, P) :- creature(C), place(P), needs_habitat(C, H), habitat(P, H), supports(P, C).
valid(C, P) :- suitable(C, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, creature in CREATURES.items():
        lines.append(asp.fact("creature", cid))
        lines.append(asp.fact("needs_habitat", cid, creature.habitat))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("habitat", pid, place.habitat))
        for cid in sorted(place.supports):
            lines.append(asp.fact("supports", pid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        with redirect_stdout(StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal-story transformation world. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (creature, place) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.creature and args.place:
        creature, place = CREATURES[args.creature], PLACES[args.place]
        if not suitable_place(creature, place):
            raise StoryError(explain_rejection(creature, place))

    combos = [
        combo for combo in valid_combos()
        if (args.creature is None or combo[0] == args.creature)
        and (args.place is None or combo[1] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    creature_id, place_id = rng.choice(combos)
    return StoryParams(creature_id, place_id)


def generate(params: StoryParams) -> StorySample:
    creature = CREATURES[params.creature]
    place = PLACES[params.place]
    if not suitable_place(creature, place):
        raise StoryError(explain_rejection(creature, place))

    world = tell(creature, place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (creature, place) combos:\n")
        for creature, place in combos:
            print(f"  {creature:16} {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.creature} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
