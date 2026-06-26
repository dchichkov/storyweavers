#!/usr/bin/env python3
"""
Storyworld: nana, tangle, contrary, with a comic happy-ending / bad-ending split.

This world models a little comedy about a child who keeps being contrary while
helping Nana untangle something knotted. The state changes are physical
(tangled string, dropped cookies, slipped knitting) and emotional (contrary
mood, Nana's patience, shared laughter). A happy ending is possible when the
child chooses to help; a bad ending is possible when the child keeps arguing
and the mess stays messy.

The story is generated from a small simulated world. The same world model can
produce either a cheerful resolution or a comic flop depending on the sampled
ending mode.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "nana", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    setting: str
    object_kind: str
    ending: str
    name: str
    child_type: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    indoor: bool
    afford: set[str] = field(default_factory=set)


@dataclass
class TangleThing:
    id: str
    label: str
    phrase: str
    mess_key: str
    knot_key: str
    comic_risk: str
    untangle_tool: str
    location: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, afford={"yarn", "cookie_dough"}),
    "living_room": Setting(place="the living room", indoor=True, afford={"yarn", "sock"}),
    "porch": Setting(place="the porch", indoor=False, afford={"yarn", "ribbon"}),
}

THINGS = {
    "yarn": TangleThing(
        id="yarn",
        label="a ball of yarn",
        phrase="a bright ball of yarn",
        mess_key="tangle",
        knot_key="knotted",
        comic_risk="roll under the couch",
        untangle_tool="a smooth spoon",
        location="on the chair",
        tags={"yarn", "tangle"},
    ),
    "cookie_dough": TangleThing(
        id="cookie_dough",
        label="cookie dough",
        phrase="a sticky bowl of cookie dough",
        mess_key="sticky",
        knot_key="clumped",
        comic_risk="stick to everything",
        untangle_tool="floured hands",
        location="by the oven",
        tags={"cookie", "sticky"},
    ),
    "sock": TangleThing(
        id="sock",
        label="a long sock",
        phrase="a long striped sock with a missing pair",
        mess_key="tangle",
        knot_key="twisted",
        comic_risk="hide under the laundry basket",
        untangle_tool="careful fingers",
        location="near the basket",
        tags={"sock", "tangle"},
    ),
    "ribbon": TangleThing(
        id="ribbon",
        label="a party ribbon",
        phrase="a shiny party ribbon",
        mess_key="tangle",
        knot_key="looped",
        comic_risk="wrap around a lamp",
        untangle_tool="gentle pulls",
        location="on a shelf",
        tags={"ribbon", "tangle"},
    ),
}


def _introduce(world: World, child: Entity, nana: Entity, thing: TangleThing) -> None:
    world.say(
        f"{child.id} was a little contrary {child.type} who liked to answer every plan with, "
        f'"Nope, not that way."'
    )
    world.say(
        f"Nana lived with {child.id} in {world.setting.place}, and one day they found {thing.phrase} {thing.location}."
    )


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.child_type,
        label=params.name,
        meters={"hunger": 0.0},
        memes={"contrary": 1.0, "joy": 0.0, "mischief": 0.0, "patience": 0.0},
    ))
    nana = world.add(Entity(
        id="Nana",
        kind="character",
        type="nana",
        label="Nana",
        meters={"work": 0.0},
        memes={"patience": 1.0, "love": 2.0, "laughing": 0.0},
    ))
    thing = THINGS[params.object_kind]
    bundle = world.add(Entity(
        id=thing.id,
        kind="thing",
        type=thing.label,
        label=thing.label,
        plural=False,
        owner="Nana",
        meters={"tangle": 1.0 if thing.mess_key == "tangle" else 0.0,
                "sticky": 1.0 if thing.mess_key == "sticky" else 0.0},
    ))
    world.facts.update(child=child, nana=nana, thing=thing, bundle=bundle, params=params)
    return world


def _comic_problem(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    nana: Entity = f["nana"]
    thing: TangleThing = f["thing"]
    bundle: Entity = f["bundle"]

    world.say(
        f"Nana sighed and asked {child.id} to help with the {thing.label}, because it had gone {thing.knot_key} in the funniest possible way."
    )
    child.memes["contrary"] += 1
    world.say(
        f"But {child.id} crossed {child.pronoun('possessive')} arms and said, "
        f'"No, I think it should stay {thing.knot_key} forever."'
    )
    bundle.meters[thing.mess_key] = bundle.meters.get(thing.mess_key, 0.0) + 1.0
    nana.meters["work"] += 1.0
    world.say(
        f"That made Nana stare at the {thing.label}, then at {child.id}, as if the knot had just told a joke."
    )


def _happy_turn(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    nana: Entity = f["nana"]
    thing: TangleThing = f["thing"]
    bundle: Entity = f["bundle"]

    world.say(
        f"Then {child.id} tried one tiny pull, and the {thing.label} gave a soft little pop, like a startled popcorn kernel."
    )
    bundle.meters[thing.mess_key] = 0.0
    child.memes["joy"] += 1.0
    child.memes["contrary"] = 0.0
    nana.memes["patience"] += 1.0
    nana.memes["laughing"] += 1.0
    world.say(
        f"{child.id} laughed, because {thing.untangle_tool} was not needed after all; the knot had loosened from patience alone."
    )
    world.say(
        f"Nana smiled so hard that her cheeks looked round as dumplings, and together they set the {thing.label} neatly in a basket."
    )


def _bad_turn(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    nana: Entity = f["nana"]
    thing: TangleThing = f["thing"]
    bundle: Entity = f["bundle"]

    world.say(
        f"{child.id} kept saying the opposite of every idea, so the {thing.label} only got more {thing.knot_key}."
    )
    child.memes["mischief"] += 1.0
    child.memes["contrary"] += 1.0
    bundle.meters[thing.mess_key] += 1.0
    nana.meters["work"] += 1.0
    world.say(
        f"Nana tried to help anyway, but the {thing.label} did exactly what a stubborn tangle likes to do: it made a bigger tangle."
    )
    world.say(
        f"In the end Nana still loved {child.id}, but the basket stayed messy, and the room looked like a noodle factory had sneezed."
    )


def _ending_image(world: World, happy: bool) -> None:
    f = world.facts
    child: Entity = f["child"]
    nana: Entity = f["nana"]
    thing: TangleThing = f["thing"]
    if happy:
        world.say(
            f"By supper time, {thing.label} was smooth, Nana was chuckling, and {child.id} was no longer being contrary at all."
        )
    else:
        world.say(
            f"By supper time, {thing.label} was still knotty, Nana was tired, and {child.id} had learned that being contrary can tangle a whole afternoon."
        )


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    f = world.facts
    child: Entity = f["child"]
    nana: Entity = f["nana"]
    thing: TangleThing = f["thing"]

    _introduce(world, child, nana, thing)
    world.para()

    world.say(f"The day was quiet, and {thing.label} was the sort of thing that begged to {thing.comic_risk}.")
    world.say(
        f"Nana wanted to fix it, because she had promised a neat afternoon and a cookie afterward."
    )
    _comic_problem(world)
    world.para()

    if params.ending == "happy":
        _happy_turn(world)
    else:
        _bad_turn(world)
    world.para()
    _ending_image(world, params.ending == "happy")
    world.facts["happy"] = params.ending == "happy"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]
    thing: TangleThing = f["thing"]
    return [
        f'Write a short comedy story for a child about Nana, a contrary little helper, and {thing.label}.',
        f"Tell a funny story where {params.name} keeps being contrary while Nana tries to untangle {thing.phrase}.",
        f'Write a gentle comic story that includes the words "nana", "tangle", and "contrary", and ends with a clear ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]
    child: Entity = f["child"]
    thing: TangleThing = f["thing"]
    happy = f["happy"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {params.name}, a contrary little {child.type}, and Nana trying to deal with {thing.label}.",
        ),
        QAItem(
            question=f"What was wrong with {thing.label} at the start?",
            answer=f"It had gone {thing.knot_key}, so Nana had to figure out how to untangle it.",
        ),
        QAItem(
            question=f"Why did Nana want to fix it?",
            answer="She wanted a neat afternoon and a calmer room, plus she was expecting a cookie afterward.",
        ),
    ]
    if happy:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended happily: {thing.label} became smooth, and {params.name} stopped being contrary.",
        ))
    else:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the tangle stayed messy, and {params.name} kept being contrary.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tangle?",
            answer="A tangle is a knotty mess where strings, ribbons, or hair get twisted together.",
        ),
        QAItem(
            question="What does contrary mean?",
            answer="Contrary means always wanting to do the opposite of what someone suggests.",
        ),
        QAItem(
            question="Why do people smile at comedy?",
            answer="Comedy is funny, so people smile or laugh when something silly happens and nobody gets hurt.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  happy ending: {world.facts.get('happy')}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("affords", sid, a))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("knotty", tid, thing.knot_key))
        lines.append(asp.fact("mess", tid, thing.mess_key))
        lines.append(asp.fact("can_untangle", tid, thing.untangle_tool))
        for tag in sorted(thing.tags):
            lines.append(asp.fact("tag", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(T) :- thing(T), knotty(T,_).
good_ending(T) :- at_risk(T), can_untangle(T,_).
bad_ending(T) :- at_risk(T), not good_ending(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comic story world: Nana, a tangle, and a contrary child.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object-kind", choices=THINGS)
    ap.add_argument("--ending", choices=["happy", "bad"])
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    object_kind = args.object_kind or rng.choice(sorted(SETTINGS[setting].afford))
    ending = args.ending or rng.choice(["happy", "bad"])
    child_type = args.child_type or rng.choice(["girl", "boy"])
    name_pool = ["Mia", "Leo", "Nina", "Owen", "Ada", "Milo", "Ruby", "Theo"]
    name = args.name or rng.choice(name_pool)
    return StoryParams(setting=setting, object_kind=object_kind, ending=ending, name=name, child_type=child_type)


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


def asp_valid_endings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_ending/1.\n#show bad_ending/1."))
    goods = set(asp.atoms(model, "good_ending"))
    bads = set(asp.atoms(model, "bad_ending"))
    return sorted(goods | bads)


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_ending/1.\n#show bad_ending/1."))
    atoms = set((a.name, tuple(x.name if x.type == x.SymbolType.Function else getattr(x, 'name', str(x)) for x in a.arguments)) for a in model)
    if atoms:
        print("OK: ASP program solves and emits ending atoms.")
        return 0
    print("MISMATCH: ASP program returned no shown atoms.")
    return 1


CURATED = [
    StoryParams(setting="kitchen", object_kind="yarn", ending="happy", name="Mia", child_type="girl"),
    StoryParams(setting="living_room", object_kind="sock", ending="bad", name="Leo", child_type="boy"),
    StoryParams(setting="porch", object_kind="ribbon", ending="happy", name="Nina", child_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_ending/1.\n#show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show good_ending/1.\n#show bad_ending/1."))
        print("ASP ending atoms:")
        for a in model:
            print(a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
