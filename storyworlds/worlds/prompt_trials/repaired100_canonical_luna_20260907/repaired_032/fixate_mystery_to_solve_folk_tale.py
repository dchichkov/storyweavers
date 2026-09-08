#!/usr/bin/env python3
"""
A small folk-tale storyworld about Luna, who fixates on a mystery and learns
that patient questions, careful observation, and a friend's help reveal the
answer.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    feature: str


@dataclass(frozen=True)
class Mystery:
    id: str
    object_label: str
    clue: str
    false_lead: str
    reveal: str
    answer: str
    ending: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    helper: str
    seed: Optional[int] = None
    telling: str = "hearth"


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


PLACES = {
    "hill_village": Place(
        "hill_village",
        "the hill village",
        "a bell tower whose door had been locked for seven years",
    ),
    "willow_ford": Place(
        "willow_ford",
        "Willow Ford",
        "a river ford where silver ripples hid old stepping stones",
    ),
    "pine_market": Place(
        "pine_market",
        "Pine Market",
        "a market square where every stall had a different colored awning",
    ),
    "moon_meadow": Place(
        "moon_meadow",
        "Moon Meadow",
        "a meadow where a circle of pale stones stood beneath an ancient oak",
    ),
}

MYSTERIES = {
    "silent_bell": Mystery(
        "silent_bell",
        "the brass bell",
        "three pale feathers lay beneath the tower window",
        "the old keeper's key had vanished from its hook",
        "Luna noticed a thin cord running from the bell rope through a crack in the wall",
        "a swallow had woven the cord into her nest, pulling the bell rope tight whenever the wind rose",
        "When Luna loosened the cord without harming the nest, the bell rang, and the village heard its bright voice again.",
    ),
    "blue_lantern": Mystery(
        "blue_lantern",
        "the missing blue lantern",
        "a blue drop of wax marked the path behind the baker's shed",
        "a fox-shaped shadow crossed the empty lantern hook",
        "Luna found tiny paw prints ending beside a hollow log",
        "the baker's puppy had carried the lantern's blue handle to its secret sleeping place",
        "The puppy returned the lantern, and its blue light guided everyone safely home.",
    ),
    "singing_stone": Mystery(
        "singing_stone",
        "the stone that sang",
        "a ring of dry moss circled one stone beside the ford",
        "the miller's child claimed a goblin lived beneath it",
        "Luna heard water whispering through a narrow crack under the stone",
        "the river wind passed through the crack and made the stone hum",
        "The villagers left the stone in place, and travelers used its gentle song to find the ford in fog.",
    ),
    "vanished_crown": Mystery(
        "vanished_crown",
        "the mayor's wooden crown",
        "yellow sawdust glittered beneath the market table",
        "a crow carried something bright toward the pine trees",
        "Luna saw fresh carving marks on a low stool near the carpenter's stall",
        "the carpenter had hidden the crown while repairing its cracked band",
        "The crown returned stronger than before, and the mayor wore it at the harvest dance.",
    ),
    "moon_tracks": Mystery(
        "moon_tracks",
        "the footprints around the oak",
        "the tracks appeared only inside the ring of pale stones",
        "the shepherd said a moon giant walked there at night",
        "Luna compared the tracks with the shape of the oak's fallen leaves",
        "an owl had hopped in circles while hunting moths under the moon",
        "The villagers watched the owl that evening and called its careful hunt a moon dance.",
    ),
}

NAMES = ["Luna", "Toma", "Pella", "Neri", "Odo", "Mira", "Sela", "Bran"]
HELPERS = ["Toma", "Pella", "Neri", "Odo", "Mira", "Sela", "Bran", "Fenn"]

TELLINGS = {
    "hearth": {
        "opening": "Long ago, when the village fires burned low, {hero} noticed {mystery}.",
        "invite": "\"A mystery grows no smaller when we stare at it,\" said {hero}. \"Come, {helper}; let us ask what the clues say.\"",
        "lesson": "So {hero} stopped fixating on the first frightening guess and began to follow the small facts.",
    },
    "road": {
        "opening": "Once, on a road where travelers traded riddles for bread, {hero} came upon {mystery}.",
        "invite": "{hero} fixated on the strange sight until {helper} touched {hero}'s sleeve. \"Look twice,\" said {helper}. \"A clue may be quieter than a rumor.\"",
        "lesson": "Together they traded guessing for noticing, and each new detail shortened the road to the truth.",
    },
    "village": {
        "opening": "In a village of red roofs and patient wells, {hero} found {mystery}.",
        "invite": "\"I cannot think of anything else,\" {hero} confessed. {helper} replied, \"Then lend your eyes to the clues, not to your worry.\"",
        "lesson": "The two friends examined the scene piece by piece, until the mystery became a question they could answer.",
    },
    "tale": {
        "opening": "The old tale says that {hero} once met {mystery} beneath a sky full of geese.",
        "invite": "\"Perhaps a giant did it!\" cried {hero}. \"Perhaps,\" said {helper}, \"but let us first ask the ground, the walls, and the wind.\"",
        "lesson": "Their careful search proved that a bold rumor may be loud, while a true clue may whisper.",
    },
}


ASP_RULES = r"""
place(P) :- place_name(P).
mystery(M) :- mystery_name(M).
compatible(P, M) :- place(P), mystery(M), placed_mystery(P, M).
solvable(P, M) :- compatible(P, M), has_clue(M), has_reveal(M), has_answer(M).
#show solvable/2.
"""


def valid_combos() -> list[tuple[str, str]]:
    return sorted(
        (place_id, mystery_id)
        for place_id in PLACES
        for mystery_id in MYSTERIES
    )


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place_name", place_id))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery_name", mystery_id))
        lines.append(asp.fact("placed_mystery", "hill_village", mystery_id))
        lines.append(asp.fact("has_clue", mystery_id))
        lines.append(asp.fact("has_reveal", mystery_id))
        lines.append(asp.fact("has_answer", mystery_id))
    for place_id in PLACES:
        for mystery_id in MYSTERIES:
            lines.append(asp.fact("placed_mystery", place_id, mystery_id))
    return "\n".join(lines)


def asp_program(show: str = "#show solvable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> set[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "solvable"))


def asp_verify() -> int:
    try:
        import asp
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    py = set(valid_combos())
    clingo_combos = asp_valid_combos()
    if py == clingo_combos:
        print(f"OK: clingo gate matches Python validity ({len(py)} combinations).")
        for params in curated_params():
            sample = generate(params)
            if not sample.story or "fixat" not in sample.story.lower():
                print("Generated-story exercise failed.")
                return 1
        print("OK: generated stories exercised.")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo_combos - py))
    print("  only in Python:", sorted(py - clingo_combos))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Folk-tale mystery storyworld about Luna and careful clues."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--mystery", choices=sorted(MYSTERIES))
    parser.add_argument("--name")
    parser.add_argument("--helper")
    parser.add_argument("--telling", choices=sorted(TELLINGS))
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
    choices = [
        combo
        for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.mystery is None or combo[1] == args.mystery
    ]
    if not choices:
        raise StoryError("No place and mystery combination matches the requested options.")
    place, mystery = rng.choice(choices)
    name = args.name or rng.choice(NAMES)
    helper_choices = [item for item in HELPERS if item != name]
    helper = args.helper or rng.choice(helper_choices)
    if helper == name:
        raise StoryError("The helper must have a different name from the seeker.")
    return StoryParams(
        place=place,
        mystery=mystery,
        name=name,
        helper=helper,
        telling=args.telling or rng.choice(sorted(TELLINGS)),
    )


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    telling = TELLINGS[params.telling]
    world = World(place)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.name,
            memes={"curiosity": 1.0, "fixation": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper,
            memes={"patience": 1.0, "care": 1.0},
        )
    )
    object_entity = world.add(
        Entity(
            id="mystery_object",
            kind="mystery",
            label=mystery.object_label,
            meters={"hidden_answer": 1.0},
        )
    )

    opening = telling["opening"].format(hero=hero.label, mystery=mystery.object_label)
    invite = telling["invite"].format(hero=hero.label, helper=helper.label)
    lesson = telling["lesson"].format(hero=hero.label)

    world.facts.update(
        hero=hero,
        helper=helper,
        mystery=mystery,
        opening=opening,
        invite=invite,
        lesson=lesson,
        place=place,
        clue_seen=False,
        false_lead_seen=False,
        answer_found=False,
        solved=False,
    )

    world.say(opening)
    world.say(
        f"It had become the village's Mystery to Solve, and {hero.label} fixated on it "
        "until every ordinary sound seemed to whisper a warning."
    )
    world.say(invite)
    world.para()
    world.say(
        f"First they followed a false lead: {mystery.false_lead}. "
        "But the path ended in silence."
    )
    world.facts["false_lead_seen"] = True
    world.fired.add("false_lead")

    world.say(
        f"Then {helper.label} pointed to a quieter sign: {mystery.clue}. "
        f"{hero.label} wrote the clue in the dust instead of chasing another rumor."
    )
    world.facts["clue_seen"] = True
    world.fired.add("clue_found")
    hero.memes["fixation"] = 0.5
    hero.memes["attention"] = 1.0

    world.say(
        f"\"What does that tell us?\" asked {hero.label}. "
        f"\"It tells us where to look next,\" said {helper.label}. "
        f"\"And what should we do?\" asked {hero.label}. "
        f"\"Move gently, and let the answer prove itself,\" said {helper.label}."
    )
    world.fired.add("dialogue")

    world.say(mystery.reveal)
    world.facts["answer_found"] = True
    world.fired.add("reveal")
    hero.memes["understanding"] = 1.0
    hero.meters["mystery_solved"] = 1.0

    world.para()
    world.say(lesson)
    world.say(mystery.ending)
    world.say(
        f"From that day on, {hero.label} still loved a mystery, but never fixated on a guess "
        "when a patient question could open the door to truth."
    )
    world.facts["solved"] = True
    world.fired.add("resolution")
    return world


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    return [
        "Write a child-facing folk tale about a mystery to solve.",
        f"Show how {hero.label} fixates on a mystery, then lets {helper.label} help follow a concrete clue.",
        f"Use this clue and reveal causally: {mystery.clue} Then explain that {mystery.answer}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    place: Place = world.facts["place"]
    return [
        QAItem(
            question=f"What mystery did {hero.label} try to solve?",
            answer=f"{hero.label} tried to solve the mystery of {mystery.object_label} in {place.label}.",
        ),
        QAItem(
            question=f"Why did {hero.label} need help?",
            answer=f"{hero.label} fixated on a frightening guess, so {helper.label} helped by slowing down and noticing a quieter clue.",
        ),
        QAItem(
            question="What was the important clue?",
            answer=f"The important clue was that {mystery.clue}. It pointed the friends toward the real answer.",
        ),
        QAItem(
            question="What false lead did they investigate?",
            answer=f"They first investigated this false lead: {mystery.false_lead}, but it did not explain the mystery.",
        ),
        QAItem(
            question="What was the answer to the mystery?",
            answer=f"The answer was that {mystery.answer}.",
        ),
        QAItem(
            question="What did the seeker learn?",
            answer=f"The seeker learned to enjoy mysteries without fixating on a guess and to let careful questions and evidence guide the search.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people do not understand yet and may investigate.",
        ),
        QAItem(
            question="What does it mean to fixate?",
            answer="To fixate means to focus on one thought so strongly that it becomes hard to notice other possibilities.",
        ),
        QAItem(
            question="Why are clues useful?",
            answer="Clues are useful because they provide evidence that can guide a search toward a reasonable answer.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a traditional-style story with memorable characters, a clear problem, and a lesson or change.",
        ),
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
    lines = ["--- world model state ---", f"  place: {world.place.label}"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}, "
            f"meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  facts: solved={world.facts.get('solved')}, "
                 f"clue_seen={world.facts.get('clue_seen')}, "
                 f"answer_found={world.facts.get('answer_found')}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def curated_params() -> list[StoryParams]:
    return [
        StoryParams(
            place="hill_village",
            mystery="silent_bell",
            name="Luna",
            helper="Toma",
            telling="hearth",
        ),
        StoryParams(
            place="willow_ford",
            mystery="singing_stone",
            name="Pella",
            helper="Neri",
            telling="road",
        ),
        StoryParams(
            place="pine_market",
            mystery="vanished_crown",
            name="Mira",
            helper="Odo",
            telling="village",
        ),
        StoryParams(
            place="moon_meadow",
            mystery="moon_tracks",
            name="Sela",
            helper="Bran",
            telling="tale",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            combinations = sorted(asp_valid_combos())
        except ImportError as exc:
            print(f"ASP mode unavailable: {exc}")
            sys.exit(1)
        print(f"{len(combinations)} solvable combinations:")
        for combination in combinations:
            print(" ", combination)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in curated_params()]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            attempts += 1
            rng = random.Random(base_seed + attempts)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
                return
            params.seed = base_seed + attempts
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
