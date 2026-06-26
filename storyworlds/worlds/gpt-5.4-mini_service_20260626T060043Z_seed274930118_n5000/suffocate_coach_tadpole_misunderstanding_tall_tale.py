#!/usr/bin/env python3
"""
storyworlds/worlds/suffocate_coach_tadpole_misunderstanding_tall_tale.py
=========================================================================

A small Tall Tale storyworld about a coach, a tadpole, and a misunderstanding.

Seed story:
---
A mighty little river coach named Coach Hattie was guiding a child naturalist,
Milo, through the cattail marsh. Milo had found a tiny tadpole in a glass jar
with a loose lid and was carrying it carefully toward the pond.

Coach Hattie squinted and boomed, "That tadpole looks like it's going to
suffocate in there!" Milo thought the coach meant the tadpole should be taught
how to coach its own breathing, so he started talking to the jar like it was a
sports team.

Then the jar lid slipped shut. The coach's face went pale, because now the
tadpole really might suffocate. But Milo popped the lid open, the tadpole
flipped into the pond with a silver wink, and the coach laughed so hard the
marsh birds echoed her cackle all the way to dusk.

World model:
---
- A child can carry a tadpole.
- A coach can misunderstand an emergency and overreact.
- A closed container can make a tadpole unsafe only if it is kept out of water
  or without air.
- A simple fix is opening the lid and returning the tadpole to the pond.

Tall Tale style:
---
The prose leans on big-hearted exaggeration, vivid concrete images, and a
single clear misunderstanding that turns into a quick rescue and a laugh.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    contains: Optional[str] = None
    open: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "coach"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    watery: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    open_when_safe: bool = True
    keeps_air: bool = True
    keeps_water: bool = True
    fix: str = ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def open_container(world: World, container: Entity) -> None:
    container.open = True
    container.meters["air"] = 1.0


def close_container(world: World, container: Entity) -> None:
    container.open = False
    container.meters["air"] = 0.0


def maybe_suffocate(world: World, tadpole: Entity, container: Entity) -> bool:
    if container.open:
        return False
    if world.setting.watery:
        return False
    tadpole.meters["air"] = max(0.0, tadpole.meters.get("air", 1.0) - 1.0)
    if tadpole.meters["air"] <= 0.0:
        tadpole.memes["panic"] = tadpole.memes.get("panic", 0.0) + 1.0
        tadpole.memes["suffocating"] = 1.0
        return True
    return False


def tell(setting: Setting, activity: Activity, hero_name: str, coach_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="boy",
        label=hero_name,
        traits=["little", "careful"],
        memes={"wonder": 1.0},
    ))
    coach = world.add(Entity(
        id=coach_name,
        kind="character",
        type="coach",
        label=f"Coach {coach_name}",
        traits=["booming", "grand"],
        memes={"worry": 1.0},
    ))
    tadpole = world.add(Entity(
        id="tadpole",
        kind="character",
        type="tadpole",
        label="tadpole",
        phrase="a tiny tadpole",
        owner=hero.id,
        caretaker=hero.id,
        open=False,
        meters={"air": 1.0, "wet": 1.0},
        memes={"trust": 1.0},
    ))
    jar = world.add(Entity(
        id="jar",
        type="container",
        label="glass jar",
        phrase="a glass jar with a loose lid",
        owner=hero.id,
        caretaker=hero.id,
        open=False,
        meters={"air": 1.0, "wet": 1.0},
    ))

    # Act 1
    world.say(
        f"{coach.label} was a tall-talking coach who could spot trouble from a mile "
        f"of mud and moonlight. {hero.id} was a little boy who loved the marsh, "
        f"and one bright morning he found {tadpole.phrase} in {jar.phrase}."
    )
    world.say(
        f"{hero.id} carried the jar with both hands and headed for {world.setting.place}, "
        f"because {activity.gerund} was the kind of adventure that made his eyes shine."
    )

    # Act 2
    world.para()
    world.say(
        f"At the cattails, {coach.label} thundered, '{tadpole.label.capitalize()} will "
        f"{activity.risk}!'"
    )
    coach.memes["misunderstanding"] = 1.0
    coach.memes["alarm"] = 1.0
    hero.memes["misunderstanding"] = 1.0
    world.say(
        f"{hero.id} misunderstood the warning and thought the coach wanted him to "
        f"coach the tadpole about breathing, so he started talking to the jar like it "
        f"was a baseball team with a very tiny catcher."
    )

    close_container(world, jar)
    if maybe_suffocate(world, tadpole, jar):
        coach.memes["fear"] = 1.0
        world.say(
            f"Then the lid clicked shut with a sound as small as a pea and as scary as "
            f"a thunderclap. Now the tadpole really might suffocate."
        )

    # Act 3
    world.para()
    open_container(world, jar)
    tadpole.meters["air"] = 1.0
    tadpole.memes["panic"] = 0.0
    coach.memes["misunderstanding"] = 0.0
    coach.memes["relief"] = 1.0
    world.say(
        f"{hero.id} popped the lid open, and the jar breathed like a tiny storm window. "
        f"The tadpole flipped out in a silver blink and vanished into the pond water."
    )
    world.say(
        f"{coach.label} laughed so hard the reeds shook. 'I meant open the lid, not "
        f"teach the tadpole a lecture!' she boomed, and {hero.id} grinned because the "
        f"marsh had kept its promise: no tadpole was left to suffocate, and the whole "
        f"story ended with a splash big enough to tickle the egrets."
    )

    world.facts.update(
        hero=hero,
        coach=coach,
        tadpole=tadpole,
        jar=jar,
        activity=activity,
        setting=setting,
        resolved=True,
        misunderstanding=True,
    )
    return world


SETTINGS = {
    "marsh": Setting(place="the cattail marsh", affords={"carry_tadpole"}, watery=True),
    "pond": Setting(place="the pond bank", affords={"carry_tadpole"}, watery=True),
    "creek": Setting(place="the creek bend", affords={"carry_tadpole"}, watery=True),
}

ACTIVITIES = {
    "carry_tadpole": Activity(
        id="carry_tadpole",
        verb="carry the tadpole to the pond",
        gerund="carrying the tadpole to the pond",
        rush="rush toward the pond",
        risk="suffocate",
        keyword="tadpole",
        tags={"tadpole", "suffocate", "coach", "misunderstanding"},
    )
}

CONTAINERS = {
    "jar": Container(
        id="jar",
        label="glass jar",
        phrase="a glass jar with a loose lid",
        open_when_safe=True,
        keeps_air=True,
        keeps_water=True,
        fix="open the lid",
    ),
    "bucket": Container(
        id="bucket",
        label="tin bucket",
        phrase="a tin bucket with little air holes",
        open_when_safe=True,
        keeps_air=True,
        keeps_water=True,
        fix="leave the top open",
    ),
}

NAMES = ["Milo", "June", "Penny", "Otis", "Wren", "Bram"]
COACH_NAMES = ["Hattie", "Mabel", "Nora", "Clara"]

@dataclass
class StoryParams:
    place: str
    activity: str
    container: str
    name: str
    coach: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, c) for p in SETTINGS for a in ACTIVITIES for c in CONTAINERS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale about a coach, a tadpole, and a misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--name")
    ap.add_argument("--coach")
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
    combos = valid_combos()
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.activity is None or c[1] == args.activity)
                and (args.container is None or c[2] == args.container)]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    place, activity, container = rng.choice(filtered)
    return StoryParams(
        place=place,
        activity=activity,
        container=container,
        name=args.name or rng.choice(NAMES),
        coach=args.coach or rng.choice(COACH_NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child about a coach, a tadpole, and a misunderstanding that includes the word "{f["activity"].keyword}".',
        f"Tell a big-hearted story where {f['coach'].label} worries a tadpole might suffocate, but {f['hero'].id} fixes the problem.",
        f"Write a short story about {f['hero'].id} carrying a tadpole in a jar and a coach mistaking the danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    coach = f["coach"]
    tadpole = f["tadpole"]
    qa = [
        QAItem(
            question=f"Who found the tadpole?",
            answer=f"{hero.id} found the tadpole in a jar while visiting {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {coach.label} worry about?",
            answer=f"{coach.label} worried that the tadpole might suffocate if the jar stayed shut.",
        ),
        QAItem(
            question=f"What was the misunderstanding?",
            answer=f"{hero.id} misunderstood the coach and started talking as if the tadpole needed coaching, when the real problem was the closed lid.",
        ),
        QAItem(
            question=f"How was the problem fixed?",
            answer=f"{hero.id} opened the lid, and the tadpole splashed safely back into the pond water.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The coach laughed with relief, and the tadpole was safe and wet in the pond.",
        ),
    ]
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does suffocate mean?",
            answer="To suffocate means to have too little air to breathe safely.",
        ),
        QAItem(
            question="What is a coach?",
            answer="A coach can be a person who guides or trains someone and gives advice.",
        ),
        QAItem(
            question="What is a tadpole?",
            answer="A tadpole is a young frog. It usually lives in water and has a tail.",
        ),
    ]


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.type == "container":
            bits.append(f"open={e.open}")
        out.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.name, params.coach)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


ASP_RULES = r"""
% A tadpole is at risk when a container is closed.
at_risk(T, C) :- tadpole(T), container(C), contains(C, T), closed(C).

% A compatible fix is to open the container.
has_fix(C) :- container(C), fixable(C).

valid(Place, Activity, Container) :- affords(Place, Activity), has_fix(Container), at_risk(tadpole, Container).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        for a in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        lines.append(asp.fact("contains", cid, "tadpole"))
        lines.append(asp.fact("closed", cid))
        lines.append(asp.fact("fixable", cid))
    lines.append(asp.fact("tadpole", "tadpole"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_sample_list(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = []
        for i, p in enumerate(valid_combos()):
            params = StoryParams(place=p[0], activity=p[1], container=p[2], name=NAMES[i % len(NAMES)], coach=COACH_NAMES[i % len(COACH_NAMES)], seed=base_seed + i)
            samples.append(generate(params))
        return samples
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 20):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    samples = build_sample_list(args)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
