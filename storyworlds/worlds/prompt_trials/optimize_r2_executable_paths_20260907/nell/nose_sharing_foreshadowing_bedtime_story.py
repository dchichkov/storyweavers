#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve()
for parent in ROOT.parents:
    if (parent / "storyworlds" / "results.py").exists():
        sys.path.insert(0, str(parent / "storyworlds"))
        break
else:
    sys.path.insert(0, str(ROOT.parents[2]))

from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


PROBLEMS = ("cold", "sniffles", "night_wind", "sleepy_sneeze")
SOLUTIONS = ("shared_warmth", "lantern_ritual")
NAMES = ("Mira", "Lina", "Tess", "Nora")
ANIMAL_NAMES = ("Pip", "Moss", "Bram", "Clover")
TONES = ("gentle", "cozy", "playful")
OPENINGS = ("moonlit", "rainy", "quiet")
MAX_STEPS = 12


@dataclass
class StoryParams:
    child: str = "Mira"
    friend: str = "Pip"
    problem: str = "cold"
    solution: str = "shared_warmth"
    tone: str = "gentle"
    opening: str = "moonlit"
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
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity]
    history: list[Event] = field(default_factory=list)
    facts: dict[str, int] = field(default_factory=dict)
    outcome: str = ""

    def record(self, kind, actor, *, facts=(), needs=(), **data):
        missing = [f for f in needs if f not in self.facts]
        if missing:
            raise StoryError(f"{kind} needs earlier facts: {', '.join(missing)}.")
        causes = tuple(sorted({self.facts[f] for f in needs}))
        event = Event(len(self.history), kind, actor, data, tuple(facts), causes)
        self.history.append(event)
        for fact in facts:
            self.facts[fact] = event.id

    def snapshot(self):
        return {
            "entities": {k: asdict(v) for k, v in self.entities.items()},
            "outcome": self.outcome,
        }


def validate_params(p: StoryParams):
    for value, choices, label in (
        (p.problem, PROBLEMS, "problem"),
        (p.solution, SOLUTIONS, "solution"),
        (p.tone, TONES, "tone"),
        (p.opening, OPENINGS, "opening"),
    ):
        if value not in choices:
            raise StoryError(f"Unknown {label}: {value!r}.")
    if not p.child or not p.child[0].isupper():
        raise StoryError("The child's name must begin with a capital letter.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def compatible(problem, solution):
    return (problem, solution) in {
        ("cold", "shared_warmth"),
        ("cold", "lantern_ritual"),
        ("sniffles", "shared_warmth"),
        ("sniffles", "lantern_ritual"),
        ("night_wind", "shared_warmth"),
        ("night_wind", "lantern_ritual"),
        ("sleepy_sneeze", "shared_warmth"),
        ("sleepy_sneeze", "lantern_ritual"),
    }


def build_world(p: StoryParams) -> World:
    validate_params(p)
    if not compatible(p.problem, p.solution):
        raise StoryError(f"The solution {p.solution!r} does not fit the problem {p.problem!r}.")
    entities = {
        "child": Entity(
            "child", p.child, "character", "bedroom",
            meters={"warmth": 4, "sleepiness": 6, "breath": 1},
            memes={"worry": 2, "kindness": 1},
        ),
        "friend": Entity(
            "friend", p.friend, "character", "bedroom",
            meters={"warmth": 2, "size": 1, "breath": 1},
            memes={"worry": 3, "trust": 1},
        ),
        "blanket": Entity("blanket", "the quilt", "thing", "bed", meters={"warmth": 4}),
        "lantern": Entity("lantern", "the little lantern", "thing", "shelf", meters={"glow": 0}),
        "window": Entity("window", "the window", "thing", "wall", meters={"closed": 0}),
        "nose": Entity("nose", "a small nose", "thing", "bed", meters={"tickle": 0}),
    }
    w = World(p, entities)
    w.record("opening", "child", facts=("problem_seen",), problem=p.problem)
    return w


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    w.record("notice", "child", facts=("clue_seen",), needs=("problem_seen",),
             clue="wind" if p.problem == "night_wind" else "nose")
    if p.solution == "shared_warmth":
        w.entities["blanket"].location = "shared_bed"
        w.entities["child"].meters["warmth"] += 2
        w.entities["friend"].meters["warmth"] += 3
        w.record("share_blanket", "child", facts=("warmth_shared",), needs=("clue_seen",))
        w.record("settle", "friend", facts=("friend_settled",), needs=("warmth_shared",))
        w.outcome = "shared_rest"
    else:
        w.entities["window"].meters["closed"] = 1
        w.entities["lantern"].meters["glow"] = 3
        w.entities["child"].meters["sleepiness"] += 2
        w.record("close_window", "child", facts=("wind_stilled",), needs=("clue_seen",))
        w.record("light_lantern", "friend", facts=("gentle_light",), needs=("wind_stilled",))
        w.record("settle", "friend", facts=("friend_settled",), needs=("gentle_light",))
        w.outcome = "lantern_rest"
    w.record("goodnight", "child", facts=("ending",), needs=("friend_settled",))
    validate_world(w)
    return w


def validate_world(w: World):
    if not w.outcome or "ending" not in w.facts:
        raise StoryError("The bedtime story has no resolved ending.")
    if w.entities["friend"].meters["warmth"] < 4 and w.outcome == "shared_rest":
        raise StoryError("Sharing must warm the friend.")
    if w.outcome == "lantern_rest" and w.entities["lantern"].meters["glow"] <= 0:
        raise StoryError("The lantern must glow before rest.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event depends on a future event.")


class Teller:
    def __init__(self, w: World):
        self.w = w
        self.p = w.params
        self.rng = random.Random(self.p.prose_seed)
        self.lines = []
        self.qa = []

    def say(self, text):
        self.lines.append(text)

    def exchange(self, pairs):
        for speaker, words in pairs:
            name = self.p.child if speaker == "child" else self.p.friend
            self.say(f'"{words}" said {name}.')

    def render(self):
        p, friend = self.p, self.p.friend
        if p.opening == "moonlit":
            self.say(f"Moonlight rested on {p.child}'s bedroom floor.")
        elif p.opening == "rainy":
            self.say(f"Rain whispered against {p.child}'s window.")
        else:
            self.say(f"The house was quiet, and bedtime had come.")

        self.say(f"{p.child} tucked {friend} beneath the quilt, but the little friend did not look ready for sleep.")
        if p.problem == "cold":
            self.say(f"{friend} curled up with a shiver. Even the tip of the small nose looked chilly.")
            question = "Why was the little friend uncomfortable?"
            answer = f"{friend} was cold, so {p.child} needed to find a gentle way to warm them."
        elif p.problem == "sniffles":
            self.say(f"{friend}'s nose gave a tiny sniff. Then it gave another, softer sniff.")
            question = "What told the child that the friend needed help?"
            answer = f"The friend's repeated sniffles and unhappy nose showed that bedtime was not yet comfortable."
        elif p.problem == "night_wind":
            self.say("A night wind slipped through the loose window and fluttered the quilt.")
            question = "What made the bedtime room uneasy?"
            answer = "A night wind came through the loose window and disturbed the quilt."
        else:
            self.say(f"{friend} tried to stifle a sneeze, but the small nose wiggled once, twice, and three times.")
            question = "What was happening to the friend's nose?"
            answer = f"The friend's nose was tickly, and a sneeze kept trying to arrive."

        self.exchange((
            ("child", f'"Do you want to tell me what is wrong, {friend}?"'),
            ("friend", "My nose says the night feels too big."),
            ("child", "Then we will make it small together."),
        ))
        self.say("The words made the room feel less lonely. Long ago, before the moon reached the chimney, someone had taught that sharing a little comfort could make a great deal of calm.")

        if p.solution == "shared_warmth":
            self.say(f"{p.child} lifted half the quilt and shared it instead of keeping the warmest fold.")
            self.exchange((
                ("friend", "Will there be enough for you?"),
                ("child", "Warmth grows when two friends share it."),
            ))
            self.say(f"{friend} moved close. The quilt covered both shoulders, and the little nose stopped trembling.")
            self.qa.append(QAItem(
                question="How did the child help the friend?",
                answer=f"{p.child} shared the quilt, so both friends became warm enough to rest together.",
            ))
            self.qa.append(QAItem(
                question="What changed after the quilt was shared?",
                answer=f"{friend} moved close beneath the shared quilt, and the worried nose became still.",
            ))
        else:
            self.say(f"{p.child} closed the loose window and placed the little lantern where its golden light could reach the bed.")
            self.exchange((
                ("friend", "The shadows were making my nose feel brave and frightened at once."),
                ("child", "The lantern can keep watch while we sleep."),
            ))
            self.say(f"The golden circle settled over the quilt. The room was quiet again, and {friend}'s nose gave one last tiny sniff.")
            self.qa.append(QAItem(
                question="How did the child make the room peaceful?",
                answer=f"{p.child} closed the loose window and lit the little lantern, stopping the wind and giving the room a gentle glow.",
            ))
            self.qa.append(QAItem(
                question="Why did the friend feel ready to sleep?",
                answer=f"The wind was shut out and the lantern made a calm circle of light around {friend}'s bed.",
            ))

        self.say(f"{p.child} whispered, \"Good night, {friend}.\"")
        self.say(f"{friend} whispered, \"Good night.\"")
        self.say(f"Outside, the moon climbed higher. Inside, the small nose rested softly, and the room held its peaceful breath.")
        self.qa.append(QAItem(
            question="What proved that bedtime had become peaceful?",
            answer=f"{friend} settled under the quilt, the small nose grew quiet, and both friends said good night before falling asleep.",
        ))
        self.qa.insert(0, QAItem(question=question, answer=answer))
        return "\n\n".join(self.lines), self.qa


ASP_RULES = """
compatible(P,S) :- problem(P), solution(S), allowed(P,S).
allowed(cold,shared_warmth).
allowed(cold,lantern_ritual).
allowed(sniffles,shared_warmth).
allowed(sniffles,lantern_ritual).
allowed(night_wind,shared_warmth).
allowed(night_wind,lantern_ritual).
allowed(sleepy_sneeze,shared_warmth).
allowed(sleepy_sneeze,lantern_ritual).
#show compatible/2.
"""


def asp_facts():
    from asp import fact
    rows = [fact("problem", p) for p in PROBLEMS]
    rows += [fact("solution", s) for s in SOLUTIONS]
    rows += [
        fact("allowed", p, s)
        for p in PROBLEMS
        for s in SOLUTIONS
    ]
    return "\n".join(rows)


def asp_combos():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "compatible"))


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    story, qa = Teller(world).render()
    return StorySample(
        params=params,
        story=story,
        prompts=[f"Tell a gentle bedtime story in which {params.child} helps {params.friend}'s nose feel safe through sharing."],
        story_qa=qa,
        world_qa=[
            QAItem(
                question="What makes a bedtime story comforting?",
                answer="A comforting bedtime story gives a worried character a small, kind action that changes the room and leads toward rest.",
            )
        ],
        world=world,
    )


def verify():
    expected = {(p, s) for p in PROBLEMS for s in SOLUTIONS}
    if asp_combos() != expected:
        raise StoryError("Python and ASP disagree about compatible paths.")
    for problem in PROBLEMS:
        for solution in SOLUTIONS:
            sample = generate(StoryParams(problem=problem, solution=solution))
            if "{ " in sample.story or "{" in sample.story or "}" in sample.story:
                raise StoryError("Unresolved template in story.")
            if not any("said" in line for line in sample.story.splitlines()):
                raise StoryError("Story lacks spoken dialogue.")
            if len(sample.story_qa) < 2:
                raise StoryError("Story lacks grounded questions.")
    print(f"OK: {len(expected)} executable paths; dialogue, QA, and ASP parity verified.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--child", choices=NAMES)
    parser.add_argument("--friend", choices=ANIMAL_NAMES)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--tone", choices=TONES)
    parser.add_argument("--opening", choices=OPENINGS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
    )
    registries = {
        "child": NAMES,
        "friend": ANIMAL_NAMES,
        "problem": PROBLEMS,
        "solution": SOLUTIONS,
        "tone": TONES,
        "opening": OPENINGS,
    }
    for name, choices in registries.items():
        value = getattr(args, name)
        if value is not None:
            setattr(p, name, value)
        elif sample:
            setattr(p, name, rng.choice(choices))
    validate_params(p)
    if not compatible(p.problem, p.solution):
        raise StoryError(f"The selected solution {p.solution!r} does not fit {p.problem!r}.")
    return p


def emit(sample, *, trace=False, qa=False, header=""):
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


def main():
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

        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for problem in PROBLEMS:
                for solution in SOLUTIONS:
                    if args.problem is not None and args.problem != problem:
                        continue
                    if args.solution is not None and args.solution != solution:
                        continue
                    p = resolve_params(args, rng, sample=False)
                    p.problem = problem
                    p.solution = solution
                    params.append(p)
        else:
            params = [
                resolve_params(args, rng, index=i, sample=args.n > 1)
                for i in range(args.n)
            ]

        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for i, params_item in enumerate(params):
                emit(
                    generate(params_item),
                    trace=args.trace,
                    qa=args.qa,
                    header=f"\n### Story {i + 1}\n" if len(params) > 1 else "",
                )
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
