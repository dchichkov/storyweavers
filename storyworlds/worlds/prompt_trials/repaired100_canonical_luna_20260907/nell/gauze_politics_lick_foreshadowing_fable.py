#!/usr/bin/env python3
"""A fable about gauze, a village election, and the cost of a careless lick."""

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


CANDIDATES = ("Mara", "Oren")
ANIMALS = ("fox", "goat", "crow")
MESSAGES = ("kindness", "order")
SUPPLIES = ("gauze", "none")
VOICES = ("plain", "warm", "wry")


@dataclass
class StoryParams:
    candidate: str = "Mara"
    animal: str = "fox"
    message: str = "kindness"
    supply: str = "gauze"
    voice: str = "warm"
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

    def record(self, kind, actor, facts=(), needs=(), **data):
        missing = [fact for fact in needs if fact not in self.facts]
        if missing:
            raise StoryError(f"{kind} needs missing evidence: {', '.join(missing)}.")
        causes = tuple(sorted({self.facts[fact] for fact in needs}))
        event = Event(len(self.history), kind, actor, data, tuple(facts), causes)
        self.history.append(event)
        for fact in facts:
            self.facts[fact] = event.id


def validate_params(p: StoryParams):
    if p.candidate not in CANDIDATES:
        raise StoryError(f"Unknown candidate: {p.candidate}.")
    if p.animal not in ANIMALS:
        raise StoryError(f"Unknown animal: {p.animal}.")
    if p.message not in MESSAGES:
        raise StoryError(f"Unknown message: {p.message}.")
    if p.supply not in SUPPLIES:
        raise StoryError(f"Unknown supply: {p.supply}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice}.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    animal_label = {"fox": "the fox", "goat": "the goat", "crow": "the crow"}[p.animal]
    entities = {
        "hero": Entity("hero", p.candidate, "character", "square",
                       memes={"pride": 0.5, "care": 1}),
        "animal": Entity("animal", animal_label, "animal", "square",
                         meters={"hurt": 1, "bite": 0}, memes={"fear": 1}),
        "ballot": Entity("ballot", "the ballot box", "object", "square",
                         meters={"trust": 1}),
        "gauze": Entity("gauze", "the gauze", "object",
                        "pocket" if p.supply == "gauze" else "shop",
                        meters={"clean": 1, "length": 2}),
        "council": Entity("council", "the council table", "place", "square",
                          meters={"stability": 1}),
    }
    w = World(p, entities)
    w.record("opening", "hero", facts=("election_open", "animal_seen"),
             candidate=p.candidate, message=p.message)
    return w


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    w.record("warning", "animal", facts=("warning_seen",), needs=("animal_seen",),
             warning="the animal keeps licking its sore paw")
    if p.supply == "none":
        w.record("search", "hero", facts=("gauze_found",), needs=("warning_seen",),
                 place="the apothecary")
    else:
        w.record("notice", "hero", facts=("gauze_found",), needs=("warning_seen",),
                 place="a pocket")
    w.record("bandage", "hero", facts=("paw_wrapped",), needs=("gauze_found",),
             method="clean gauze")
    w.entities["animal"].meters["hurt"] = 0
    w.entities["animal"].memes["fear"] = 0
    w.record("conversation", "animal", facts=("truth_learned",), needs=("paw_wrapped",),
             truth="the animal feared a loud council")
    w.record("choice", "hero", facts=("promise_made",), needs=("truth_learned",),
             promise="a quiet vote")
    w.record("vote", "council", facts=("election_settled",), needs=("promise_made",),
             result=p.message)
    w.outcome = "kindness_before_power"
    w.record("ending", "hero", facts=("story_complete",), needs=("election_settled",),
             outcome=w.outcome)
    validate_world(w)
    return w


def validate_world(w: World):
    if w.outcome != "kindness_before_power":
        raise StoryError("The fable needs a moral resolution.")
    if w.entities["animal"].meters["hurt"] != 0:
        raise StoryError("The animal must be healed.")
    if "paw_wrapped" not in w.facts or "election_settled" not in w.facts:
        raise StoryError("The healing and election must both occur.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on the future.")


class Teller:
    def __init__(self, w: World):
        self.w = w
        self.p = w.params
        self.rng = random.Random(self.p.prose_seed)
        self.lines = []
        self.qa = []

    def say(self, text):
        self.lines.append(text)

    def dialogue(self, first, second, third=None):
        self.lines.append(f'"{first}" said {self.p.candidate}.')
        self.lines.append(f'"{second}" said the {self.p.animal}.')
        if third:
            self.lines.append(f'"{third}" replied {self.p.candidate}.')

    def run(self):
        p = self.p
        for event in self.w.history:
            if event.kind == "opening":
                self.say(
                    f"On the morning of the village election, {p.candidate} stood beneath the elm "
                    f"and polished a speech about {p.message}."
                )
                self.dialogue(
                    "Today the village will choose its voice.",
                    "Then listen before you ask us to listen to you.",
                    "That is a strange campaign rule."
                )
                self.say(
                    "A fox limped past the council table, and every few steps it gave its paw a quick lick. "
                    "The small act was easy to miss, but it was the first sign that the day would not belong to speeches alone."
                )
                self.qa.append(QAItem(
                    "What sign hinted that the election would need more than speeches?",
                    "A fox limped past the council table and kept licking its sore paw."
                ))
            elif event.kind == "warning":
                self.say(
                    "The fox tried to hide beneath the bench. Its paw was raw, and each lick made it wince."
                )
                self.dialogue(
                    "Why do you keep licking that paw?",
                    "Because it hurts, and no one has stopped to see why.",
                    "Then I will stop first."
                )
            elif event.kind == "notice":
                self.say(
                    f"{p.candidate} reached into a pocket and found a clean roll of gauze. "
                    "The candidate had carried it for a scraped knee, but a pocket is a poor place "
                    "for a remedy unless someone remembers to use it."
                )
            elif event.kind == "search":
                self.say(
                    f"{p.candidate} hurried to the apothecary and returned with gauze. "
                    "The election bell rang once while the candidate was away."
                )
            elif event.kind == "bandage":
                self.say(
                    f"{p.candidate} washed the fox's paw and wrapped it in soft gauze. "
                    "The fox stopped licking and placed its weight carefully on the bandage."
                )
                self.dialogue(
                    "There. The gauze will guard the cut.",
                    "You guarded me before asking for my vote.",
                    "A vote is not a bandage, and a bandage is not a vote."
                )
                self.qa.append(QAItem(
                    "How did the candidate help the fox?",
                    "The candidate washed the fox's sore paw and wrapped it in clean gauze, so the fox no longer needed to lick it."
                ))
            elif event.kind == "conversation":
                self.say(
                    "When the fox felt safe, it told the truth. It feared the council's shouting more than it feared the election."
                )
                self.dialogue(
                    "The council argues until small voices disappear.",
                    "Then promise a quiet vote, not a grand victory.",
                    "I promise the first."
                )
            elif event.kind == "choice":
                self.say(
                    f"{p.candidate} folded the speech and promised that the village would hear the quiet voices first. "
                    "The promise changed the campaign from a contest of pride into a duty of care."
                )
            elif event.kind == "vote":
                self.say(
                    f"At the council table, the villagers chose {p.message}. "
                    "No one shouted over the fox, and the bandaged paw rested beneath the bench."
                )
            elif event.kind == "ending":
                self.say(
                    f"{p.candidate} did not win the village by making the loudest promise. "
                    "The candidate won its trust by noticing the paw that everyone else had passed."
                )
                self.say(
                    "And the fox gave one final lick to the edge of the gauze, not because it hurt, "
                    "but because it was grateful."
                )
                self.qa.append(QAItem(
                    "What did the election teach the village?",
                    "The village learned that kindness and careful listening should come before the desire for power."
                ))
        return "\n\n".join(self.lines), self.qa


ASP_RULES = """
needs_gauze :- animal_hurt, supply_gauze.
healed :- needs_gauze.
trustworthy :- healed, truth_heard.
good_choice :- trustworthy, quiet_vote.
#show needs_gauze/0.
#show healed/0.
#show trustworthy/0.
#show good_choice/0.
"""


def asp_facts(p=None):
    from asp import fact
    p = p or StoryParams()
    return "\n".join([
        fact("animal_hurt"),
        fact("supply_gauze") if p.supply == "gauze" else "",
        fact("truth_heard"),
        fact("quiet_vote") if p.message == "kindness" else "",
    ])


def asp_outcome(p=None):
    from asp import atoms, one_model
    model = one_model(asp_facts(p) + ASP_RULES)
    return set(atoms(model, "good_choice"))


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    story, qa = Teller(world).run()
    return StorySample(
        params=params,
        story=story,
        prompts=["Write a fable about gauze, politics, and a fox that keeps licking its sore paw."],
        story_qa=qa,
        world_qa=[
            QAItem(
                "Why is gauze useful for a wound?",
                "Clean gauze protects a wound and helps keep it from being rubbed or dirtied."
            )
        ],
        world=world,
    )


def verify():
    for supply, message in itertools.product(SUPPLIES, MESSAGES):
        p = StoryParams(supply=supply, message=message)
        sample = generate(p)
        if "gauze" not in sample.story.lower() or "lick" not in sample.story.lower():
            raise StoryError("The required story instruments are missing.")
        if trace_signature(sample.world) != trace_signature(simulate(p)):
            raise StoryError("Rendering changed the world trace.")
    if asp_outcome(StoryParams(supply="gauze", message="kindness")) != {()}:
        raise StoryError("ASP did not recognize the resolved fable.")
    print("OK: world simulation, story grounding, and ASP parity.")


def trace_signature(w):
    return json.dumps([asdict(event) for event in w.history], sort_keys=True)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--candidate", choices=CANDIDATES)
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--message", choices=MESSAGES)
    parser.add_argument("--supply", choices=SUPPLIES)
    parser.add_argument("--voice", choices=VOICES, default="warm")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.seed + index,
        prose_seed=args.seed + 1000 + index,
        voice=args.voice,
    )
    choices = {
        "candidate": CANDIDATES,
        "animal": ANIMALS,
        "message": MESSAGES,
        "supply": SUPPLIES,
    }
    for name, values in choices.items():
        given = getattr(args, name)
        setattr(p, name, given if given is not None else (rng.choice(values) if sample else getattr(p, name)))
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
        print(json.dumps({
            "history": [asdict(event) for event in sample.world.history],
            "outcome": sample.world.outcome,
        }, indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(ASP_RULES.strip())
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_outcome())))
            return 0
        rng = random.Random(args.seed)
        if args.all:
            params = []
            for supply, message in itertools.product(SUPPLIES, MESSAGES):
                if args.supply is not None and args.supply != supply:
                    continue
                if args.message is not None and args.message != message:
                    continue
                p = resolve_params(args, rng)
                p.supply = supply
                p.message = message
                params.append(p)
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1) for i in range(args.n)]
        samples = [generate(p) for p in params]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload, ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
