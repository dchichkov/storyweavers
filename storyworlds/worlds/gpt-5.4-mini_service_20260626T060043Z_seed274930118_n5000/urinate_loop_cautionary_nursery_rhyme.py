#!/usr/bin/env python3
"""
A small cautionary nursery-rhyme storyworld about a looping play path,
a growing urge to urinate, and a timely stop before a mishap.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

LOOP_CHOICES = ["loop"]
SETTING_CHOICES = ["yard", "garden", "path", "playroom"]

CHARACTER_NAMES = ["Milo", "Nina", "Poppy", "Teddy", "Luna", "Wren"]
CHARACTER_TYPES = ["bunny", "duckling", "kitten", "pup", "mouse", "foxling"]
GUARDIAN_TYPES = ["mother", "father", "aunt", "uncle", "grandma", "grandpa"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "aunt", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "uncle", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class LoopPath:
    place: str
    has_tree: bool = True
    has_gate: bool = True
    has_potty: bool = False
    has_bed: bool = False


@dataclass
class StoryParams:
    place: str
    name: str
    creature: str
    guardian: str
    loop_count: int
    seed: Optional[int] = None


class World:
    def __init__(self, setting: LoopPath) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary nursery-rhyme loop storyworld.")
    ap.add_argument("--place", choices=SETTING_CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--creature", choices=CHARACTER_TYPES)
    ap.add_argument("--guardian", choices=GUARDIAN_TYPES)
    ap.add_argument("--loop", dest="loop_count", type=int)
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


def rhyme_line(name: str, creature: str, loop_count: int) -> str:
    return f"{name} the {creature} went round the loop {loop_count} times, a tripping little tune in twinkling rhymes."


def no_story_reason() -> str:
    return "(No story: the loop must be a real repeated path and the caution must matter.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(SETTING_CHOICES)
    name = args.name or rng.choice(CHARACTER_NAMES)
    creature = args.creature or rng.choice(CHARACTER_TYPES)
    guardian = args.guardian or rng.choice(GUARDIAN_TYPES)
    loop_count = args.loop_count if args.loop_count is not None else rng.choice([2, 3, 4, 5])

    if loop_count < 2:
        raise StoryError("The rhyme needs at least two turns around the loop.")
    if place not in SETTING_CHOICES:
        raise StoryError(no_story_reason())

    return StoryParams(place=place, name=name, creature=creature, guardian=guardian, loop_count=loop_count)


def _can_urge_escalate(loop_count: int) -> bool:
    return loop_count >= 3


def tell(params: StoryParams) -> World:
    world = World(LoopPath(place=f"the {params.place}", has_potty=True))
    child = world.add(Entity(id=params.name, kind="character", type=params.creature))
    guardian = world.add(Entity(id="guardian", kind="character", type=params.guardian, label=f"the {params.guardian}"))
    potty = world.add(Entity(id="potty", kind="thing", type="potty", label="little potty chair", owner=child.id))
    child.meters["urinate"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["relief"] = 0.0

    world.say(f"{params.name} was a tiny {params.creature} with busy feet and a bouncy grin.")
    world.say(f"{params.name} liked the {params.place} loop, and every lap made the tune feel brighter.")
    world.say(f"Each round began as a game, with {params.name} humming softly and counting the stones.")

    world.para()
    world.say(f"On lap one, the song was merry; on lap two, {params.name} still ran with a cheery stride.")
    child.meters["urinate"] += 1
    child.memes["worry"] += 1
    world.say(f"But by the third turn, a squirmy feeling grew, a sign that {params.name} needed to urinate soon.")

    if _can_urge_escalate(params.loop_count):
        child.meters["urinate"] += 1
        world.say(f"Round and round came the loop again, and the urge grew stronger with every step.")
        world.say(f"{params.name} pressed close to {params.guardian} and whispered, 'I need the potty now.'")
        child.memes["worry"] += 1
        child.memes["relief"] += 1
        world.say(f"{params.guardian.capitalize()} hurried {params.name} to the little potty chair before a puddle could start.")
        world.say(f"There was no crash, no splash, no shame—just a quick stop and a careful breath.")
        world.para()
        world.say(f"After that, {params.name} went back to the loop with lighter feet and a shining smile.")
        world.say(f"The rhyme stayed sweet, and the caution saved the day from a wet little mishap.")
    else:
        world.say(f"{params.name} slowed down at once, and {params.guardian} pointed to the potty chair.")
        child.memes["relief"] += 1
        world.say(f"A wise little pause was enough, and the loop ended before any trouble began.")
        world.para()
        world.say(f"Then {params.name} returned to the {params.place} loop calm, dry, and very proud.")

    world.facts.update(
        child=child,
        guardian=guardian,
        potty=potty,
        params=params,
        loop_count=params.loop_count,
        caution=child.meters["urinate"] >= 1,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a cautionary nursery rhyme about {p.name} the {p.creature} going round a loop.",
        f"Tell a gentle story where {p.name} notices a need to urinate before playing one lap too many.",
        f"Write a short rhyming story set at {world.setting.place} with a loop, a warning, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    guardian: Entity = world.facts["guardian"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {p.name}, a little {p.creature} who loves the loop at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {p.name} need to do before the loop went too far?",
            answer=f"{p.name} needed to urinate and stop at the potty before the feeling turned into trouble.",
        ),
        QAItem(
            question=f"How did {p.name} and {guardian.type} keep the day safe?",
            answer=f"{p.name} told {guardian.pronoun('object')} about the urge, and {guardian.pronoun('subject')} helped {p.name} reach the potty chair in time.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {p.name} was calm, dry, and happy to go back to the loop after a careful pause.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a loop?",
            answer="A loop is a path or shape that goes around and comes back again.",
        ),
        QAItem(
            question="What does urinate mean?",
            answer="To urinate means to let pee out of your body, usually in a potty or toilet.",
        ),
        QAItem(
            question="Why should a child stop when the urge gets strong?",
            answer="A child should stop because waiting too long can cause a wet accident and make a mess.",
        ),
    ]


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import

    return "\n".join(
        [
            asp.fact("setting", "loop_place"),
            asp.fact("loop_place", "yard"),
            asp.fact("loop_place", "garden"),
            asp.fact("loop_place", "path"),
            asp.fact("loop_place", "playroom"),
            asp.fact("action", "loop"),
            asp.fact("action", "urinate"),
            asp.fact("warning", "cautionary"),
            asp.fact("style", "nursery_rhyme"),
        ]
    )


ASP_RULES = r"""
#show valid_story/2.
setting(loop_place).
action(loop).
action(urinate).
warning(cautionary).
style(nursery_rhyme).

valid_story(Place, loop) :- setting(Place), warning(cautionary), style(nursery_rhyme), action(loop), action(urinate).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp  # lazy import

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_ok = {"loop"}
    asp_ok = {a for _, a in asp_valid_stories()}
    if asp_ok == python_ok:
        print("OK: ASP and Python agree on the story seed facts.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", sorted(asp_ok))
    print("Python:", sorted(python_ok))
    return 1


def explain_rejection() -> str:
    return "(No story: this world needs a real loop, a caution, and the urinate turn.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(place="garden", name="Milo", creature="bunny", guardian="mother", loop_count=3),
        StoryParams(place="yard", name="Nina", creature="kitten", guardian="father", loop_count=4),
        StoryParams(place="path", name="Poppy", creature="duckling", guardian="aunt", loop_count=3),
        StoryParams(place="playroom", name="Teddy", creature="mouse", guardian="grandma", loop_count=2),
    ]


CURATED = build_curated()


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story seed:")
        for place, action in asp_valid_stories():
            print(f"  {place}: {action}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: loop={p.loop_count} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
