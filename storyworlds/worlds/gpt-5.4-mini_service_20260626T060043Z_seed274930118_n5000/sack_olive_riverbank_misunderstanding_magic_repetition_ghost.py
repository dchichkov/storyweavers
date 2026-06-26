#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sack_olive_riverbank_misunderstanding_magic_repetition_ghost.py
================================================================================================

A small ghost-story world set on a riverbank, built from the seed words
"sack" and "olive". The core premise is a misunderstanding: a child finds a
mysterious sack, mistakes the signs around it, and keeps repeating the same
mistaken action until a little magic reveals the truth.

The story is designed to feel like a gentle ghost tale: dusk, reeds, soft
mist, a shy presence, and a final image that shows what changed.
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
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    dusk: bool = True
    misty: bool = True


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    charm: str
    glow: str
    avoids: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    relic: str
    child_name: str
    child_type: str
    companion_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Child")
    sack = world.entities.get("Sack")
    if not child or not sack:
        return out
    if child.memes.get("repeat", 0) < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sack.meters["opened"] = sack.meters.get("opened", 0) + 1
    out.append("Again, the sack gave only a soft rustle.")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Child")
    olive = world.entities.get("Olive")
    if not child or not olive:
        return out
    if child.memes.get("wonder", 0) < THRESHOLD:
        return out
    sig = ("magic",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    olive.meters["glow"] = olive.meters.get("glow", 0) + 1
    child.memes["fear"] = max(0.0, child.memes.get("fear", 0) - 1)
    child.memes["understanding"] = child.memes.get("understanding", 0) + 1
    out.append("The olive pebble shone, as if moonlight had learned a secret.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("Child")
    ghost = world.entities.get("Ghost")
    sack = world.entities.get("Sack")
    if not child or not ghost or not sack:
        return out
    if child.memes.get("misunderstanding", 0) < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["sadness"] = ghost.memes.get("sadness", 0) + 1
    out.append("The shy figure by the reeds looked even sadder, because it had been mistaken.")
    return out


RULES = [_r_misunderstanding, _r_magic, _r_repeat]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACE = Place(name="the riverbank", dusk=True, misty=True)

RELICS = {
    "sack": Relic(
        id="sack",
        label="sack",
        phrase="a small frayed sack",
        charm="a whisper in the reeds",
        glow="moon-silver",
        avoids="being opened too fast",
        tags={"sack", "misunderstanding"},
    ),
    "olive": Relic(
        id="olive",
        label="olive",
        phrase="a smooth olive stone",
        charm="a green glimmer",
        glow="soft green",
        avoids="being ignored",
        tags={"olive", "magic"},
    ),
}


NAMES = ["Mina", "Oren", "Luna", "Pip", "Tara", "Noa", "Iris", "Jasper"]
TRAITS = ["careful", "curious", "brave", "gentle", "nervous", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    return [("riverbank", "sack"), ("riverbank", "olive")]


def reasonableness_gate(place: str, relic: str) -> bool:
    return (place, relic) in valid_combos()


def introduce(world: World, child: Entity, relic: Relic, ghost: Entity) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} little {child.type} who loved the riverbank at dusk."
    )
    world.say(
        f"One evening, {child.id} found {relic.phrase} near the reeds, and a shy ghost watched from the water's edge."
    )


def setup_magic(world: World, child: Entity, relic: Relic, ghost: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    if relic.id == "sack":
        child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0) + 1
        world.say(
            f"{child.id} thought the sack might hide a lost treasure, because it was tied tight and no one spoke."
        )
    else:
        child.memes["wonder"] = child.memes.get("wonder", 0) + 1
        world.say(
            f"{child.id} lifted the olive stone and felt a tiny warm hum, like a lantern waking up."
        )
    ghost.memes["waiting"] = ghost.memes.get("waiting", 0) + 1


def repeat_action(world: World, child: Entity, relic: Relic) -> None:
    child.memes["repeat"] = child.memes.get("repeat", 0) + 1
    world.say(
        f"{child.id} opened the sack again and again, but each time there was only the same soft rustle."
    )
    propagate(world, narrate=True)


def turn_to_truth(world: World, child: Entity, relic: Relic, ghost: Entity) -> None:
    child.memes["wonder"] = child.memes.get("wonder", 0) + 1
    propagate(world, narrate=True)
    if relic.id == "olive":
        world.say(
            f"Then the olive stone glowed brighter, and {child.id} saw that the ghost was not scary at all."
        )
    else:
        world.say(
            f"Then the sack loosened in the breeze, and {child.id} saw a little olive stone tucked in the knot."
        )
    ghost.memes["sadness"] = max(0.0, ghost.memes.get("sadness", 0) - 1)
    ghost.memes["relief"] = ghost.memes.get("relief", 0) + 1


def resolve(world: World, child: Entity, relic: Relic, ghost: Entity) -> None:
    child.memes["misunderstanding"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["understanding"] = child.memes.get("understanding", 0) + 1
    world.say(
        f"{child.id} smiled, set the sack down carefully, and whispered a sorry to the ghost."
    )
    if relic.id == "sack":
        world.say(
            f"Inside the sack, the olive stone gave one last green blink, and the ghost floated up with a grateful sigh."
        )
    else:
        world.say(
            f"{child.id} placed the olive stone beside the sack, and the ghost nodded as if a long-lost story had finally been heard."
        )
    world.say(
        f"The river kept humming in the dark, but now {child.id} was listening the right way."
    )


def tell(params: StoryParams) -> World:
    world = World(PLACE)
    child = world.add(Entity(
        id="Child",
        kind="character",
        type=params.child_type,
        traits=[params.trait, "little"],
    ))
    ghost = world.add(Entity(
        id="Ghost",
        kind="character",
        type="ghost",
        traits=["shy", "quiet"],
    ))
    relic = RELICS[params.relic]
    item = world.add(Entity(
        id=relic.id.capitalize(),
        kind="thing",
        type=relic.id,
        label=relic.label,
        phrase=relic.phrase,
        owner=child.id,
        location="riverbank",
    ))

    intro(world, child, relic, ghost)
    world.para()
    setup_magic(world, child, relic, ghost)
    if relic.id == "sack":
        repeat_action(world, child, relic)
    else:
        world.say(
            f"{child.id} kept looking back at the sack, because the olive light made the shadows seem full of messages."
        )
        child.memes["repeat"] = child.memes.get("repeat", 0) + 1
        propagate(world, narrate=True)
    world.para()
    turn_to_truth(world, child, relic, ghost)
    resolve(world, child, relic, ghost)

    world.facts.update(child=child, ghost=ghost, relic=item, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        'Write a gentle ghost story for a young child about a sack and an olive stone by a riverbank.',
        f"Tell a moonlit riverbank story where {p.child_name} keeps making the same mistake until a tiny bit of magic helps.",
        "Write a short story with misunderstanding, magic, and repetition that ends kindly instead of frighteningly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    params: StoryParams = f["params"]
    relic: Entity = f["relic"]
    return [
        QAItem(
            question=f"Where did {child.id} find the mysterious {relic.label}?",
            answer=f"{child.id} found it on the riverbank near the reeds, where the mist was drifting low.",
        ),
        QAItem(
            question=f"Why did {child.id} keep doing the same thing with the {relic.label}?",
            answer=f"{child.id} kept repeating the action because there was a misunderstanding, and {child.id} thought the {relic.label} was hiding something important.",
        ),
        QAItem(
            question=f"What changed when the magic happened in the story?",
            answer=f"The magic made the little olive glow and helped {child.id} understand that the ghost was shy, not dangerous.",
        ),
        QAItem(
            question=f"Who was the ghost waiting for by the riverbank?",
            answer=f"The ghost was waiting for someone kind enough to notice the message hidden in the sack and the olive stone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land right beside a river.",
        ),
        QAItem(
            question="What does misunderstanding mean?",
            answer="A misunderstanding is when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing the same thing again and again.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special, impossible thing that can change what people see, feel, or understand.",
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
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:6} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for (name,) in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "riverbank"))
    lines.append(asp.fact("feature", "misunderstanding"))
    lines.append(asp.fact("feature", "magic"))
    lines.append(asp.fact("feature", "repetition"))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        for t in sorted(relic.tags):
            lines.append(asp.fact("tagged", rid, t))
    return "\n".join(lines)


ASP_RULES = r"""
% A relic can trigger a story if it lives at the riverbank and carries the seed features.
seed_story(R) :- relic(R), place(riverbank), tagged(R, misunderstanding).
seed_story(R) :- relic(R), place(riverbank), tagged(R, magic).
seed_story(R) :- relic(R), place(riverbank), tagged(R, repetition).

valid_story(riverbank, sack) :- seed_story(sack).
valid_story(riverbank, olive) :- seed_story(olive).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world on a riverbank.")
    ap.add_argument("--place", choices=["riverbank"])
    ap.add_argument("--relic", choices=sorted(RELICS))
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--companion-type", choices=["ghost"])
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
    if args.place and args.place != "riverbank":
        raise StoryError("This storyworld only supports the riverbank setting.")
    relic = args.relic or rng.choice(list(RELICS))
    if not reasonableness_gate("riverbank", relic):
        raise StoryError("No valid story matches the requested options.")
    child_type = args.child_type or rng.choice(["girl", "boy"])
    companion_type = "ghost"
    trait = args.trait or rng.choice(TRAITS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        place="riverbank",
        relic=relic,
        child_name=name,
        child_type=child_type,
        companion_type=companion_type,
        trait=trait,
    )


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
    StoryParams(place="riverbank", relic="sack", child_name="Mina", child_type="girl", companion_type="ghost", trait="curious"),
    StoryParams(place="riverbank", relic="olive", child_name="Oren", child_type="boy", companion_type="ghost", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            except StoryError as e:
                print(e)
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
            header = f"### {p.child_name}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
