#!/usr/bin/env python3
"""
Storyworld: cue / ark / negotiate / lesson learned / fairy tale.

A small, self-contained story simulation in a fairy-tale style:
- A young character notices a cue that something delicate needs help.
- They find or build an ark-like solution to keep something safe.
- They negotiate with a helper or guardian to reach a fair plan.
- The ending explicitly shows the lesson learned.

The world is intentionally tiny and constraint-checked: the cue must be
believable, the ark must fit the protected thing, and the negotiation must
resolve the problem in a way that changes the simulated state.
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


# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

PLACES = {
    "meadow": {
        "place": "the meadow",
        "weather": "cloudy",
        "risk": "flood",
        "cue": "dark water at the path",
        "gives": "the brook began to swell after the rain",
    },
    "riverbank": {
        "place": "the riverbank",
        "weather": "rainy",
        "risk": "flood",
        "cue": "muddy water licking the reeds",
        "gives": "the river rose up and spilled over the stones",
    },
    "orchard": {
        "place": "the orchard",
        "weather": "windy",
        "risk": "storm",
        "cue": "branches bowing under the wind",
        "gives": "the wind grew stronger and shook the apple boughs",
    },
}

PRECIOUS_THINGS = {
    "duckling": {
        "label": "duckling",
        "phrase": "a tiny duckling",
        "place": "pond",
        "size": "small",
        "needs": {"dry", "safe"},
        "at_risk": "water",
    },
    "book": {
        "label": "book",
        "phrase": "an old storybook",
        "place": "table",
        "size": "small",
        "needs": {"dry", "safe"},
        "at_risk": "water",
    },
    "lantern": {
        "label": "lantern",
        "phrase": "a little lantern with a gold handle",
        "place": "shelf",
        "size": "small",
        "needs": {"safe"},
        "at_risk": "storm",
    },
}

GUARDIANS = {
    "grandmother": {"label": "grandmother", "kind": "elder"},
    "gardener": {"label": "gardener", "kind": "helper"},
    "fisherman": {"label": "fisherman", "kind": "helper"},
}

LESSONS = [
    "it was wiser to ask than to rush",
    "a kind plan could keep everyone safe",
    "listening to a warning could save the day",
    "a fair bargain could turn worry into help",
]

NAMES = ["Mina", "Toby", "Lena", "Pip", "Nia", "Owen", "Suri", "Jasper"]
TRAITS = ["brave", "curious", "gentle", "patient", "earnest", "kind"]


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    protected_by: Optional[str] = None
    in_ark: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "fisherman"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    key: str
    place: str
    weather: str
    risk: str
    cue: str
    gives: str


@dataclass
class Thing:
    key: str
    label: str
    phrase: str
    place: str
    size: str
    needs: set[str]
    at_risk: str


@dataclass
class StoryParams:
    place: str
    thing: str
    guardian: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place, thing: Thing, guardian: str) -> None:
        self.place = place
        self.thing = thing
        self.guardian = guardian
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        c = World(self.place, self.thing, self.guardian)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


# ---------------------------------------------------------------------------
# Arithmetic / causal helpers
# ---------------------------------------------------------------------------
def cue_is_believable(place: Place, thing: Thing) -> bool:
    return place.risk == thing.at_risk


def choose_ark(thing: Thing) -> dict[str, object]:
    if thing.key in {"duckling", "book", "lantern"}:
        return {
            "label": "a little ark",
            "phrase": "a little wooden ark",
            "covers": {"dry", "safe"},
            "fits": thing.size == "small",
        }
    return {"label": "an ark", "phrase": "an ark", "covers": {"safe"}, "fits": False}


def reasonableness_gate(place: Place, thing: Thing) -> bool:
    return cue_is_believable(place, thing) and choose_ark(thing)["fits"]


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def intro(world: World, child: Entity) -> None:
    world.say(
        f"Once upon a time, there was a little {child.memes.get('trait_word', 'kind')} "
        f"{child.type} named {child.id}."
    )
    world.say(
        f"{child.pronoun().capitalize()} lived near {world.place.place} and watched the "
        f"days with bright eyes."
    )


def desire(world: World, child: Entity, thing: Entity) -> None:
    child.memes["love"] = child.memes.get("love", 0) + 1
    world.say(
        f"{child.id} loved {thing.phrase} and wanted to keep {thing.pronoun('object')} safe."
    )


def cue_event(world: World, child: Entity) -> None:
    world.say(
        f"Then came a cue: {world.place.cue}."
    )
    world.say(
        f"{child.id} saw it at once and knew something precious might soon be in danger."
    )


def worry(world: World, guardian: Entity, thing: Entity) -> None:
    guardian.memes["worry"] = guardian.memes.get("worry", 0) + 1
    world.say(
        f"{guardian.id} frowned and said, "
        f'"If the {world.place.risk} comes, the {thing.label} could be lost."'
    )


def negotiate(world: World, child: Entity, guardian: Entity, thing: Entity) -> None:
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(
        f"{child.id} did not argue. {child.pronoun().capitalize()} chose to negotiate instead."
    )
    world.say(
        f'"What if we build an ark?" {child.pronoun()} asked. "Then the {thing.label} can stay dry and safe."'
    )
    world.say(
        f"{guardian.id} thought about it, then nodded. "
        f'"That is a fair plan, as long as you help carry it."'
    )
    child.memes["determination"] = child.memes.get("determination", 0) + 1
    guardian.memes["trust"] = guardian.memes.get("trust", 0) + 1


def build_ark(world: World, child: Entity, thing: Entity) -> Entity:
    ark_info = choose_ark(world.thing)
    ark = world.add(Entity(
        id="ark",
        kind="thing",
        type="ark",
        label="ark",
        phrase=ark_info["phrase"],
        owner=child.id,
        protected_by=child.id,
        in_ark=True,
    ))
    thing.in_ark = True
    thing.protected_by = ark.id
    world.say(
        f"So {child.id} found smooth boards and built {ark_info['phrase']} with a snug lid."
    )
    world.say(
        f"They placed the {thing.label} inside, and the little ark held it close like a nest."
    )
    return ark


def turn(world: World) -> None:
    world.say(world.place.gives)
    world.say(
        f"But the {world.place.risk} could not reach the {world.thing.label}, because it was already in the ark."
    )


def lesson(world: World, child: Entity, guardian: Entity) -> None:
    world.say(
        f"In the end, {child.id} learned that {random.choice(LESSONS)}."
    )
    world.say(
        f"{guardian.id} smiled, and the two of them watched the little ark drift gently where it was safe."
    )


# ---------------------------------------------------------------------------
# World construction
# ---------------------------------------------------------------------------
def tell(place: Place, thing: Thing, guardian_name: str, child_name: str, trait: str) -> World:
    world = World(place, thing, guardian_name)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type="girl" if child_name in {"Mina", "Lena", "Nia", "Suri"} else "boy",
        memes={"trait_word": trait},
    ))
    guardian = world.add(Entity(
        id=guardian_name,
        kind="character",
        type=guardian_name,
        label=guardian_name,
    ))
    precious = world.add(Entity(
        id=thing.key,
        kind="thing",
        type=thing.key,
        label=thing.label,
        phrase=thing.phrase,
        owner=child.id,
    ))

    intro(world, child)
    world.para()
    desire(world, child, precious)
    cue_event(world, child)
    worry(world, guardian, precious)
    negotiate(world, child, guardian, precious)
    ark = build_ark(world, child, precious)
    world.para()
    turn(world)
    lesson(world, child, guardian)

    world.facts.update(
        child=child,
        guardian=guardian,
        thing=precious,
        ark=ark,
        place=place,
        cue=place.cue,
        risk=place.risk,
        lesson="lesson learned",
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES_REGISTRY = {k: Place(key=k, **v) for k, v in PLACES.items()}
THINGS_REGISTRY = {k: Thing(key=k, **v) for k, v in PRECIOUS_THINGS.items()}
GUARDIANS_REGISTRY = {k: v for k, v in GUARDIANS.items()}


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    thing = f["thing"]
    guardian = f["guardian"]
    place = f["place"]
    return [
        f'Write a short fairy tale for a young child about a cue, an ark, and a negotiation at {place.place}.',
        f"Tell a gentle story where {child.id} notices {place.cue}, negotiates with {guardian.id}, and protects {thing.phrase} in an ark.",
        f'Write a tiny fairy tale that includes the words "cue", "ark", and "negotiate", and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    thing: Entity = f["thing"]
    place: Place = f["place"]
    qa = [
        QAItem(
            question=f"What cue did {child.id} notice near {place.place}?",
            answer=f"{child.id} noticed {place.cue}, and that was the cue that something might need protecting.",
        ),
        QAItem(
            question=f"Why did {child.id} want to build an ark?",
            answer=f"{child.id} wanted to build an ark because {thing.phrase} could be harmed if the {place.risk} arrived.",
        ),
        QAItem(
            question=f"How did {child.id} and {guardian.id} solve the problem?",
            answer=f"They negotiated a fair plan: they built a little ark and placed {thing.phrase} inside it so it could stay safe.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn in the end?",
            answer="The story ended with a lesson learned: a fair plan and kind words can turn worry into help.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an ark in a fairy tale?",
            answer="In a fairy tale, an ark is a protective boat or box that carries something safe through danger.",
        ),
        QAItem(
            question="What does it mean to negotiate?",
            answer="To negotiate means to talk calmly and reach a fair plan that both sides can accept.",
        ),
        QAItem(
            question="What is a cue?",
            answer="A cue is a sign that tells someone something important is about to happen or needs attention.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A cue is believable when the place's danger matches the thing's vulnerability.
believable(P,T) :- risk(P,R), at_risk(T,R).

% An ark is suitable when it fits the thing and offers the needed protection.
suitable_ark(A,T) :- ark(A), fits(A,T), protects(A,dry), protects(A,safe).

% The negotiation succeeds only when there is a believable cue and a suitable ark.
can_resolve(P,T) :- believable(P,T), suitable_ark(a1,T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("risk", pid, p["risk"]))
    for tid, t in PRECIOUS_THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("at_risk", tid, t["at_risk"]))
        lines.append(asp.fact("size", tid, t["size"]))
        if t["size"] == "small":
            lines.append(asp.fact("fits", "a1", tid))
    lines.append(asp.fact("ark", "a1"))
    lines.append(asp.fact("protects", "a1", "dry"))
    lines.append(asp.fact("protects", "a1", "safe"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_resolve/2."))
    return sorted(set(asp.atoms(model, "can_resolve")))


def asp_valid_combos() -> list[tuple]:
    return [(p, t) for p in PLACES_REGISTRY for t in THINGS_REGISTRY if cue_is_believable(PLACES_REGISTRY[p], THINGS_REGISTRY[t]) and choose_ark(THINGS_REGISTRY[t])["fits"]]


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_stories())
    python_set = set(asp_valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# StoryWorld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about cue, ark, negotiate, and lesson learned.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--thing", choices=PRECIOUS_THINGS)
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = []
    for place_key, place in PLACES_REGISTRY.items():
        for thing_key, thing in THINGS_REGISTRY.items():
            if not reasonableness_gate(place, thing):
                continue
            combos.append((place_key, thing_key))
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.thing:
        combos = [c for c in combos if c[1] == args.thing]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, thing = rng.choice(sorted(combos))
    guardian = args.guardian or rng.choice(list(GUARDIANS_REGISTRY))
    name = args.name or rng.choice(NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, thing=thing, guardian=guardian, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    place = PLACES_REGISTRY[params.place]
    thing = THINGS_REGISTRY[params.thing]
    world = tell(place, thing, params.guardian, params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.in_ark:
            bits.append("in_ark=True")
        if e.protected_by:
            bits.append(f"protected_by={e.protected_by}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="meadow", thing="duckling", guardian="grandmother", name="Mina", trait="gentle"),
    StoryParams(place="riverbank", thing="book", guardian="fisherman", name="Pip", trait="curious"),
    StoryParams(place="orchard", thing="lantern", guardian="gardener", name="Nia", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_resolve/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:")
        for p, t in stories:
            print(f"  {p:10} {t}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.thing} at {p.place} (guardian: {p.guardian})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
