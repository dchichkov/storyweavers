#!/usr/bin/env python3
"""Gingham Magic Nursery Rhyme.

A compact, executable storyworld about a gingham ribbon, a little magic,
and a nursery rhyme that changes when someone learns to listen.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import random
import sys
from typing import Any

for parent in Path(__file__).resolve().parents:
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


PROBLEMS = ("moon_stuck", "bell_silent", "rainbow_faded", "seed_sleeping")
SOLUTIONS = ("ribbon_bridge", "ribbon_song")
MAGICS = ("sparkle", "whisper", "glow")
VOICES = ("bouncy", "gentle", "plain")
HEROES = ("Nell", "Mina", "Pip", "Tess")
ANIMALS = ("mouse", "robin", "lamb", "kitten")
PLACES = ("garden gate", "cottage lane", "old well", "apple yard")


@dataclass
class StoryParams:
    hero: str = "Nell"
    animal: str = "mouse"
    place: str = "garden gate"
    problem: str = "moon_stuck"
    solution: str = "ribbon_bridge"
    magic: str = "sparkle"
    voice: str = "bouncy"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: str = ""


@dataclass
class Event:
    id: int
    kind: str
    actor: str
    facts: tuple[str, ...]
    data: dict[str, Any]
    state: dict[str, Any]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity]
    history: list[Event] = field(default_factory=list)
    facts: set[str] = field(default_factory=set)
    outcome: str = ""

    def snapshot(self) -> dict[str, Any]:
        return {
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "facts": sorted(self.facts),
            "outcome": self.outcome,
        }

    def record(self, kind: str, actor: str, facts: tuple[str, ...] = (), **data: Any) -> None:
        event = Event(
            id=len(self.history),
            kind=kind,
            actor=actor,
            facts=facts,
            data=data,
            state=self.snapshot(),
        )
        self.history.append(event)
        self.facts.update(facts)


PATHS = {
    ("moon_stuck", "ribbon_bridge"): {
        "clue": "The moon is caught on a thorn above the gate.",
        "actions": ("notice", "speak", "tie", "lift"),
        "changes": ("thorn_seen", "plan_known", "bridge_tied", "moon_free"),
        "ending": "The moon rides high, and the gingham bridge sways below.",
    },
    ("moon_stuck", "ribbon_song"): {
        "clue": "The moon is caught because it is waiting for a song.",
        "actions": ("notice", "speak", "sing", "release"),
        "changes": ("thorn_seen", "plan_known", "song_sung", "moon_free"),
        "ending": "The moon hums home, leaving silver on the gingham bow.",
    },
    ("bell_silent", "ribbon_bridge"): {
        "clue": "The bell's clapper hangs beyond a puddle.",
        "actions": ("notice", "speak", "tie", "pull"),
        "changes": ("clapper_seen", "plan_known", "bridge_tied", "bell_rings"),
        "ending": "The bell rings bright above the gingham bridge.",
    },
    ("bell_silent", "ribbon_song"): {
        "clue": "The bell is quiet because it has forgotten its tune.",
        "actions": ("notice", "speak", "sing", "ring"),
        "changes": ("clapper_seen", "plan_known", "song_sung", "bell_rings"),
        "ending": "The bell remembers, and its song skips over gingham.",
    },
    ("rainbow_faded", "ribbon_bridge"): {
        "clue": "A gray cloud hides the rainbow's far end.",
        "actions": ("notice", "speak", "tie", "stretch"),
        "changes": ("cloud_seen", "plan_known", "bridge_tied", "colors_return"),
        "ending": "Red, gold, and blue return above the gingham bridge.",
    },
    ("rainbow_faded", "ribbon_song"): {
        "clue": "The rainbow's colors are sleeping under a hush.",
        "actions": ("notice", "speak", "sing", "brighten"),
        "changes": ("cloud_seen", "plan_known", "song_sung", "colors_return"),
        "ending": "The rainbow wakes to the song and paints the gingham bow.",
    },
    ("seed_sleeping", "ribbon_bridge"): {
        "clue": "A seed cannot cross the dry crack in the soil.",
        "actions": ("notice", "speak", "tie", "carry"),
        "changes": ("crack_seen", "plan_known", "bridge_tied", "seed_planted"),
        "ending": "The seed crosses safely, beneath a gingham flag.",
    },
    ("seed_sleeping", "ribbon_song"): {
        "clue": "A seed sleeps until it hears its morning rhyme.",
        "actions": ("notice", "speak", "sing", "sprout"),
        "changes": ("crack_seen", "plan_known", "song_sung", "seed_planted"),
        "ending": "A green sprout sings beside the gingham bow.",
    },
}


PROBLEM_TEXT = {
    "moon_stuck": "a little moon snagged above the gate",
    "bell_silent": "a blue bell that would not ring",
    "rainbow_faded": "a rainbow pale as old chalk",
    "seed_sleeping": "a sleepy seed beside a dry crack",
}


def validate_params(p: StoryParams) -> None:
    for value, choices, label in (
        (p.problem, PROBLEMS, "problem"),
        (p.solution, SOLUTIONS, "solution"),
        (p.magic, MAGICS, "magic"),
        (p.voice, VOICES, "voice"),
        (p.animal, ANIMALS, "animal"),
        (p.place, PLACES, "place"),
    ):
        if value not in choices:
            raise StoryError(f"Unknown {label}: {value!r}.")
    if not p.hero or not p.hero[0].isupper():
        raise StoryError("The hero name must begin with a capital letter.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")
    if (p.problem, p.solution) not in PATHS:
        raise StoryError("That magic solution does not fit this problem.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    entities = {
        "hero": Entity("hero", p.hero, "character", p.place, memes={"curiosity": 1}),
        "animal": Entity("animal", f"the {p.animal}", "helper", p.place, memes={"hope": 1}),
        "ribbon": Entity("ribbon", "the gingham ribbon", "magic", "pocket",
                         meters={"length": 5, "softness": 1}, memes={"magic": 1}),
        "problem": Entity("problem", PROBLEM_TEXT[p.problem], "trouble", p.place,
                          meters={"difficulty": 2}, memes={"loneliness": 1}),
    }
    w = World(p, entities)
    w.record("opening", "hero", ("trouble_present",), trouble=PROBLEM_TEXT[p.problem])
    return w


def execute(w: World, kind: str) -> None:
    p = w.params
    path = PATHS[(p.problem, p.solution)]
    if len(w.history) - 1 >= len(path["actions"]):
        raise StoryError("The path has already finished.")
    expected = path["actions"][len(w.history) - 1]
    if kind != expected:
        raise StoryError(f"The next needed action is {expected}, not {kind}.")
    if kind == "notice":
        w.record("notice", "hero", (path["changes"][0],), clue=path["clue"])
    elif kind == "speak":
        w.record("speak", "animal", (path["changes"][1],), clue=path["clue"])
    elif kind == "tie":
        ribbon = w.entities["ribbon"]
        ribbon.location = "between"
        ribbon.meters["length"] -= 1
        w.record("tie", "hero", (path["changes"][2],), magic=p.magic)
    elif kind == "lift":
        w.entities["problem"].location = "sky"
        w.outcome = "moon_free"
        w.record("lift", "hero", (path["changes"][3],), result=w.outcome)
    elif kind == "pull":
        w.entities["problem"].meters["difficulty"] = 0
        w.outcome = "bell_rings"
        w.record("pull", "hero", (path["changes"][3],), result=w.outcome)
    elif kind == "stretch":
        w.entities["problem"].memes["loneliness"] = 0
        w.outcome = "colors_return"
        w.record("stretch", "hero", (path["changes"][3],), result=w.outcome)
    elif kind == "carry":
        w.entities["problem"].location = "soft soil"
        w.outcome = "seed_planted"
        w.record("carry", "hero", (path["changes"][3],), result=w.outcome)
    elif kind == "sing":
        w.entities["animal"].memes["hope"] = 2
        w.record("sing", "hero", (path["changes"][2],), magic=p.magic)
    elif kind == "release":
        w.outcome = "moon_free"
        w.record("release", "animal", (path["changes"][3],), result=w.outcome)
    elif kind == "ring":
        w.outcome = "bell_rings"
        w.record("ring", "animal", (path["changes"][3],), result=w.outcome)
    elif kind == "brighten":
        w.outcome = "colors_return"
        w.record("brighten", "animal", (path["changes"][3],), result=w.outcome)
    elif kind == "sprout":
        w.outcome = "seed_planted"
        w.record("sprout", "animal", (path["changes"][3],), result=w.outcome)
    else:
        raise StoryError(f"Unknown action {kind!r}.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for action in PATHS[(p.problem, p.solution)]["actions"]:
        execute(w, action)
    if not w.outcome:
        raise StoryError("The path did not resolve.")
    return w


class Teller:
    def __init__(self, w: World):
        self.w = w
        self.p = w.params
        self.rng = random.Random(self.p.prose_seed)
        self.parts: list[str] = []
        self.qa: list[QAItem] = []

    def line(self, *choices: str) -> None:
        self.parts.append(self.rng.choice(choices))

    def tell(self) -> None:
        p = self.p
        self.line(
            f"{p.hero} skipped to the {p.place}, where {PROBLEM_TEXT[p.problem]} waited.",
            f"By the {p.place}, {p.hero} found {PROBLEM_TEXT[p.problem]}.",
        )
        self.parts.append(
            f"Round and round went the gingham ribbon, "
            f"for Magic was awake in its red-and-white squares."
        )
        self.parts.append(f'"What is wrong?" asked {p.hero}.')
        self.parts.append(
            f'"Listen close," said the {p.animal}. '
            f'"{PATHS[(p.problem, p.solution)]["clue"]}"'
        )
        self.parts.append(
            f'"Then we shall try a {p.solution.replace("_", " ")}," said {p.hero}.'
        )

        if p.solution == "ribbon_bridge":
            self.parts.append(
                f"{p.hero} tied the gingham ribbon from the {p.place} to the waiting trouble. "
                f"It stretched like a tiny road."
            )
            self.parts.append(
                f'"Step softly," said {p.hero}. "The ribbon is ready." '
                f'"And hope is ready too," said the {p.animal}.'
            )
        else:
            self.parts.append(
                f"{p.hero} lifted the gingham ribbon and sang a small nursery rhyme. "
                f"The Magic in its squares glittered with every beat."
            )
            self.parts.append(
                f'"Again!" cried the {p.animal}. "The quiet thing can hear you." '
                f'"Then again," said {p.hero}, and sang.'
            )

        if p.problem == "moon_stuck":
            self.parts.append(
                "Up slipped the moon, round and bright, "
                "like a silver button in the night."
            )
            answer = (
                "The gingham ribbon made a little bridge so the moon could be lifted free."
                if p.solution == "ribbon_bridge"
                else "The moon was waiting for a song, so the hero sang with the animal until it floated free."
            )
        elif p.problem == "bell_silent":
            self.parts.append("Ting-a-ling! The blue bell rang, and the lane rang after it.")
            answer = (
                "The gingham ribbon reached the bell's clapper across the puddle and pulled it."
                if p.solution == "ribbon_bridge"
                else "The bell remembered its tune when the hero and animal sang."
            )
        elif p.problem == "rainbow_faded":
            self.parts.append("Red came first, then gold, then blue, bright as a bird's eye.")
            answer = (
                "The gingham ribbon stretched across the gray gap and helped the colors return."
                if p.solution == "ribbon_bridge"
                else "The rainbow brightened because the hero's song woke its sleeping colors."
            )
        else:
            self.parts.append("Pop! A green sprout rose, wearing a drop of morning dew.")
            answer = (
                "The gingham ribbon carried the seed across the dry crack to soft soil."
                if p.solution == "ribbon_bridge"
                else "The seed sprouted after the hero's song woke it."
            )

        self.parts.append(PATHS[(p.problem, p.solution)]["ending"])
        self.qa.append(QAItem(
            question="How was the problem solved?",
            answer=answer,
        ))
        self.qa.append(QAItem(
            question="What part did the gingham ribbon play?",
            answer=(
                "It was the magical object that became a bridge."
                if p.solution == "ribbon_bridge"
                else "It carried Magic through a song and helped the waiting thing change."
            ),
        ))
        return

    def render(self) -> tuple[str, list[QAItem]]:
        self.tell()
        return "\n\n".join(self.parts), self.qa


ASP_RULES = """
compatible(P,S) :- problem(P), solution(S), bridge(P,S).
compatible(P,S) :- problem(P), solution(S), song(P,S).
resolved(P,S) :- compatible(P,S).
#show compatible/2.
#show resolved/2.
"""


def asp_facts() -> str:
    from asp import fact
    lines = [fact("problem", p) for p in PROBLEMS]
    lines += [fact("solution", s) for s in SOLUTIONS]
    for problem in PROBLEMS:
        lines.append(fact("bridge", problem, "ribbon_bridge"))
        lines.append(fact("song", problem, "ribbon_song"))
    return "\n".join(lines)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "compatible"))


def generate(p: StoryParams) -> StorySample:
    world = simulate(p)
    story, story_qa = Teller(world).render()
    prompt = (
        f"Write a Nursery Rhyme about {p.hero}, a {p.animal}, gingham, "
        f"and {p.magic} Magic solving {p.problem.replace('_', ' ')}."
    )
    return StorySample(
        params=p,
        story=story,
        prompts=[prompt],
        story_qa=story_qa,
        world_qa=[
            QAItem(
                question="What is the setting?",
                answer=f"The story takes place near the {p.place}.",
            )
        ],
        world=world,
    )


def verify() -> None:
    expected = set(PATHS)
    if asp_combos() != expected:
        raise StoryError("ASP and Python disagree about compatible paths.")
    for problem, solution in expected:
        p = StoryParams(problem=problem, solution=solution)
        sample = generate(p)
        if not sample.world.outcome:
            raise StoryError("A verified story lacks an outcome.")
        if "gingham" not in sample.story.lower():
            raise StoryError("The seed word is missing.")
        if "Magic" not in sample.story:
            raise StoryError("Magic is missing.")
        if '"' not in sample.story or sample.story.count('"') < 4:
            raise StoryError("The story needs a back-and-forth exchange.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError("Unresolved template field.")
    print(f"OK: {len(expected)} executable paths; ASP parity; dialogue and grounding verified.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--magic", choices=MAGICS)
    parser.add_argument("--voice", choices=VOICES)
    for name in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + name, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    sample = args.n > 1
    p = StoryParams(
        world_seed=args.seed + index,
        prose_seed=args.prose_seed + index,
        hero=args.hero or (rng.choice(HEROES) if sample else "Nell"),
        animal=args.animal or (rng.choice(ANIMALS) if sample else "mouse"),
        place=args.place or (rng.choice(PLACES) if sample else "garden gate"),
        problem=args.problem or (rng.choice(PROBLEMS) if sample else "moon_stuck"),
        solution=args.solution or (rng.choice(SOLUTIONS) if sample else "ribbon_bridge"),
        magic=args.magic or (rng.choice(MAGICS) if sample else "sparkle"),
        voice=args.voice or (rng.choice(VOICES) if sample else "bouncy"),
    )
    validate_params(p)
    return p


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "state": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0

        rng = random.Random(args.seed)
        if args.all:
            params = []
            for problem, solution in PATHS:
                p = resolve_params(args, rng)
                p.problem = problem
                p.solution = solution
                validate_params(p)
                params.append(p)
        else:
            params = [resolve_params(args, rng, i) for i in range(args.n)]

        samples = [generate(p) for p in params]
        if args.json:
            value = [sample.to_dict() for sample in samples]
            print(json.dumps(value[0] if len(value) == 1 else value, ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
