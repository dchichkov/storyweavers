#!/usr/bin/env python3
"""A compact hotel-lobby whodunit about a dim chick, a garter, and repeated clues."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


SUSPECTS = ("Mara", "Otto", "Priya")
OBJECTS = ("garter", "brass_key", "blue_button")
LIGHTS = ("dim", "bright")
REPETITIONS = ("bell", "footsteps", "elevator")
MAX_STEPS = 20


@dataclass
class StoryParams:
    suspect: str = "Mara"
    light: str = "dim"
    repetition: str = "bell"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str = "hotel_lobby"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


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

    def record(self, kind, actor, facts=(), needs=(), **data):
        causes = tuple(sorted({self.facts[x] for x in needs}))
        if any(x not in self.facts for x in needs):
            raise StoryError(f"{kind} lacks an observed cause.")
        event = Event(len(self.history), kind, actor, data, tuple(facts), causes)
        self.history.append(event)
        for fact in facts:
            self.facts[fact] = event.id

    def snapshot(self):
        return {
            "entities": {k: asdict(v) for k, v in self.entities.items()},
            "facts": sorted(self.facts),
            "outcome": self.outcome,
        }


def validate_params(p):
    if p.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if p.light not in LIGHTS:
        raise StoryError("The lobby light must be dim or bright.")
    if p.repetition not in REPETITIONS:
        raise StoryError("Unknown repeated lobby clue.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p):
    validate_params(p)
    return World(
        p,
        {
            "detective": Entity("detective", "Nell", "character"),
            "clerk": Entity("clerk", "the clerk", "character"),
            "suspect": Entity("suspect", p.suspect, "character"),
            "garter": Entity("garter", "a green garter", "object", meters={"length": 1}),
            "key": Entity("key", "the brass key", "object"),
            "button": Entity("button", "a blue button", "object"),
            "bell": Entity("bell", "the front-desk bell", "object"),
            "ledger": Entity("ledger", "the guest ledger", "object"),
            "clock": Entity("clock", "the lobby clock", "object"),
        },
    )


def simulate(p):
    w = build_world(p)
    w.record("arrival", "detective", facts=("missing_key", "lobby_seen"),
             repetition=p.repetition, light=p.light)
    w.record("first_question", "detective", facts=("suspect_named",),
             needs=("missing_key",), suspect=p.suspect)
    w.record("repeat_clue", "clerk", facts=("repeat_heard",),
             needs=("lobby_seen",), clue=p.repetition)
    w.record("dim_observation", "detective", facts=("dim_seen",),
             needs=("repeat_heard",), light=p.light)
    w.record("garter_found", "detective", facts=("garter_seen",),
             needs=("dim_seen",), object="garter", place="under sofa")
    w.record("second_question", "detective", facts=("answer_changed",),
             needs=("suspect_named", "garter_seen"), suspect=p.suspect)
    w.record("solution", "detective", facts=("culprit_known",),
             needs=("repeat_heard", "garter_seen", "answer_changed"),
             culprit=p.suspect)
    w.outcome = "the garter exposed the false alibi"
    w.record("departure", "detective", facts=("ending",),
             needs=("culprit_known",), outcome=w.outcome)
    validate_world(w)
    return w


def validate_world(w):
    if "ending" not in w.facts or not w.outcome:
        raise StoryError("The mystery must end.")
    if "repeat_heard" not in w.facts or "garter_seen" not in w.facts:
        raise StoryError("The repeated clue and garter must matter.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("A clue cannot depend on the future.")


def render(w):
    p = w.params
    color = "soft gray" if p.light == "dim" else "clear gold"
    repeated = {
        "bell": "The front-desk bell rang twice, though nobody touched it.",
        "footsteps": "Footsteps crossed the marble floor twice, then stopped beside the sofa.",
        "elevator": "The elevator opened twice on the same empty floor.",
    }[p.repetition]
    lines = [
        f"In the {p.light} hotel lobby, Nell noticed that the brass room key was missing.",
        f'"Who last held it?" Nell asked. "I did not," said {p.suspect}.',
        f"The clerk looked toward the {color} windows. {repeated}",
        f'"That happened before," Nell said. "Then we should remember what came next."',
        "Under a velvet sofa, she found a green garter with fresh dust on its edge.",
        f'"This is not mine," said {p.suspect}. "It is not proof."',
        '"No," Nell agreed. "But it is a clock with a loose hand."',
        f"The first time Nell asked, the suspect said the sofa had been empty. The second time, after the garter appeared, {p.suspect} said the sofa had been crossed in a hurry.",
        f'"Why change the story?" Nell asked. "Because you saw me find it," said {p.suspect}.',
        f"The repeated {p.repetition} had fixed the moment: the garter had fallen when the suspect hurried past the sofa, and the key had slipped from the same pocket.",
        f'{p.suspect} opened that pocket and found the brass key. The lobby became quiet, and the mystery was no longer missing.',
        '"A small clue can make a large lie stumble," Nell told the clerk.',
    ]
    story = "\n\n".join(lines)
    qa = [
        QAItem("What object helped Nell solve the mystery?",
               "A green garter under the velvet sofa showed that the suspect had hurried past it."),
        QAItem("Why did the suspect's story fail?",
               f"The suspect gave a different answer after Nell found the garter, so the repeated {p.repetition} helped place the suspect at the sofa."),
        QAItem("Where was the missing key?",
               f"The brass key was hidden in {p.suspect}'s pocket."),
    ]
    return story, qa


ASP_RULES = """
observed(repetition).
observed(garter).
culprit(S) :- suspect(S), observed(repetition), observed(garter), changed_answer(S).
#show culprit/1.
"""


def asp_facts():
    from asp import fact
    return "\n".join(
        [fact("suspect", x.lower()) for x in SUSPECTS]
        + [fact("observed", "repetition"), fact("observed", "garter")]
        + [fact("changed_answer", x.lower()) for x in SUSPECTS]
    )


def asp_solution():
    from asp import atoms, one_model
    return atoms(one_model(asp_facts() + ASP_RULES), "culprit")


def generate(p):
    w = simulate(p)
    story, qa = render(w)
    return StorySample(
        params=p,
        story=story,
        prompts=["Write a Whodunit in a hotel lobby where a chick-dim clue, a garter, and repetition frustrate a false alibi."],
        story_qa=qa,
        world_qa=[
            QAItem("What does repetition do in a mystery?",
                   "Repetition lets an investigator compare what happened more than once and notice a change or pattern.")
        ],
        world=w,
    )


def verify():
    if asp_solution() != [("mara",), ("otto",), ("priya",)]:
        raise StoryError("ASP and Python disagree about possible culprits.")
    for light, repetition, suspect in itertools.product(LIGHTS, REPETITIONS, SUSPECTS):
        sample = generate(StoryParams(light=light, repetition=repetition, suspect=suspect))
        if "garter" not in sample.story or repetition not in sample.story:
            raise StoryError("A generated story omitted a required clue.")
    print("OK: hotel-lobby simulations, dialogue, repetition, conflict, and ASP parity.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--suspect", choices=SUSPECTS)
    parser.add_argument("--light", choices=LIGHTS)
    parser.add_argument("--repetition", choices=REPETITIONS)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(world_seed=args.world_seed + index, prose_seed=args.prose_seed + index)
    for name, values in (("suspect", SUSPECTS), ("light", LIGHTS), ("repetition", REPETITIONS)):
        value = getattr(args, name)
        setattr(p, name, value if value is not None else rng.choice(values) if sample else getattr(p, name))
    validate_params(p)
    return p


def emit(sample, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(sample.world.snapshot(), indent=2))


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
            print(json.dumps(asp_solution()))
            return 0
        rng = random.Random(args.world_seed)
        if args.all:
            params = [
                resolve_params(args, rng, i, sample=False)
                for i in range(args.n)
            ]
            params = [
                StoryParams(suspect=s, light=l, repetition=r,
                            world_seed=args.world_seed + i,
                            prose_seed=args.prose_seed + i)
                for i, (s, l, r) in enumerate(
                    itertools.product(SUSPECTS, LIGHTS, REPETITIONS)
                )
            ]
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1) for i in range(args.n)]
        samples = [generate(p) for p in params]
        if args.json:
            rows = [s.to_dict() for s in samples]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
