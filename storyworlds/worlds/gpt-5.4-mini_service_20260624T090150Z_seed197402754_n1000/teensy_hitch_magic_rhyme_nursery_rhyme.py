#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld: a teensy hitch in a magical rhyme.

A little singer tries to make a rhyme, but the last line gets snagged by a
teensy hitch. A bit of Magic helps them mend the rhyme, and the song ends with
a bright little flourish.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    can_sing: bool = True
    can_magic: bool = True


@dataclass
class Charm:
    id: str
    label: str
    action: str
    fix: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TinyProblem:
    id: str
    label: str
    kind: str
    snag: str
    risk: str
    area: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        nw = World(self.place)
        nw.entities = {k: asdict(v) for k, v in self.entities.items()}  # placeholder overwritten below
        nw.entities = {k: Entity(**v) for k, v in ((eid, asdict(ent)) for eid, ent in self.entities.items())}
        nw.facts = dict(self.facts)
        nw.paragraphs = [[]]
        nw.fired = set(self.fired)
        return nw


def _r_hitch(world: World) -> list[str]:
    out: list[str] = []
    singer = world.entities.get("singer")
    if not singer:
        return out
    if singer.memes.get("hitch", 0.0) < THRESHOLD:
        return out
    sig = ("hitch",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The rhyme caught on a teensy hitch.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    singer = world.entities.get("singer")
    charm = world.entities.get("charm")
    if not singer or not charm:
        return out
    if singer.memes.get("mended", 0.0) >= THRESHOLD:
        return out
    if singer.memes.get("hope", 0.0) < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    singer.memes["mended"] = 1.0
    singer.memes["joy"] = singer.memes.get("joy", 0.0) + 1.0
    out.append("A little Magic tucked the snag away.")
    return out


CAUSAL_RULES = [_r_hitch, _r_fix]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setup_world(place: Place, problem: TinyProblem, charm: Charm, singer_name: str) -> World:
    world = World(place)
    singer = world.add(Entity(id="singer", kind="character", type="child", label=singer_name))
    hitch = world.add(Entity(id="hitch", label=problem.label, type=problem.kind))
    magic = world.add(Entity(id="charm", label=charm.label, type="magic"))
    world.facts.update(singer=singer, hitch=hitch, charm=magic, problem=problem, charm_def=charm)
    return world


def tell(place: Place, problem: TinyProblem, charm: Charm, singer_name: str = "Mina") -> World:
    world = setup_world(place, problem, charm, singer_name)
    singer = world.get("singer")
    hitch = world.get("hitch")

    world.say(f"{singer.label_word if hasattr(singer, 'label_word') else singer.label} loved to sing a nursery rhyme.")
    world.say(f"One teensy morning, {singer.label} tried to sing at {place.name}.")
    world.say(f"But a {hitch.label} made the last word go all wrong.")
    singer.memes["hitch"] = 1.0
    singer.memes["hope"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(f"{singer.label} held up the {charm.label} and whispered a soft little rhyme.")
    singer.memes["hope"] = 2.0
    world.say(f"The {charm.action} {charm.sparkle}.")
    propagate(world, narrate=True)
    world.para()
    if singer.memes.get("mended", 0.0) >= THRESHOLD:
        world.say(f"So the rhyme came back neat and sweet, and {singer.label} sang it clear to the end.")
        world.say(f"The little {problem.kind} was gone, and the song ended with a merry ring.")
    else:
        world.say(f"The rhyme stayed stuck, and the song fell quiet.")
    return world


PLACE_REGISTRY = {
    "garden": Place(name="the garden"),
    "porch": Place(name="the porch"),
    "meadow": Place(name="the meadow"),
}

PROBLEM_REGISTRY = {
    "stumble": TinyProblem(
        id="stumble",
        label="teensy stumble",
        kind="hitch",
        snag="trip the tune",
        risk="lose the beat",
        area="line",
        tags={"teensy", "hitch"},
    ),
    "tangle": TinyProblem(
        id="tangle",
        label="teensy tangle",
        kind="hitch",
        snag="snip the rhyme",
        risk="lose the verse",
        area="line",
        tags={"teensy", "hitch"},
    ),
}

CHARM_REGISTRY = {
    "glow": Charm(
        id="glow",
        label="Magic Glow",
        action="glowed low and kind",
        fix="mend the rhyme",
        sparkle="shimmered like a candle in the dusk",
        tags={"Magic", "Rhyme"},
    ),
    "bell": Charm(
        id="bell",
        label="Magic Bell",
        action="tingled with a bright note",
        fix="smooth the words",
        sparkle="rang like a silver spoon",
        tags={"Magic", "Rhyme"},
    ),
}

SINGER_NAMES = ["Mina", "Pippa", "Lulu", "Nell", "Toby", "Bea"]


@dataclass
class StoryParams:
    place: str
    problem: str
    charm: str
    name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, pr, c) for p in PLACE_REGISTRY for pr in PROBLEM_REGISTRY for c in CHARM_REGISTRY]


def explain_rejection() -> str:
    return "(No story: this little world only allows a teensy hitch and a Magic charm that can mend a rhyme.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld with a teensy hitch and Magic.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--problem", choices=PROBLEM_REGISTRY)
    ap.add_argument("--charm", choices=CHARM_REGISTRY)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError(explain_rejection())
    place, problem, charm = rng.choice(combos)
    name = args.name or rng.choice(SINGER_NAMES)
    return StoryParams(place=place, problem=problem, charm=charm, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about a teensy hitch and a little Magic fix.',
        f"Tell a gentle rhyme story where {f['singer'].label} sings at {world.place.name} and a teensy hitch snags the tune.",
        f"Write a child-friendly story that includes the words 'teensy', 'hitch', 'Magic', and 'Rhyme'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    singer = f["singer"].label
    place = world.place.name
    charm = f["charm_def"].label
    return [
        QAItem(
            question=f"Who was singing at {place}?",
            answer=f"{singer} was singing a nursery rhyme at {place}.",
        ),
        QAItem(
            question="What made the rhyme go wrong at first?",
            answer=f"A teensy hitch made the last word go wrong and snagged the rhyme.",
        ),
        QAItem(
            question=f"What helped the singer mend the rhyme?",
            answer=f"The {charm} helped by bringing a little Magic to smooth the words back into place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something wonderful can happen that feels a little wondrous or surprising.",
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACE_REGISTRY[params.place],
        PROBLEM_REGISTRY[params.problem],
        CHARM_REGISTRY[params.charm],
        params.name,
    )
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
    StoryParams(place="garden", problem="stumble", charm="glow", name="Mina"),
    StoryParams(place="porch", problem="tangle", charm="bell", name="Pippa"),
]


ASP_RULES = r"""
% The world has a tiny hitch when the problem is present.
hitch(P) :- problem(P).

% Magic can fix a hitch.
fixed :- hitch(P), charm(C), magic(C).

#show hitch/1.
#show fixed/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for p in PROBLEM_REGISTRY:
        lines.append(asp.fact("problem", p))
        lines.append(asp.fact("hitch_kind", p, "teensy"))
    for c in CHARM_REGISTRY:
        lines.append(asp.fact("charm", c))
        lines.append(asp.fact("magic", c))
        lines.append(asp.fact("rhyme", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show hitch/1.\n#show fixed/0."))
    clingo_hitch = set(asp.atoms(model, "hitch"))
    clingo_fixed = bool(asp.atoms(model, "fixed"))
    py_hitch = {(p,) for p in PROBLEM_REGISTRY}
    py_fixed = True
    if clingo_hitch == py_hitch and clingo_fixed == py_fixed:
        print(f"OK: clingo gate matches Python gate ({len(py_hitch)} hitches).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show hitch/1.\n#show fixed/0."))
    return sorted(set(asp.atoms(model, "hitch")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hitch/1.\n#show fixed/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(PROBLEM_REGISTRY)} hitch kinds, {len(CHARM_REGISTRY)} magic charms.")
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
