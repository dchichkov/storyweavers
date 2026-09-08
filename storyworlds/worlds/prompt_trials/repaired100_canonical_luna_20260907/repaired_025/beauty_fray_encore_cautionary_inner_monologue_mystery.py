#!/usr/bin/env python3
"""
A small fairy-tale storyworld about beauty, a frayed song, and an encore
that can only be earned by listening carefully.
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
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    frayed: bool = False
    hidden: bool = False


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Tale:
    id: str
    opening: str
    mystery: str
    clue: str
    warning: str
    reveal: str
    repair: str
    ending: str


@dataclass
class StoryParams:
    name: str
    creature: str
    flower: str
    tale: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTING = Setting(
    place="the Moonlit Glass Garden",
    affords={"beauty", "music", "mystery", "caution", "encore"},
)

TALES = {
    "silver_lily": Tale(
        id="silver_lily",
        opening="Once, in the Moonlit Glass Garden, the flowers shone brighter than little stars.",
        mystery="Yet the silver lily's song broke apart just before the royal encore.",
        clue="A thread of blue moon-silk trembled beneath the lily's bell, though no wind touched it.",
        warning="The old gardener warned that beauty can hide a danger when everyone stares only at its shine.",
        reveal="Behind the lily stood a tiny thorn-door, and the moon-silk had caught on its sharp latch.",
        repair="Luna covered the thorn with a folded leaf, then gently freed the silk instead of pulling it.",
        ending="When the encore began, the silver lily sang one clear note, and every flower answered.",
    ),
    "rose_clock": Tale(
        id="rose_clock",
        opening="At midnight, the rose clock opened its velvet petals for the garden's grand song.",
        mystery="But its beautiful chime frayed into three frightened squeaks.",
        clue="Luna noticed a single gold petal pointing toward the clock's shadow.",
        warning="The queen whispered that lovely things may still need careful mending.",
        reveal="A spider had woven a shining web through the clock's hidden spring.",
        repair="Luna asked the spider to loosen the web, and she shielded its little nest from the falling dew.",
        ending="The rose clock chimed an encore so warm that even the spider tapped its feet.",
    ),
    "opal_bell": Tale(
        id="opal_bell",
        opening="Beyond the palace path hung an opal bell, famous for making dawn sound beautiful.",
        mystery="On festival morning, its ribbon began to fray and the bell forgot its tune.",
        clue="A pale feather lay beside the ribbon, marked with a tiny drop of honey.",
        warning="Luna remembered that a rushed repair can turn a small fray into a great tear.",
        reveal="A sleepy bee had tied the feather into the ribbon while carrying pollen home.",
        repair="Luna waited for the bee to wake, then tied the ribbon around a smooth branch instead.",
        ending="At sunrise, the opal bell rang its encore, and the bee danced in the golden sound.",
    ),
}


NAMES = ["Luna", "Mira", "Nella", "Suri", "Elia"]
CREATURES = ["princess", "fox", "mouse", "fairy", "fawn"]
FLOWERS = ["silver lily", "rose", "moon orchid", "glass tulip"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A fairy-tale world of beauty, fray, mystery, caution, and encore."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--creature", choices=CREATURES)
    parser.add_argument("--flower", choices=FLOWERS)
    parser.add_argument("--tale", choices=sorted(TALES))
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
    name = args.name or rng.choice(NAMES)
    creature = args.creature or rng.choice(CREATURES)
    flower = args.flower or rng.choice(FLOWERS)
    tale = args.tale or rng.choice(sorted(TALES))
    return StoryParams(name=name, creature=creature, flower=flower, tale=tale)


def tell(params: StoryParams) -> World:
    tale = TALES[params.tale]
    world = World(SETTING)
    hero = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.creature,
            label=params.name,
            meters={"care": 0.0, "listening": 0.0},
            memes={"wonder": 1.0, "caution": 0.0, "confidence": 0.0},
        )
    )
    flower = world.add(
        Entity(
            id="garden_song",
            kind="thing",
            type="flower",
            label=params.flower,
            meters={"beauty": 1.0, "music": 1.0},
            memes={"hope": 1.0},
            frayed=True,
        )
    )
    silk = world.add(
        Entity(
            id="moon_silk",
            kind="thing",
            type="ribbon",
            label="blue moon-silk",
            meters={"strength": 0.3},
            frayed=True,
            hidden=True,
        )
    )
    world.facts.update(hero=hero, flower=flower, silk=silk, tale=tale, params=params)

    world.say(tale.opening)
    world.say(
        f"{params.name}, a {params.creature}, had been chosen to announce the encore "
        f"because {params.name.lower()} could hear small sounds beneath great beauty."
    )
    world.para()

    world.say(tale.mystery)
    world.say(f'The flower whispered, "I am beautiful, but I cannot sing."')
    world.say(f'"Do not fear," said {params.name}. "I will listen before I touch anything."')
    world.say(tale.warning)
    world.say(f"{params.name} followed the quiet clue: {tale.clue}")
    world.say(
        f"Inside {params.name}'s thoughts came a careful question: "
        f'"Is the song broken, or is something holding it back?"'
    )
    world.say(f'"There is a secret here," {params.name} murmured. "We must solve it gently."')
    world.para()

    world.say(tale.reveal)
    world.say(tale.repair)
    hero.meters["care"] = 1.0
    hero.meters["listening"] = 1.0
    hero.memes["caution"] = 1.0
    hero.memes["confidence"] = 1.0
    flower.frayed = False
    flower.meters["music"] = 2.0
    silk.frayed = False
    silk.hidden = False
    silk.meters["strength"] = 1.0
    world.fired.update({"mystery_solved", "fray_repaired", "caution_learned"})
    world.say(
        f"The fray rested safely, and {params.name} learned that caution did not make beauty smaller; "
        "it helped beauty last."
    )
    world.para()
    world.say(tale.ending)
    world.say(
        f"{params.name} bowed, not because {params.name.lower()} had made the garden beautiful, "
        "but because {params.name.lower()} had cared for what was already there."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    tale = world.facts["tale"]
    hero = world.facts["hero"]
    return [
        f"Write a Fairy Tale about {hero.id} solving this mystery: {tale.mystery}",
        f"Tell a cautionary story in which beauty, a fray, and an encore are connected by careful listening.",
        f"Use an inner monologue to show why {hero.id} repairs the danger gently.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tale: Tale = world.facts["tale"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    return [
        QAItem(
            question="What mystery needed to be solved?",
            answer=tale.mystery,
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=tale.clue,
        ),
        QAItem(
            question="What cautionary warning did the story give?",
            answer=tale.warning,
        ),
        QAItem(
            question=f"How did {hero.id} repair the fray?",
            answer=tale.repair,
        ),
        QAItem(
            question="What changed after the repair?",
            answer=tale.ending,
        ),
        QAItem(
            question=f"What did {hero.id} learn?",
            answer=(
                f"{hero.id} learned that caution does not make beauty smaller; "
                "it helps beauty last."
            ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is beauty?",
            answer="Beauty is a quality that makes something pleasing or wonderful to notice.",
        ),
        QAItem(
            question="What is a fray?",
            answer="A fray is a place where threads or edges become loose and worn.",
        ),
        QAItem(
            question="What is an encore?",
            answer="An encore is an extra performance given after people ask for more.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means moving carefully so that a small danger does not become a larger one.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private stream of thoughts.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes} "
            f"frayed={entity.frayed} hidden={entity.hidden}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return params.tale in TALES and params.name in NAMES and params.creature in CREATURES


ASP_RULES = r"""
valid_story(N,C,T) :- name(N), creature(C), tale(T), cautious_tale(T).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for name in NAMES:
        lines.append(asp.fact("name", name))
    for creature in CREATURES:
        lines.append(asp.fact("creature", creature))
    for tale in TALES:
        lines.append(asp.fact("tale", tale))
        lines.append(asp.fact("cautious_tale", tale))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = {
        (name, creature, tale)
        for name in NAMES
        for creature in CREATURES
        for tale in TALES
        if valid_story(StoryParams(name, creature, FLOWERS[0], tale))
    }
    if actual == expected:
        print(f"OK: clingo gate matches python gate ({len(expected)} combinations).")
        for tale in TALES:
            sample = generate(
                StoryParams("Luna", "fairy", "silver lily", tale, seed=0)
            )
            if "encore" not in sample.story.lower():
                return 1
        print("OK: generated stories exercise the encore resolution.")
        return 0
    print("MISMATCH between clingo and Python.")
    print("Only in clingo:", sorted(actual - expected))
    print("Only in Python:", sorted(expected - actual))
    return 1


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError(
            "This fairy-tale world requires a known name, creature, and cautious tale."
        )
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
    StoryParams("Luna", "fairy", "silver lily", "silver_lily", 0),
    StoryParams("Mira", "fox", "rose", "rose_clock", 1),
    StoryParams("Nella", "fawn", "glass tulip", "opal_bell", 2),
]


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    seen = set()
    index = 0
    while len(samples) < args.n:
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        index += 1
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid story combinations.")
        for atom in atoms[:20]:
            print(atom)
        return

    samples = [generate(p) for p in CURATED] if args.all else build_story_from_args(args)

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
