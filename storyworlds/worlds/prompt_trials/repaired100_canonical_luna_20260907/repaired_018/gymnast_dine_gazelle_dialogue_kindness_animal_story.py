#!/usr/bin/env python3
"""
A gentle animal storyworld about a gymnast, a gazelle, a shared dinner,
and the kindness that helps a nervous friend try again.
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


GYMNASTS = ["Lina", "Mara", "Toby", "Nia", "Owen", "Suri"]
GAZELLES = ["Gigi", "Zara", "Fara", "Kito", "Mina", "Dali"]
MEALS = ["carrot stew", "berry porridge", "warm grass cakes", "melon soup"]
PLACES = ["the sunlit meadow", "the acacia grove", "the riverside clearing", "the red-dust field"]

ARCS = [
    {
        "trouble": "the gazelle froze before the tall grass hurdle",
        "cause": "a loose vine had curled across the landing place",
        "clue": "the vine trembled whenever the wind touched it",
        "kind_action": "cleared the vine and practiced beside the low stones first",
        "result": "the gazelle sprang over the hurdle with a bright, easy leap",
        "ending": "the friends shared dinner beneath an acacia tree while the hurdle cast a tiny shadow",
        "worry": "I cannot jump with that strange vine waiting below me!",
        "reply": "You do not have to hurry. We can make the landing safe together.",
        "lesson": "kindness made room for courage",
    },
    {
        "trouble": "the gazelle stumbled during a careful balance pose",
        "cause": "a smooth seed pod had rolled beneath one hoof",
        "clue": "the pod gleamed beside the practice mat",
        "kind_action": "moved the pod and invited the gazelle to balance while holding a soft branch",
        "result": "the gazelle held the pose long enough for a butterfly to land nearby",
        "ending": "they dined together as the butterfly circled their picnic cloth",
        "worry": "Everyone will laugh if I fall again.",
        "reply": "A fall is only one moment. I will stay beside you while you try again.",
        "lesson": "kind words helped a mistake become practice",
    },
    {
        "trouble": "the gazelle would not enter the circle for the evening routine",
        "cause": "the shiny hoop reflected a bright flash into its eyes",
        "clue": "the frightened gazelle blinked whenever the hoop turned",
        "kind_action": "covered the hoop with cloth and let the gazelle choose a quiet starting place",
        "result": "the gazelle trotted into the circle and made a graceful turn",
        "ending": "the friends dined by the hoop, which now rested softly under the moon",
        "worry": "That flashing circle feels like a storm.",
        "reply": "Thank you for telling me. We can soften it and begin where you feel safe.",
        "lesson": "listening was a kind way to help",
    },
    {
        "trouble": "the gazelle missed the soft landing blanket",
        "cause": "the blanket had blown behind a clump of reeds",
        "clue": "one corner of blue cloth fluttered beyond the reeds",
        "kind_action": "found the blanket and held its corners while the gazelle tried a small leap",
        "result": "the gazelle landed safely and then chose a slightly higher mark",
        "ending": "they dined on melon slices beside the blanket as evening birds sang",
        "worry": "I thought the safe blanket had vanished.",
        "reply": "It was hiding, not gone. We found it, and I will hold it steady.",
        "lesson": "helping patiently gave fear less room",
    },
    {
        "trouble": "the gazelle became quiet when the other animals gathered to watch",
        "cause": "the crowd's excited hooves sounded louder than anyone expected",
        "clue": "the gazelle relaxed when the animals stepped back",
        "kind_action": "asked everyone to make a wide, quiet ring and praised every small try",
        "result": "the gazelle performed a lovely stretch for the gentle audience",
        "ending": "the whole group dined together and spoke in calm, happy voices",
        "worry": "There are too many eyes on me.",
        "reply": "We can give you space. Your first small stretch is already brave.",
        "lesson": "kindness can make a crowd feel like a family",
    },
    {
        "trouble": "the gazelle's ribbon tangled around a practice bar",
        "cause": "the ribbon was longer than the gymnast had noticed",
        "clue": "a red thread looped around the bar's wooden peg",
        "kind_action": "untied the ribbon and replaced it with a shorter one",
        "result": "the gazelle twirled without a tangle and bowed proudly",
        "ending": "they dined on carrot stew while the short ribbon waved from a nearby branch",
        "worry": "The ribbon is holding me back!",
        "reply": "We will not pull. We will loosen the knot gently together.",
        "lesson": "careful hands showed caring hearts",
    },
]


@dataclass
class StoryParams:
    gymnast: str
    gazelle: str
    meal: str
    place: str
    seed: Optional[int] = None


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

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Animal story about a gymnast, a gazelle, dinner, and kindness.")
    parser.add_argument("--gymnast", choices=GYMNASTS)
    parser.add_argument("--gazelle", choices=GAZELLES)
    parser.add_argument("--meal", choices=MEALS)
    parser.add_argument("--place", choices=PLACES)
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
    gymnast = args.gymnast or rng.choice(GYMNASTS)
    gazelle = args.gazelle or rng.choice(GAZELLES)
    meal = args.meal or rng.choice(MEALS)
    place = args.place or rng.choice(PLACES)
    if gymnast == gazelle:
        raise StoryError("The gymnast and gazelle need different names.")
    return StoryParams(gymnast=gymnast, gazelle=gazelle, meal=meal, place=place)


def build_world(params: StoryParams) -> World:
    world = World(params)
    world.add(
        Entity(
            id="gymnast",
            kind="character",
            label=params.gymnast,
            type="child_gymnast",
            meters={"balance": 0.7},
            memes={"patience": 0.5, "kindness": 1.0},
        )
    )
    world.add(
        Entity(
            id="gazelle",
            kind="animal",
            label=params.gazelle,
            type="gazelle",
            meters={"speed": 0.8, "balance": 0.4},
            memes={"worry": 0.4, "trust": 0.3},
        )
    )
    world.add(
        Entity(
            id="dinner",
            kind="thing",
            label=params.meal,
            type="shared_food",
            meters={"warmth": 0.8},
            memes={"welcome": 1.0},
        )
    )
    return world


def story_variation(params: StoryParams) -> int:
    seed = params.seed
    if seed is None:
        seed = sum((i + 1) * ord(c) for i, c in enumerate("|".join(vars(params).values() if False else [
            params.gymnast, params.gazelle, params.meal, params.place
        ])))
    return (seed * 131 + 17) % len(ARCS)


def generate_story(world: World) -> None:
    p = world.params
    gymnast = world.entities["gymnast"]
    gazelle = world.entities["gazelle"]
    arc = ARCS[story_variation(p)]

    world.say(
        f"In {p.place}, {p.gymnast} practiced gentle gymnastics beside a patch of sweet grass. "
        f"{p.gazelle}, a quick young gazelle, came to watch."
    )
    world.say(
        f"After practice, the friends planned to dine on {p.meal}. "
        f"First, {p.gymnast} invited {p.gazelle} to try a small animal-friendly routine."
    )

    world.para()
    world.say(f"But {arc['trouble']}.")
    world.say(f"{p.gymnast} asked, “{arc['worry']}”")
    world.say(f"{p.gazelle} answered, “I want to try, but I feel afraid.”")
    world.say(f"{p.gymnast} spoke gently. “{arc['reply']}”")
    world.facts["trouble"] = arc["trouble"]
    world.facts["worry"] = arc["worry"]
    world.facts["dialogue"] = True
    gymnast.memes["kindness"] = 2.0
    gazelle.memes["worry"] = 1.0

    world.para()
    world.say(f"Instead of guessing, {p.gymnast} looked carefully and noticed that {arc['clue']}.")
    world.say(f"The real cause was that {arc['cause']}.")
    world.say(f"With patient care, {p.gymnast} {arc['kind_action']}.")
    world.say(f"Then {arc['result']}.")
    world.say(
        f"{p.gymnast} clapped softly, and {p.gazelle} smiled. "
        f"“You stayed with me,” said {p.gazelle}. “That made me brave.”"
    )
    world.say(
        f"{p.gymnast} replied, “Friends do not need to be perfect. Friends can help one another begin.”"
    )

    gymnast.memes["pride"] = 1.0
    gymnast.memes["kindness"] = 3.0
    gazelle.memes["worry"] = 0.0
    gazelle.memes["trust"] = 1.0
    gazelle.meters["balance"] = 0.9
    world.facts.update(
        {
            "cause": arc["cause"],
            "clue": arc["clue"],
            "kind_action": arc["kind_action"],
            "result": arc["result"],
            "lesson": arc["lesson"],
            "ending": arc["ending"],
            "settled": True,
        }
    )

    world.para()
    world.say(
        f"At last, {p.gymnast} and {p.gazelle} sat together to dine on {p.meal}. "
        f"{arc['ending']}."
    )
    world.say(
        f"The gymnast had learned that {arc['lesson']}, and the gazelle had learned that asking for help was brave."
    )


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write an Animal Story about gymnast {p.gymnast} and gazelle {p.gazelle} in {p.place}. Include Dialogue, Kindness, and a shared {p.meal} dinner.",
        f"Tell a gentle story in which a gymnast helps a gazelle solve a frightening gymnastics problem through patient kindness.",
        "Create a child-friendly animal story with spoken back-and-forth dialogue, a clear problem, a caring solution, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"Why did {p.gazelle} become worried during gymnastics in {p.place}?",
            answer=f"{p.gazelle} became worried because {f['trouble']}. The real cause was that {f['cause']}.",
        ),
        QAItem(
            question=f"How did {p.gymnast} show kindness to {p.gazelle}?",
            answer=f"{p.gymnast} noticed that {f['clue']} and then {f['kind_action']}. This gave the gazelle time and safety to try again.",
        ),
        QAItem(
            question=f"What did the dialogue change for {p.gazelle}?",
            answer=f"When {p.gazelle} said it felt afraid, {p.gymnast} promised to help instead of rushing it. The kind words helped the gazelle trust its friend and continue.",
        ),
        QAItem(
            question=f"What happened when {p.gymnast} and {p.gazelle} finished their practice?",
            answer=f"{f['result']}. Then they dined on {p.meal} together, and the gazelle felt proud and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gymnast?",
            answer="A gymnast is someone who practices movements such as balancing, stretching, jumping, and turning.",
        ),
        QAItem(
            question="What is a gazelle?",
            answer="A gazelle is a graceful grassland animal known for running quickly and leaping lightly.",
        ),
        QAItem(
            question="Why is kindness useful when someone is afraid?",
            answer="Kindness can make a frightened person or animal feel safe, understood, and ready to try again at a comfortable pace.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.kind:10}) {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


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


def asp_facts() -> str:
    import asp

    lines = []
    for gymnast in GYMNASTS:
        lines.append(asp.fact("gymnast", gymnast))
    for gazelle in GAZELLES:
        lines.append(asp.fact("gazelle", gazelle))
    for meal in MEALS:
        lines.append(asp.fact("meal", meal))
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.extend(
        [
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "kindness"),
            asp.fact("style", "animal_story"),
        ]
    )
    return "\n".join(lines)


ASP_RULES = r"""
animal_story(G, Z, M, P) :-
    gymnast(G), gazelle(Z), meal(M), place(P),
    G != Z.
dialogue(G, Z) :-
    gymnast(G), gazelle(Z), feature(dialogue).
kindness(G, Z) :-
    gymnast(G), gazelle(Z), feature(kindness).
complete_story(G, Z, M, P) :-
    animal_story(G, Z, M, P),
    dialogue(G, Z),
    kindness(G, Z).
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(
        asp_program(
            "#show animal_story/4.\n"
            "#show dialogue/2.\n"
            "#show kindness/2.\n"
            "#show complete_story/4."
        )
    )
    animal = set(asp.atoms(model, "animal_story"))
    dialogue = set(asp.atoms(model, "dialogue"))
    kindness = set(asp.atoms(model, "kindness"))
    complete = set(asp.atoms(model, "complete_story"))
    expected_animal = {
        (g, z, m, p)
        for g in GYMNASTS
        for z in GAZELLES
        if g != z
        for m in MEALS
        for p in PLACES
    }
    expected_pair = {(g, z) for g in GYMNASTS for z in GAZELLES if g != z}
    ok = animal == expected_animal and dialogue == expected_pair and kindness == expected_pair
    ok = ok and complete == expected_animal
    if not ok:
        print("Mismatch between ASP and Python registries.")
        return 1
    for params in [
        StoryParams(GYMNASTS[0], GAZELLES[0], MEALS[0], PLACES[0], seed=11),
        StoryParams(GYMNASTS[1], GAZELLES[1], MEALS[1], PLACES[1], seed=23),
    ]:
        sample = generate(params)
        if not sample.story or len(sample.story_qa) < 3:
            print("Generated story exercise failed.")
            return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


CURATED = [
    StoryParams("Lina", "Gigi", "carrot stew", "the sunlit meadow", 101),
    StoryParams("Mara", "Zara", "berry porridge", "the acacia grove", 202),
    StoryParams("Toby", "Fara", "melon soup", "the riverside clearing", 303),
    StoryParams("Nia", "Kito", "warm grass cakes", "the red-dust field", 404),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show animal_story/4.\n#show dialogue/2.\n#show kindness/2.\n#show complete_story/4."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            raise SystemExit(1)
        model = asp.one_model(
            asp_program("#show animal_story/4.\n#show dialogue/2.\n#show kindness/2.\n#show complete_story/4.")
        )
        print(f"animal_story={len(asp.atoms(model, 'animal_story'))}")
        print(f"dialogue={len(asp.atoms(model, 'dialogue'))}")
        print(f"kindness={len(asp.atoms(model, 'kindness'))}")
        print(f"complete_story={len(asp.atoms(model, 'complete_story'))}")
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            seed = base_seed + attempt
            attempt += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if args.all:
            header = f"### {sample.params.gymnast} and {sample.params.gazelle}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
