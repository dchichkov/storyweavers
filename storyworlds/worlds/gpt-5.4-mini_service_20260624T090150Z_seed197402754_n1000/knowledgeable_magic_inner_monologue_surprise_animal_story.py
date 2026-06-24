#!/usr/bin/env python3
"""
Storyworld: knowledgeable magic surprise animal story
=====================================================

A tiny classical story simulation in an animal-story style.

Premise:
- A small animal character wants to use a bit of magic.
- The character thinks privately through an inner monologue.
- A surprise complicates the plan.
- The character uses knowledge, care, and a gentle magical fix to resolve it.

The world model tracks:
- physical state in meters: location, carrying, sparkles, dampness, etc.
- emotional state in memes: worry, wonder, pride, relief, surprise, kindness.

The prose is driven by state changes rather than a frozen template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "cat", "dog", "mouse", "bear", "squirrel", "bird"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    cozy: bool = True
    magic_kind: str = ""


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    helps: str
    surprise_safe: bool = True


@dataclass
class StoryParams:
    place: str
    animal: str
    charm: str
    surprise: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_sparkle(world: World) -> list[str]:
    out: list[str] = []
    for animal in world.characters():
        if animal.meters.get("magic", 0.0) < THRESHOLD:
            continue
        sig = ("sparkle", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        animal.meters["sparkles"] = animal.meters.get("sparkles", 0.0) + 1
        out.append(f"Soft sparkles danced around {animal.name_word}.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("surprise_seen"):
        return out
    for animal in world.characters():
        if animal.memes.get("surprise", 0.0) < THRESHOLD:
            continue
        sig = ("surprise", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["surprise_seen"] = True
        out.append(f"Something unexpected made {animal.name_word} blink wide-eyed.")
    return out


CAUSAL_RULES = [
    Rule("sparkle", _r_sparkle),
    Rule("surprise", _r_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "meadow": Place(id="meadow", label="the meadow", cozy=True, magic_kind="glow"),
    "forest": Place(id="forest", label="the forest", cozy=True, magic_kind="whisper"),
    "pond": Place(id="pond", label="the pond", cozy=True, magic_kind="mirror"),
    "garden": Place(id="garden", label="the garden", cozy=True, magic_kind="bloom"),
}

ANIMALS = {
    "fox": {"type": "fox", "label": "Fox"},
    "rabbit": {"type": "rabbit", "label": "Rabbit"},
    "cat": {"type": "cat", "label": "Cat"},
    "mouse": {"type": "mouse", "label": "Mouse"},
    "squirrel": {"type": "squirrel", "label": "Squirrel"},
    "bird": {"type": "bird", "label": "Bird"},
}

CHARM = {
    "lantern": Charm(
        id="lantern",
        label="lantern",
        phrase="a little lantern with a blue ribbon",
        effect="glow softly",
        helps="light a path",
    ),
    "bell": Charm(
        id="bell",
        label="bell",
        phrase="a small bell with a shiny loop",
        effect="sing gently",
        helps="call a friend",
    ),
    "leaf": Charm(
        id="leaf",
        label="leaf charm",
        phrase="a leaf charm that smelled like rain",
        effect="float on air",
        helps="find a hidden thing",
    ),
}

SURPRISES = {
    "raindrop": "a fat raindrop on the nose",
    "hollow_log": "a tiny mouse peeking from a hollow log",
    "lost_berry": "a bright berry stuck under a stone",
    "wind_bell": "a stray wind bell ringing by itself",
}


KNOWLEDGE = {
    "knowledgeable": [
        (
            "What does knowledgeable mean?",
            "Knowledgeable means knowing a lot about something and being able to use that knowledge to help."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is something special and surprising that can make impossible things happen in a gentle story."
        )
    ],
    "surprise": [
        (
            "What is a surprise?",
            "A surprise is something unexpected that happens when you do not see it coming."
        )
    ],
    "inner monologue": [
        (
            "What is an inner monologue?",
            "An inner monologue is the private voice a character uses to think through a problem in their own mind."
        )
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small animal story with magic, inner monologue, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--charm", choices=CHARM)
    ap.add_argument("--surprise", choices=SURPRISES)
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


def reasonableness_gate(place: Place, animal_id: str, charm_id: str, surprise_id: str) -> None:
    if animal_id not in ANIMALS:
        raise StoryError("Unknown animal.")
    if charm_id not in CHARM:
        raise StoryError("Unknown charm.")
    if surprise_id not in SURPRISES:
        raise StoryError("Unknown surprise.")
    if place.id == "pond" and charm_id == "bell":
        raise StoryError("(No story: a bell is not a good fit for a quiet pond story.)")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place or rng.choice(list(PLACES))
    animal_id = args.animal or rng.choice(list(ANIMALS))
    charm_id = args.charm or rng.choice(list(CHARM))
    surprise_id = args.surprise or rng.choice(list(SURPRISES))
    place = PLACES[place_id]
    reasonableness_gate(place, animal_id, charm_id, surprise_id)
    name = args.name or rng.choice(["Pip", "Milo", "Nia", "Jun", "Tavi", "Luna"])
    return StoryParams(place=place_id, animal=animal_id, charm=charm_id, surprise=surprise_id, name=name)


def _do_magic(world: World, hero: Entity, charm: Charm) -> None:
    hero.meters["magic"] = hero.meters.get("magic", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    world.say(f"{hero.name_word} held {charm.phrase} close and whispered a tiny spell.")


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    animal = ANIMALS[params.animal]
    charm = CHARM[params.charm]
    surprise_text = SURPRISES[params.surprise]

    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=animal["type"], label=params.name, traits=["knowledgeable", "gentle"]))
    charm_ent = world.add(Entity(id=charm.id, type="charm", label=charm.label, phrase=charm.phrase, owner=hero.id))
    world.facts.update(hero=hero, charm=charm_ent, charm_def=charm, surprise=params.surprise, place=place)

    world.say(f"{hero.name_word} was a knowledgeable little {animal['label'].lower()} who loved quiet days in {place.label}.")
    world.say(f"{hero.name_word} kept {charm.phrase} in a safe pocket and thought, 'I can use this kindly if I need to.'")
    world.para()
    world.say(f"One day, {hero.name_word} went to {place.label} to try a small bit of magic.")
    world.say(f"Inside {hero.name_word}'s mind, a private thought rolled along: 'If I stay calm, I can help someone today.'")
    _do_magic(world, hero, charm)
    propagate(world)

    world.para()
    world.say(f"Then came a surprise: {surprise_text}.")
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(f"{hero.name_word} froze for a blink and thought, 'Oh! That was not what I expected.'")
    propagate(world)

    world.para()
    world.say(f"{hero.name_word} remembered what the little charm was for.")
    hero.memes["knowledge"] = hero.memes.get("knowledge", 0.0) + 1
    if params.surprise == "lost_berry":
        world.say(f"With a careful glow, {hero.name_word} slid the stone aside and lifted out the berry without squashing it.")
    elif params.surprise == "hollow_log":
        world.say(f"{hero.name_word} used the lantern's glow to show the mouse a safe path out of the log.")
    elif params.surprise == "raindrop":
        world.say(f"{hero.name_word} laughed softly and let the bell charm make a warm, steady sound under the rain.")
    else:
        world.say(f"{hero.name_word} gave the ringing bell a gentle tap, and the sound settled the windy little trick.")
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(f"By the end, {hero.name_word} felt proud, because the magic was small, kind, and just right.")
    world.say(f"{hero.name_word} walked home with {charm.label} tucked away again, and the surprise felt like a story to remember.")

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    charm = f["charm_def"]
    return [
        f'Write a gentle story for a young child about a knowledgeable {hero.type} who uses magic in {world.place.label}.',
        f"Tell a story with an inner monologue where {hero.name_word} thinks carefully before using {charm.label}.",
        f'Write a short animal story that includes a surprise and ends with a kind magical solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    charm = f["charm_def"]
    surprise = f["surprise"]
    place = f["place"].label
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.name_word}, a knowledgeable little {hero.type}, in {place}."
        ),
        QAItem(
            question=f"What did {hero.name_word} use for magic?",
            answer=f"{hero.name_word} used {charm.phrase} to do a small, gentle bit of magic."
        ),
        QAItem(
            question=f"What surprise happened in the story?",
            answer=f"The surprise was {SURPRISES[surprise]}."
        ),
        QAItem(
            question=f"How did {hero.name_word} feel at the end?",
            answer=f"{hero.name_word} felt proud and relieved because the magical choice helped."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["knowledgeable"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["magic"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["surprise"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["inner monologue"])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- char(H).
charm(C) :- charm_fact(C).
surprise(S) :- surprise_fact(S).

can_use_magic(H,C) :- hero(H), charm(C), knowledgeable(H).
has_inner_monologue(H) :- hero(H).
surprised(H) :- hero(H), surprise_seen(H).

story_ok(H,C,S) :- hero(H), charm(C), surprise(S), can_use_magic(H,C), has_inner_monologue(H), surprised(H).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for aid in ANIMALS:
        lines.append(asp.fact("char", aid))
        lines.append(asp.fact("knowledgeable", aid))
    for cid in CHARM:
        lines.append(asp.fact("charm_fact", cid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise_fact", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    atoms = set(asp.atoms(model, "story_ok"))
    expected = set()
    for a in ANIMALS:
        for c in CHARM:
            for s in SURPRISES:
                expected.add((a, c, s))
    if atoms == expected:
        print(f"OK: clingo gate matches Python registry space ({len(atoms)} triples).")
        return 0
    print("MISMATCH between clingo and Python registry space.")
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


CURATED = [
    StoryParams(place="meadow", animal="fox", charm="lantern", surprise="lost_berry", name="Pip"),
    StoryParams(place="forest", animal="rabbit", charm="bell", surprise="hollow_log", name="Milo"),
    StoryParams(place="garden", animal="squirrel", charm="leaf", surprise="wind_bell", name="Luna"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} compatible story triples")
        for t in asp_valid_stories():
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.animal} with {p.charm} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
