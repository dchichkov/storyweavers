#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/bowl_robin_mystery_to_solve_myth.py
===============================================================================================================

A small mythic mystery world about a robin, a bowl, and a thing to solve.

Seed tale imagined from the prompt:
A robin in an old grove found a bowl that did not belong to the birds of the
trees. The bowl was not empty: it held a hush of moonlight and a riddle in the
dust at its bottom. The robin wanted to know who had set it there and why the
bowl sang only when the dawn wind touched it. So the robin followed clues
through roots, reeds, and stones, learning that the bowl was meant as an offering
to a river spirit. When the robin returned the bowl to the water's edge, the
mystery was solved, and the grove felt blessed again.

World model:
- A mythic place may hold a bowl, a clue trail, and a mystery.
- The robin can investigate, carry, and return the bowl.
- The bowl may be hidden, found, washed, or placed.
- The mystery resolves when the robin discovers the true owner and the bowl is
  returned to the right shrine or shore.

The story is intentionally compact and state-driven, with a clear turn from
confusion to understanding.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    location: str = ""
    portable: bool = True
    sacred: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "robin":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the grove"
    features: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _all_entities(world: World):
    return list(world.entities.values())


def _r_dust_clue(world: World) -> list[str]:
    out = []
    bowl = world.entities.get("bowl")
    if not bowl:
        return out
    if bowl.meters.get("mystery", 0.0) < THRESHOLD:
        return out
    clue = world.entities.get("clue")
    if clue and clue.meters.get("seen", 0.0) >= THRESHOLD:
        sig = ("dust",)
        if sig not in world.fired:
            world.fired.add(sig)
            bowl.memes["curiosity"] = bowl.memes.get("curiosity", 0.0) + 1
            out.append("A ring of dust around the bowl hinted that it had been set down by careful hands.")
    return out


def _r_returned(world: World) -> list[str]:
    out = []
    bowl = world.entities.get("bowl")
    shrine = world.entities.get("shrine")
    robin = world.entities.get("robin")
    if not bowl or not shrine or not robin:
        return out
    if bowl.location == shrine.location and bowl.keeper == "river_spirit":
        sig = ("returned",)
        if sig not in world.fired:
            world.fired.add(sig)
            bowl.meters["rest"] = bowl.meters.get("rest", 0.0) + 1
            robin.memes["peace"] = robin.memes.get("peace", 0.0) + 1
            out.append("The bowl settled beside the water, as if it had remembered its own name.")
    return out


CAUSAL_RULES = [_r_dust_clue, _r_returned]


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


@dataclass
class StoryParams:
    place: str
    bowl_kind: str
    keeper: str
    hero_name: str
    seed: Optional[int] = None


SETTINGS = {
    "grove": Setting(place="the grove", features={"trees", "roots", "moon"}),
    "shore": Setting(place="the shore", features={"water", "shells", "wind"}),
    "ruin": Setting(place="the ruin", features={"stones", "echoes", "moss"}),
}

BOWL_KINDS = {
    "bronze": ("a bronze bowl", "bronze bowl"),
    "wood": ("a carved wooden bowl", "wooden bowl"),
    "silver": ("a silver bowl", "silver bowl"),
}

KEEPERS = {
    "river_spirit": "river spirit",
    "moon_mother": "moon mother",
    "elder": "old grove elder",
}

NAMES = ["Robin", "Pip", "Aster", "Lark", "Mira", "Rowan", "Tavi"]
FEATURE_WORDS = ["moon", "roots", "river", "wind", "moss", "stone"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic mystery storyworld: a robin, a bowl, and a thing to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--bowl-kind", choices=BOWL_KINDS)
    ap.add_argument("--keeper", choices=KEEPERS)
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


def _valid_combo(place: str, bowl_kind: str, keeper: str) -> bool:
    if place == "shore" and keeper != "river_spirit":
        return False
    if place == "grove" and keeper == "river_spirit":
        return False
    if bowl_kind == "silver" and place == "ruin":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for bowl_kind in BOWL_KINDS:
            for keeper in KEEPERS:
                if _valid_combo(place, bowl_kind, keeper):
                    out.append((place, bowl_kind, keeper))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.bowl_kind is None or c[1] == args.bowl_kind)
              and (args.keeper is None or c[2] == args.keeper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, bowl_kind, keeper = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, bowl_kind=bowl_kind, keeper=keeper, hero_name=name)


def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    robin = world.add(Entity(id="robin", kind="character", type="robin", label=params.hero_name))
    bowl_phrase, bowl_label = BOWL_KINDS[params.bowl_kind]
    bowl = world.add(Entity(
        id="bowl",
        type="bowl",
        label=bowl_label,
        phrase=bowl_phrase,
        owner=params.keeper,
        keeper=params.keeper,
        location=params.place,
        portable=True,
        sacred=True,
    ))
    shrine = world.add(Entity(
        id="shrine",
        type="shrine",
        label="a little shrine",
        phrase="a little shrine of stones",
        location=params.place,
        sacred=True,
        portable=False,
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label="a dust clue",
        phrase="a dust clue",
        location=params.place,
        portable=False,
    ))
    bowl.meters["mystery"] = 1.0
    clue.meters["seen"] = 0.0
    world.facts.update(robin=robin, bowl=bowl, shrine=shrine, clue=clue, params=params)
    return world


def tell_story(world: World) -> World:
    robin = world.get("robin")
    bowl = world.get("bowl")
    shrine = world.get("shrine")
    clue = world.get("clue")

    world.say(f"In {world.setting.place}, {robin.label} the robin found {bowl.phrase} beneath the trees.")
    world.say(f"The bowl seemed wrong there, yet it gleamed like a small moon caught on the earth.")

    world.para()
    world.say(f"{robin.label} watched the dust around it and noticed a faint trail toward {shrine.label}.")
    clue.meters["seen"] = 1.0
    robin.memes["wonder"] = robin.memes.get("wonder", 0.0) + 1
    bowl.meters["mystery"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then {robin.label} followed the trail through roots and reeds until the answer became clear.")
    world.say(f"The bowl had been left as an offering to the {KEEPERS[world.facts['params'].keeper]}.")
    bowl.keeper = world.facts["params"].keeper

    if world.facts["params"].keeper == "river_spirit":
        bowl.location = world.setting.place
    else:
        bowl.location = shrine.location

    propagate(world, narrate=True)

    world.para()
    world.say(f"{robin.label} carried the bowl to the right place and set it down gently.")
    world.say(f"The mystery was solved, and the grove felt quiet and blessed again.")
    robin.memes["peace"] = robin.memes.get("peace", 0.0) + 1
    bowl.meters["mystery"] = 0.0
    bowl.meters["rest"] = bowl.meters.get("rest", 0.0) + 1
    world.facts["solved"] = True
    world.facts["returned"] = True
    world.facts["keeper_name"] = KEEPERS[world.facts["params"].keeper]
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short mythic mystery story for a child about a robin who finds a {p.bowl_kind} bowl and must solve who it belongs to.',
        f"Tell a gentle legend where {p.hero_name} the robin follows clues and returns a bowl to the {KEEPERS[p.keeper]}.",
        f'Write a simple myth-style story using the words "bowl" and "robin" with a solved mystery at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    robin = world.facts["robin"]
    bowl = world.facts["bowl"]
    keeper_name = KEEPERS[p.keeper]
    place = SETTINGS[p.place].place
    return [
        QAItem(
            question=f"What did {robin.label} find in {place}?",
            answer=f"{robin.label} found {bowl.phrase} hidden there, shining like a little moon.",
        ),
        QAItem(
            question=f"What clue helped {robin.label} solve the mystery?",
            answer="A ring of dust and a trail leading toward the shrine helped the robin understand where the bowl belonged.",
        ),
        QAItem(
            question=f"Who did the bowl belong to in the end?",
            answer=f"It belonged to the {keeper_name}, so the robin returned it to the right place.",
        ),
        QAItem(
            question=f"How did the story end after the mystery was solved?",
            answer="The bowl was set down gently, and the place felt quiet and blessed again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a robin?",
            answer="A robin is a small bird with a cheerful song, often seen hopping on the ground and looking for worms.",
        ),
        QAItem(
            question="What is a bowl for?",
            answer="A bowl is a round container used to hold food, water, or small treasures.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a thing that is not yet understood and needs clues to solve it.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to gather the clues and find the true answer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.keeper:
            bits.append(f"keeper={e.keeper}")
        if e.location:
            bits.append(f"location={e.location}")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="grove", bowl_kind="bronze", keeper="elder", hero_name="Robin"),
    StoryParams(place="shore", bowl_kind="wood", keeper="river_spirit", hero_name="Pip"),
    StoryParams(place="ruin", bowl_kind="bronze", keeper="moon_mother", hero_name="Lark"),
]


ASP_RULES = r"""
% A bowl is mysterious until the robin notices clues and returns it.
mysterious(bowl) :- bowl(B), not solved(B).

clue_seen(B) :- bowl(B), clue(C), seen(C).
solved(B) :- bowl(B), clue_seen(B), returned(B).

compatible(P, K) :- place(P), keeper(K), not bad_pair(P, K).

% The shore is the river spirit's place; the grove is not.
bad_pair(grove, river_spirit).
bad_pair(shore, moon_mother).
bad_pair(shore, elder).

valid_story(P, B, K) :- compatible(P, K), bowl_kind(B), place(P).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for bk in BOWL_KINDS:
        lines.append(asp.fact("bowl_kind", bk))
    for k in KEEPERS:
        lines.append(asp.fact("keeper", k))
    lines.append(asp.fact("seen", "clue"))
    lines.append(asp.fact("returned", "bowl"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [(p, b, k) for p, b, k in valid_combos()]


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set((p, b, k) for p, b, k in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        sample = generate(resolve_params(argparse.Namespace(place=None, bowl_kind=None, keeper=None, name=None), random.Random(1)))
        if not sample.story.strip():
            print("ERROR: empty story")
            return 1
        print("OK: generated story is non-empty.")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_setup_world(params))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: bowl={p.bowl_kind}, place={p.place}, keeper={p.keeper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
