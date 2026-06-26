#!/usr/bin/env python3
"""
storyworlds/worlds/sliver_discover_friendship_cautionary_slice_of_life.py
========================================================================

A small slice-of-life story world about friendship, a discovered sliver, and a
careful choice that keeps somebody safe.

The premise:
- Two friends are enjoying an ordinary day in a cozy neighborhood setting.
- One of them discovers a tiny sliver that could cause a hurt if nobody notices.
- They must choose between ignoring it or being cautious and helpful.
- The story resolves through friendship, careful action, and a small kind fix.

The world model tracks:
- physical meters: risk, sharpness, cleanliness, comfort, time_spent
- emotional memes: curiosity, caution, trust, relief, gratitude

This file is standalone and uses only the stdlib plus the shared storyworld
results container; the ASP helper is imported lazily only in ASP modes.
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
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def reflexive(self) -> str:
        if self.plural:
            return "themselves"
        return {"girl": "herself", "boy": "himself"}.get(self.type, "itself")


@dataclass
class Place:
    id: str
    label: str
    indoor: bool
    details: str


@dataclass
class Sliver:
    id: str
    label: str
    phrase: str
    source: str
    where: str
    sharp: bool = True
    tiny: bool = True


@dataclass
class StoryParams:
    place: str
    sliver: str
    name: str
    friend: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "playground": Place("playground", "the playground", False, "The afternoon light fell across the benches and sandbox."),
    "kitchen": Place("kitchen", "the kitchen", True, "The room was warm, and the floor was easy to sweep."),
    "porch": Place("porch", "the porch", False, "The porch boards were pale and dry after a quiet morning."),
    "classroom": Place("classroom", "the classroom", True, "The tables were neat, with crayons and paper waiting nearby."),
}

SLIVERS = {
    "wood": Sliver("wood", "a wooden sliver", "a tiny wooden sliver", "a fence board", "on the bench"),
    "glass": Sliver("glass", "a glass sliver", "a tiny glass sliver", "a broken jar", "near the sink"),
    "shell": Sliver("shell", "a shell sliver", "a tiny shell sliver", "a beach bucket", "in the sandbox"),
}

GENDERS = ["girl", "boy"]
TRAITS = ["curious", "gentle", "careful", "bright", "kind", "quiet"]
FRIEND_NAMES = ["Mina", "Iris", "Toby", "Noah", "Lila", "Owen", "Maya", "Finn"]
CAREGIVERS = ["mother", "father", "teacher", "grandparent"]


@dataclass
class StoryState:
    world: World
    child: Entity
    friend: Entity
    caregiver: Entity
    sliver: Entity
    cautioned: bool = False
    fixed: bool = False


def _pron_label(type_name: str) -> str:
    return {"mother": "mom", "father": "dad", "teacher": "teacher", "grandparent": "grandparent"}.get(type_name, type_name)


def _setup_state(params: StoryParams) -> StoryState:
    place = SETTINGS[params.place]
    sliver_def = SLIVERS[params.sliver]
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        owner=None,
        meters={"comfort": 3.0, "risk": 0.0, "time_spent": 0.0},
        memes={"curiosity": 2.0, "caution": 1.0, "trust": 1.0, "relief": 0.0, "gratitude": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type="boy" if params.gender == "girl" else "girl",
        label=params.friend,
        meters={"comfort": 3.0, "risk": 0.0, "time_spent": 0.0},
        memes={"curiosity": 2.0, "caution": 1.0, "trust": 1.0, "relief": 0.0, "gratitude": 0.0},
    ))
    caregiver = world.add(Entity(
        id="caregiver",
        kind="character",
        type=params.caregiver,
        label=_pron_label(params.caregiver),
        meters={"comfort": 4.0, "risk": 0.0, "time_spent": 0.0},
        memes={"caution": 2.0, "trust": 1.0, "relief": 0.0, "gratitude": 0.0},
    ))
    sliver = world.add(Entity(
        id=sliver_def.id,
        kind="thing",
        type=sliver_def.id,
        label=sliver_def.label,
        phrase=sliver_def.phrase,
        owner=None,
        caregiver="caregiver",
        meters={"sharpness": 1.0, "risk": 2.0, "cleanliness": 0.0},
        memes={"noticed": 0.0},
    ))
    return StoryState(world=world, child=child, friend=friend, caregiver=caregiver, sliver=sliver)


def _discover_sliver(state: StoryState) -> None:
    w, child, friend, sliver = state.world, state.child, state.friend, state.sliver
    child.meters["time_spent"] += 1
    friend.meters["time_spent"] += 1
    sliver.memes["noticed"] += 1
    child.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    w.say(
        f"{child.id} and {friend.id} were having an ordinary day at {w.place.label}. "
        f"Then {child.id} stopped short and discovered {sliver.phrase}."
    )
    w.say(
        f"It was so small that it almost hid in the light, but {child.id} could tell it might poke a finger or a foot."
    )


def _caution(state: StoryState) -> None:
    w, child, friend, caregiver, sliver = state.world, state.child, state.friend, state.caregiver, state.sliver
    child.memes["caution"] += 1
    friend.memes["caution"] += 1
    state.cautioned = True
    w.say(
        f"{child.id} pointed it out to {friend.id} right away. "
        f"Instead of touching it, they stood back and called {caregiver.label_word if hasattr(caregiver, 'label_word') else caregiver.label}."
    )
    w.say(
        f'"We found a sliver," {child.id} said. "It could hurt somebody if nobody is careful."'
    )
    caregiver.memes["caution"] += 1
    caregiver.meters["time_spent"] += 1
    w.say(
        f"{caregiver.label.capitalize()} smiled because the warning came early. "
        f"They fetched a tissue and a small box so the sharp little piece could be moved safely."
    )
    sliver.meters["risk"] = 0.0
    sliver.meters["cleanliness"] = 1.0
    state.fixed = True


def _friendship_ending(state: StoryState) -> None:
    w, child, friend, caregiver, sliver = state.world, state.child, state.friend, state.caregiver, state.sliver
    child.memes["trust"] += 1
    friend.memes["trust"] += 1
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    child.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    w.say(
        f"After that, {child.id} and {friend.id} went back to their game with lighter hearts. "
        f"The little place where the sliver had been was safe again, and the day felt ordinary in the best way."
    )
    w.say(
        f"They left with the happy feeling that being careful had protected their friendship, not slowed it down."
    )


def tell(place: Place, sliver_def: Sliver, name: str, friend: str, gender: str, caregiver: str, trait: str) -> World:
    params = StoryParams(place=place.id, sliver=sliver_def.id, name=name, friend=friend, gender=gender, caregiver=caregiver, trait=trait)
    state = _setup_state(params)
    w = state.world

    w.say(
        f"{state.child.id} was a {trait} {gender} who liked quiet afternoons with {state.friend.id}."
    )
    w.say(
        f"Together they liked ordinary things: sharing snacks, telling jokes, and noticing small details."
    )
    w.para()
    w.say(place.details)
    _discover_sliver(state)
    w.para()
    _caution(state)
    _friendship_ending(state)

    w.facts.update(
        child=state.child,
        friend=state.friend,
        caregiver=state.caregiver,
        sliver=state.sliver,
        place=place,
        fixed=state.fixed,
        cautioned=state.cautioned,
    )
    return w


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for p in SETTINGS.values():
        for s in SLIVERS.values():
            if p.id == "kitchen" and s.id != "glass":
                continue
            if p.id == "playground" and s.id == "wood":
                continue
            if p.id == "porch" and s.id == "wood":
                continue
            if p.id == "classroom" and s.id == "glass":
                continue
            combos.append((p.id, s.id, "friendship_caution"))
    return combos


def explain_rejection(place: str, sliver_id: str) -> str:
    return (
        f"(No story: the chosen place '{place}' and sliver '{sliver_id}' do not make a natural slice-of-life discovery. "
        f"Try one of the valid combinations.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small slice-of-life story world about a discovered sliver and cautious friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sliver", choices=SLIVERS)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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
    if args.place and args.sliver:
        if (args.place, args.sliver, "friendship_caution") not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.sliver))
    if args.gender and not args.name:
        pass
    place = args.place or rng.choice(list(SETTINGS))
    sliver = args.sliver or rng.choice([s for p, s, _ in valid_combos() if p == place])
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(FRIEND_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, sliver=sliver, name=name, friend=friend, gender=gender, caregiver=caregiver, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a young child about friendship, caution, and a discovered sliver at {f["place"].label}.',
        f"Tell a gentle story where {f['child'].id} notices {f['sliver'].label} and chooses to warn {f['friend'].id} instead of touching it.",
        f'Write a child-facing story that includes the words "sliver" and "discover" and ends with friends choosing a careful fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    caregiver = f["caregiver"]
    sliver = f["sliver"]
    place = f["place"]
    return [
        QAItem(
            question=f"What did {child.id} discover at {place.label}?",
            answer=f"{child.id} discovered {sliver.phrase}. It was tiny, but it could still hurt somebody, so they were careful.",
        ),
        QAItem(
            question=f"How did {child.id} and {friend.id} handle the sliver?",
            answer=f"They stayed back, called {caregiver.label}, and let the careful grown-up move it safely with a tissue and a box.",
        ),
        QAItem(
            question=f"Why was that a good choice?",
            answer="It was a good choice because they protected their hands and feet, kept the area safe, and showed friendship by looking out for each other.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    sliver = f["sliver"]
    return [
        QAItem(
            question="What is a sliver?",
            answer="A sliver is a very small, thin piece of something, and if it is sharp it should be handled carefully.",
        ),
        QAItem(
            question="Why should children not pick up a sharp sliver by themselves?",
            answer="A sharp sliver can poke or cut skin, so children should tell a grown-up and let the grown-up move it safely.",
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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8} {e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
place_valid(P,S) :- valid_pair(P,S).
valid_pair(playground,wood).
valid_pair(playground,glass).
valid_pair(kitchen,glass).
valid_pair(porch,shell).
valid_pair(classroom,wood).
valid_story(P,S) :- place_valid(P,S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for sid in SLIVERS:
        lines.append(asp.fact("sliver", sid))
    for p, s, _ in valid_combos():
        lines.append(asp.fact("valid_pair", p, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_pair/2."))
    asp_pairs = sorted(set(asp.atoms(model, "valid_pair")))
    py_pairs = sorted((p, s) for p, s, _ in valid_combos())
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(py_pairs)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if set(asp_pairs) - set(py_pairs):
        print("  only in clingo:", sorted(set(asp_pairs) - set(py_pairs)))
    if set(py_pairs) - set(asp_pairs):
        print("  only in python:", sorted(set(py_pairs) - set(asp_pairs)))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SLIVERS[params.sliver], params.name, params.friend, params.gender, params.caregiver, params.trait)
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
    StoryParams(place="playground", sliver="wood", name="Mina", friend="Toby", gender="girl", caregiver="mother", trait="curious"),
    StoryParams(place="kitchen", sliver="glass", name="Finn", friend="Lila", gender="boy", caregiver="father", trait="careful"),
    StoryParams(place="porch", sliver="shell", name="Maya", friend="Owen", gender="girl", caregiver="grandparent", trait="kind"),
    StoryParams(place="classroom", sliver="wood", name="Noah", friend="Iris", gender="boy", caregiver="teacher", trait="quiet"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_pair/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_pair/2."))
        pairs = sorted(set(asp.atoms(model, "valid_pair")))
        print(f"{len(pairs)} compatible place/sliver combinations:")
        for p, s in pairs:
            print(f"  {p:10} {s}")
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
            header = f"### {p.name}: {p.sliver} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
