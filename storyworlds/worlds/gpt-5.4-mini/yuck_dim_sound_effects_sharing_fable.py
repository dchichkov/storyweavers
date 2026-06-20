#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yuck_dim_sound_effects_sharing_fable.py
========================================================================

A tiny fable-style story world about a dim little meal, the yuck-dim smell of
something no one wants, a sound-effect beat, and a sharing lesson.

The world is intentionally small:
- a pair of animal friends
- one shared bowl of food
- one needy helper who arrives hungry
- a state-driven turn where the food is either shared kindly or kept selfishly
- a clean ending image that proves what changed

It supports the standard storyworld CLI and the inline ASP twin for parity
checks. The prose aims for a child-facing fable tone with a simple moral.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/yuck_dim_sound_effects_sharing_fable.py
    python storyworlds/worlds/gpt-5.4-mini/yuck_dim_sound_effects_sharing_fable.py --all
    python storyworlds/worlds/gpt-5.4-mini/yuck_dim_sound_effects_sharing_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/yuck_dim_sound_effects_sharing_fable.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fullness": 0.0, "sourness": 0.0, "warmth": 0.0}
        if not self.memes:
            self.memes = {"kindness": 0.0, "hunger": 0.0, "joy": 0.0, "stinginess": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Bowl:
    id: str
    label: str
    phrase: str
    smell: str
    sound: str
    taste: str
    shareable: bool = True
    meters: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"fullness": 1.0, "sourness": 0.0}

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ShareChoice:
    id: str
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    animal1: str
    animal2: str
    hungry_guest: str
    bowl: str
    choice: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


ANIMALS = {
    "fox": ("fox", "fox"),
    "crow": ("crow", "crow"),
    "hare": ("hare", "hare"),
    "turtle": ("turtle", "turtle"),
    "cat": ("cat", "cat"),
    "mouse": ("mouse", "mouse"),
}

BOWLS = {
    "porridge": Bowl("porridge", "porridge", "a bowl of porridge", "yuck-dim", "glug-glug", "sweet and warm"),
    "berry_juice": Bowl("berry_juice", "berry juice", "a cup of berry juice", "yuck-dim", "sip-sip", "bright and sweet"),
    "root_soup": Bowl("root_soup", "root soup", "a small pot of root soup", "yuck-dim", "slurp-slurp", "earthy and warm"),
}

SHARES = {
    "share_kindly": ShareChoice("share_kindly", 3, "nudged the bowl toward the guest and said, 'Come, share with us.'",
                                "shared the food kindly and everyone felt better together", {"share"}),
    "split_half": ShareChoice("split_half", 3, "split the bowl in half with a careful little nod",
                              "split the food and gave the guest a fair half", {"share"}),
    "hide_bowl": ShareChoice("hide_bowl", 1, "hid the bowl behind a leaf and hoped nobody would ask",
                             "hid the food, which was a selfish choice", {"stingy"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny fable about yuck-dim food, sound effects, and sharing.")
    ap.add_argument("--animal1", choices=ANIMALS)
    ap.add_argument("--animal2", choices=ANIMALS)
    ap.add_argument("--hungry-guest", choices=ANIMALS)
    ap.add_argument("--bowl", choices=BOWLS)
    ap.add_argument("--choice", choices=SHARES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    a1 = args.animal1 or rng.choice(list(ANIMALS))
    a2 = args.animal2 or rng.choice([a for a in ANIMALS if a != a1])
    guest = args.hungry_guest or rng.choice([a for a in ANIMALS if a not in {a1, a2}])
    bowl = args.bowl or rng.choice(list(BOWLS))
    choice = args.choice or rng.choice(list(SHARES))
    if a1 == a2 or a1 == guest or a2 == guest:
        raise StoryError("Choose three different animals for the fable.")
    if args.choice and SHARES[args.choice].sense < SENSE_MIN:
        raise StoryError("(Refusing a selfish choice that scores too low on common sense.)")
    return StoryParams(a1, a2, guest, bowl, choice)


def reasonableness_gate(params: StoryParams) -> bool:
    return params.animal1 != params.animal2 and params.animal1 != params.hungry_guest and params.animal2 != params.hungry_guest


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out = []
    for a1 in ANIMALS:
        for a2 in ANIMALS:
            for guest in ANIMALS:
                for bowl in BOWLS:
                    for choice in SHARES:
                        p = StoryParams(a1, a2, guest, bowl, choice)
                        if reasonableness_gate(p):
                            out.append((a1, a2, guest, bowl, choice))
    return out


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for b in BOWLS:
        lines.append(asp.fact("bowl", b))
    for c, obj in SHARES.items():
        lines.append(asp.fact("choice", c))
        lines.append(asp.fact("sense", c, obj.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A1,A2,G,B,C) :- animal(A1), animal(A2), animal(G), bowl(B), choice(C),
                      A1 != A2, A1 != G, A2 != G.
sensible(C) :- choice(C), sense(C,S), sense_min(M), S >= M.
outcome(shared) :- chosen(C), (C = share_kindly; C = split_half).
outcome(stingy) :- chosen(hide_bowl).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v[0] for v in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    if set(asp_sensible()) != {c for c, s in SHARES.items() if s.sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH: ASP sensible choices differ from Python.")
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: smoke test story was empty.")
    print("OK: verification completed.")
    return rc


def _r_share(world: World) -> list[str]:
    return []


def propagate(world: World) -> None:
    _ = world


def tell(params: StoryParams) -> World:
    world = World()
    a1 = world.add(Entity(params.animal1, kind="character", type=params.animal1, role="friend"))
    a2 = world.add(Entity(params.animal2, kind="character", type=params.animal2, role="friend"))
    guest = world.add(Entity(params.hungry_guest, kind="character", type=params.hungry_guest, role="guest"))
    bowl = world.add(Entity("bowl", kind="thing", type="bowl", label=BOWLS[params.bowl].label))
    choice = SHARES[params.choice]

    a1.memes["kindness"] = 1.0
    a2.memes["kindness"] = 1.0
    guest.memes["hunger"] = 1.0

    world.say(
        f"One dim evening, {a1.id} and {a2.id} found {BOWLS[params.bowl].phrase} on a low stone table. "
        f"The air smelled {BOWLS[params.bowl].smell}, and the little bowl went {BOWLS[params.bowl].sound} in the quiet."
    )
    world.say(
        f'{a1.id} wrinkled {a1.pronoun("possessive")} nose and said, "Yuck-dim!" '
        f'But {a2.id} looked closer and saw that the food could still help someone.'
    )

    world.para()
    world.say(
        f"Then {guest.id} came in slowly, with an empty belly and a hopeful face. "
        f'{guest.id} whispered, "May I have some too?"'
    )

    world.para()
    if params.choice == "hide_bowl":
        world.say(
            f'{a1.id} {choice.text}. The bowl stayed full, but the table felt colder.'
        )
        world.say(
            f'{guest.id} sat down without a crumb, and the room answered with a sad little "hmm."'
        )
        world.say(
            f"In the end, the food was still there, but nobody felt warmer."
        )
        outcome = "stingy"
    else:
        world.say(
            f'{a2.id} smiled and {choice.text}.'
        )
        world.say(
            f"The guest took a small bite, then another, and the table answered with a happy "
            f'"Mmm!" that chased the yuck-dim smell away.'
        )
        world.say(
            f"By the end, the bowl was lighter, the bellies were fuller, and the friends sat together as if the dim room had found a candle of its own."
        )
        outcome = "shared"

    world.facts.update(
        animal1=a1, animal2=a2, guest=guest, bowl=BOWLS[params.bowl], choice=choice,
        outcome=outcome,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable for a child that includes the words "yuck-dim" and a sound effect, and ends with a sharing lesson.',
        f"Tell a tiny fable about {f['animal1'].id} and {f['animal2'].id} finding {f['bowl'].phrase}, then deciding whether to share it with {f['guest'].id}.",
        f'Write a moral-style story where someone says "Yuck-dim!" at first, but the ending shows whether the food was shared kindly or kept selfishly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    if f["outcome"] == "shared":
        return [
            QAItem(
                question="Why did the food stop seeming so yuck-dim?",
                answer="Because the animals shared it with the hungry guest, and the happy sound of eating made the table feel kinder. Sharing changed the mood as much as the meal."
            ),
            QAItem(
                question="What did the ending prove?",
                answer="It proved that the friends could make a better choice when they noticed someone was hungry. The bowl became lighter, but their friendship became warmer."
            ),
        ]
    return [
        QAItem(
            question="Why was the ending sad?",
            answer="It was sad because the bowl stayed hidden instead of being shared with the hungry guest. The guest was still hungry, so the room felt cold and stingy."
        ),
        QAItem(
            question="What did the story teach?",
            answer="It taught that food is better when it is shared. A selfish choice can leave everyone feeling worse, even if the bowl is still full."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    bowl = world.facts["bowl"]
    return [
        QAItem(
            question="What does 'yuck-dim' suggest?",
            answer="It suggests something smells a little bad and the room is dim or gloomy. A child might say it when food looks unpleasant at first."
        ),
        QAItem(
            question="Why is sharing important?",
            answer="Sharing helps hungry or lonely creatures feel cared for. It also makes a small meal more fair, because everyone gets some."
        ),
        QAItem(
            question=f"What kind of sound did {bowl.label} make in the story?",
            answer="It made a soft food sound that fit a quiet table, like glug-glug or sip-sip. Sound effects can make a fable feel lively and easy to hear."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} ({e.kind}) memes={e.memes} meters={e.meters}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


CURATED = [
    StoryParams("fox", "crow", "mouse", "porridge", "share_kindly"),
    StoryParams("turtle", "hare", "cat", "berry_juice", "split_half"),
    StoryParams("crow", "fox", "mouse", "root_soup", "hide_bowl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible choices: {', '.join(asp_sensible())}")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
