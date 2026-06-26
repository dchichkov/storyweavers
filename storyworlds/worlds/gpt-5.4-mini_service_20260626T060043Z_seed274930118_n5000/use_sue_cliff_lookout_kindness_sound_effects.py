#!/usr/bin/env python3
"""
A small comedy storyworld set at a cliff lookout.

Premise:
- A child named Sue comes to a cliff lookout with a sound-effects gadget.
- Sue wants to use it for dramatic comedy noises while watching the view.
- A friend worries the loud sounds will scare the birds and ruin the calm moment.
- Kindness and a gentler plan turn the moment into a funny shared show.

This world models typed entities with physical meters and emotional memes.
It includes:
- use, sue
- Kindness
- Sound Effects
- Inner Monologue
- comedy tone
- cliff lookout setting
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
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
    place: str = "the cliff lookout"
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    noise_kind: str
    volume: str
    funny: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    label: str
    kind: str
    phrase: str
    gives_kindness: float
    makes_sound: float
    helps_focus: float


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.mood: str = "bright"

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.mood = self.mood
        return clone


@dataclass
class StoryParams:
    name: str = "Sue"
    friend: str = "Milo"
    parent: str = "Aunt"
    toy: str = "kazoo"
    choice: str = "kindness"
    seed: Optional[int] = None


SETTINGS = {
    "cliff_lookout": Setting(place="the cliff lookout", affords={"view", "sound"}),
}

TOYS = {
    "kazoo": Toy(
        id="kazoo",
        label="a kazoo",
        phrase="a shiny kazoo",
        noise_kind="honking",
        volume="very loud",
        funny="a tiny elephant in a sock",
        keyword="sound effects",
        tags={"sound", "effects"},
    ),
    "whoopee_cushion": Toy(
        id="whoopee_cushion",
        label="a whoopee cushion",
        phrase="a squeaky whoopee cushion",
        noise_kind="a squeak-brrrap",
        volume="extra silly",
        funny="a trampoline for snacks",
        keyword="sound effects",
        tags={"sound", "effects"},
    ),
}

CHOICES = {
    "kindness": Choice(
        id="kindness",
        label="Kindness",
        kind="kindness",
        phrase="a kind plan",
        gives_kindness=1.0,
        makes_sound=0.0,
        helps_focus=1.0,
    ),
    "whisper": Choice(
        id="whisper",
        label="a whisper",
        kind="quiet",
        phrase="a whisper plan",
        gives_kindness=0.2,
        makes_sound=0.0,
        helps_focus=0.2,
    ),
    "clap": Choice(
        id="clap",
        label="a clap",
        kind="sound",
        phrase="a clap plan",
        gives_kindness=0.0,
        makes_sound=0.8,
        helps_focus=0.0,
    ),
}

GIRL_NAMES = ["Sue", "Mina", "Lia", "Nora", "Tess"]
BOY_NAMES = ["Milo", "Ben", "Kai", "Eli", "Noah"]
FRIEND_NAMES = ["Milo", "Pip", "Zed", "Ari", "Jules"]


def reasonableness_gate(toy: Toy, choice: Choice) -> None:
    if toy.id == "whoopee_cushion" and choice.kind == "sound":
        raise StoryError("The loudest choices would just create noise without a real comic turn.")
    if choice.kind == "quiet" and toy.id == "kazoo":
        raise StoryError("A whisper is too weak to matter for a story about sound effects.")


def predict_noise(world: World, actor: Entity, toy: Toy) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["giddy"] = sim.get(actor.id).meters.get("giddy", 0.0) + 1.0
    return {
        "too_loud": toy.volume in {"very loud", "extra silly"},
        "birds_startled": toy.noise_kind.startswith("honking") or toy.id == "whoopee_cushion",
    }


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS["cliff_lookout"]
    toy = TOYS[params.toy]
    choice = CHOICES[params.choice]
    reasonableness_gate(toy, choice)

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in GIRL_NAMES else "boy",
        traits=["funny", "curious"],
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="character",
        type="boy" if params.friend in BOY_NAMES else "girl",
        traits=["careful", "patient"],
    ))
    adult = world.add(Entity(
        id=params.parent,
        kind="character",
        type="adult",
        label=f"{params.parent.lower()}",
        traits=["watchful"],
    ))
    toy_ent = world.add(Entity(
        id=toy.id,
        type="toy",
        label=toy.label,
        phrase=toy.phrase,
        owner=hero.id,
        caretaker=adult.id,
    ))

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        toy=toy,
        toy_ent=toy_ent,
        choice=choice,
    )
    return world


def intro(world: World) -> None:
    h = world.facts["hero"]
    toy = world.facts["toy"]
    world.say(f"{h.id} was a funny little kid who loved to use {toy.label} to make the day feel like a joke told by the wind.")
    world.say(f"{h.id} also had a secret superpower: an Inner Monologue that narrated every idea as if it were a dramatic movie trailer.")


def arrival(world: World) -> None:
    h = world.facts["hero"]
    f = world.facts["friend"]
    world.para()
    world.say(f"One breezy afternoon, {h.id} and {f.id} went to the cliff lookout.")
    world.say("The sea blinked far below, and the railing made the whole place feel both grand and a little bit wobbly.")
    world.say(f'In {h.id}\'s head, the Inner Monologue whispered, "This is the perfect place for sound effects!"')


def conflict(world: World) -> None:
    h = world.facts["hero"]
    f = world.facts["friend"]
    toy = world.facts["toy"]
    pred = predict_noise(world, h, toy)
    world.para()
    world.say(f"{h.id} wanted to use {toy.label} right away.")
    world.say(f'“I will make the most heroic honk ever,” {h.id} thought, which was not a thought anyone else could hear, but it was definitely loud in the mind.')
    if pred["birds_startled"]:
        world.say(f"{f.id} frowned and said the birds might burst into startled swoops if the noise got too wild.")
    world.say(f'That made {h.id} pause and think, "Hmm. Maybe my comedy should be funny, not frightening."')


def kindness_turn(world: World) -> None:
    h = world.facts["hero"]
    f = world.facts["friend"]
    adult = world.facts["adult"]
    choice = world.facts["choice"]
    toy = world.facts["toy"]
    world.para()
    if choice.id == "kindness":
        h.memes["kindness"] = h.memes.get("kindness", 0.0) + choice.gives_kindness
        h.memes["calm"] = h.memes.get("calm", 0.0) + choice.helps_focus
        f.memes["relief"] = f.memes.get("relief", 0.0) + 1.0
        world.say(f"{h.id} smiled and chose Kindness.")
        world.say(f"{h.id} held the toy low, asked {f.id} what sounds would be funny instead of scary, and listened like a very serious comedian.")
        world.say(f"{adult.id} nodded, because kindness made the joke better, not smaller.")
        world.say(f'In the Inner Monologue, {h.id} proudly declared, "A good joke is one everyone can laugh at, even the birds."')
    else:
        world.say(f"{h.id} tried {choice.label}, but it did not help much, so the cliff lookout stayed tense.")
        raise StoryError("This story needs Kindness to create the turn and ending image.")


def resolution(world: World) -> None:
    h = world.facts["hero"]
    f = world.facts["friend"]
    toy = world.facts["toy"]
    world.para()
    world.say(f"Then {h.id} used {toy.label} for tiny, silly bursts: honk-honk, pause, and a tiny dramatic squeal.")
    world.say(f"{f.id} laughed so hard that {f.id} had to hold the railing and wipe a grin off {f.id}'s face.")
    world.say(f"The gulls only tilted their heads, as if they were judging the performance but still buying tickets.")
    world.say(f"At the end, {h.id} and {f.id} stood together at the cliff lookout, sharing the joke and the view, while the wind carried the last little sound effect away.")


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    arrival(world)
    conflict(world)
    kindness_turn(world)
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    toy = f["toy"]
    return [
        f'Write a comedy story about {hero.id} at the cliff lookout who wants to use {toy.label} with an Inner Monologue.',
        f"Tell a funny story where {hero.id} and {friend.id} learn to use Kindness instead of being too loud with sound effects.",
        f'Write a child-friendly joke-filled story set at the cliff lookout with Sound Effects, Kindness, and a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h = f["hero"]
    fr = f["friend"]
    toy = f["toy"]
    return [
        QAItem(
            question=f"Where did {h.id} and {fr.id} go in the story?",
            answer="They went to the cliff lookout, where the sea was far below and the wind felt breezy.",
        ),
        QAItem(
            question=f"What did {h.id} want to use at the lookout?",
            answer=f"{h.id} wanted to use {toy.label}, because {h.id} was excited to make funny sound effects.",
        ),
        QAItem(
            question=f"What made the story turn from noisy to kind?",
            answer="The story turned when Sue chose Kindness, listened to the friend, and used smaller, funnier sounds instead of a big scary blast.",
        ),
        QAItem(
            question=f"How did the Inner Monologue help {h.id}?",
            answer=f"It helped by letting {h.id} think through the joke, notice the friend's worry, and choose a better way to be funny.",
        ),
        QAItem(
            question=f"What was funny at the end?",
            answer=f"The toy made tiny silly noises, the friend laughed, and even the gulls seemed like they were judging the comedy act from the sky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    toy = f["toy"]
    out = [
        QAItem(
            question="What is a cliff lookout?",
            answer="A cliff lookout is a place with a wide view from high up, so people can look out over water, land, or a valley.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special noises that help make a story, game, or joke feel more lively and dramatic.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means choosing to help, listen, or be gentle so someone else feels safe and cared for.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice in your head that helps you think and plan.",
        ),
    ]
    if toy.id == "kazoo":
        out.append(QAItem(
            question="What does a kazoo sound like?",
            answer="A kazoo makes a buzzy, humming sound when you blow into it, which can be very silly.",
        ))
    else:
        out.append(QAItem(
            question="What does a whoopee cushion do?",
            answer="A whoopee cushion makes a squeaky fart-like noise when someone sits on it, which is meant to be goofy.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% hero(Name). friend(Name). toy(Id). choice(Id). at(place).
% The story is valid when the hero uses a toy, the friend worries, and kindness resolves it.

use_toy(H) :- hero(H), toy(_).
worries(F) :- friend(F).
kind_turn(C) :- choice(C), C = kindness.

valid_story(H, F, T, C) :- hero(H), friend(F), toy(T), choice(C), use_toy(H), worries(F), kind_turn(C).

#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    # stable generic roles
    lines.append(asp.fact("hero", "sue"))
    lines.append(asp.fact("friend", "milo"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = set(asp.atoms(model, "valid_story"))
    py = {("sue", "milo", toy, "kindness") for toy in TOYS}
    if atoms == py:
        print(f"OK: clingo gate matches Python gate ({len(atoms)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld set at a cliff lookout.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES, default="Sue")
    ap.add_argument("--friend", choices=FRIEND_NAMES, default="Milo")
    ap.add_argument("--parent", default="Aunt")
    ap.add_argument("--toy", choices=TOYS, default="kazoo")
    ap.add_argument("--choice", choices=CHOICES, default="kindness")
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
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    if friend == name:
        friend = rng.choice([n for n in FRIEND_NAMES if n != name] or FRIEND_NAMES)
    toy = args.toy or rng.choice(list(TOYS))
    choice = args.choice or "kindness"
    if choice not in CHOICES:
        raise StoryError("Unknown choice.")
    if toy not in TOYS:
        raise StoryError("Unknown toy.")
    reasonableness_gate(TOYS[toy], CHOICES[choice])
    return StoryParams(name=name, friend=friend, parent=args.parent or "Aunt", toy=toy, choice=choice)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} valid stories:")
        for atom in atoms:
            print("  ", atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for toy in TOYS:
            params = StoryParams(name="Sue", friend="Milo", parent="Aunt", toy=toy, choice="kindness")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
