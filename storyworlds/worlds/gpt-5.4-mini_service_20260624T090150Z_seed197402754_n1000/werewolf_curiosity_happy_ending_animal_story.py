#!/usr/bin/env python3
"""
A small storyworld for an animal-story style tale about a curious werewolf
who learns something safe and ends with a happy ending.

The premise is simple and child-facing:
- an animal-like hero is curious about a sound, smell, or object
- curiosity creates a small problem or worry
- a helper or careful choice turns the problem into a happy ending

This world keeps the simulation grounded in state:
- physical meters: distance, mess, noise, light, hunger, weather comfort
- emotional memes: curiosity, worry, courage, joy, trust, relief

The story is generated from a short causal model rather than a frozen template.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "she-wolf", "woman", "mother"}
        male = {"boy", "he-wolf", "man", "father", "wolf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = False
    comforts: set[str] = field(default_factory=set)


@dataclass
class CuriosityTrigger:
    id: str
    thing: str
    question: str
    draw: str
    route: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ComfortItem:
    id: str
    label: str
    phrase: str
    helps: set[str]
    wraps: set[str]
    prep: str
    tail: str
    plural: bool = False


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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    trigger: str
    comfort: str
    name: str
    seed: Optional[int] = None


PLACES = {
    "forest_edge": Place(id="forest_edge", label="the edge of the forest", comforts={"tree", "lantern"}),
    "cabin": Place(id="cabin", label="the little cabin", indoor=True, comforts={"lantern"}),
    "meadow": Place(id="meadow", label="the meadow", comforts={"flower", "pond"}),
    "moonlit_hill": Place(id="moonlit_hill", label="the moonlit hill", comforts={"moonbeam", "stone"}),
}

TRIGGERS = {
    "owl": CuriosityTrigger(
        id="owl",
        thing="an owl feather",
        question="what was making the soft hoot",
        draw="follow the hoot",
        route="tiptoe toward the tree",
        reveal="a sleepy owl tucked in a nest",
        tags={"bird", "night", "feather"},
    ),
    "jar": CuriosityTrigger(
        id="jar",
        thing="a shiny jar",
        question="what was glowing inside",
        draw="peek at the glow",
        route="walk closer to the bush",
        reveal="fireflies blinking like little stars",
        tags={"light", "bug", "glow"},
    ),
    "tracks": CuriosityTrigger(
        id="tracks",
        thing="tiny tracks in the mud",
        question="whose tracks they were",
        draw="sniff the ground",
        route="follow the tracks",
        reveal="a bunny family nibbling clover",
        tags={"mud", "bunny", "track"},
    ),
    "music": CuriosityTrigger(
        id="music",
        thing="a distant tune",
        question="who was playing the tune",
        draw="listen closely",
        route="pad toward the hill",
        reveal="a hedgehog gently plucking a little harp",
        tags={"sound", "music", "friend"},
    ),
}

COMFORTS = {
    "lantern": ComfortItem(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern",
        helps={"dark"},
        wraps={"light"},
        prep="pick up a little lantern first",
        tail="carried the lantern home",
    ),
    "tree": ComfortItem(
        id="tree",
        label="a safe tree branch",
        phrase="a safe tree branch",
        helps={"climb"},
        wraps={"height"},
        prep="stay close to the tree branch",
        tail="rested near the tree branch",
    ),
    "flower": ComfortItem(
        id="flower",
        label="a flower crown",
        phrase="a flower crown",
        helps={"calm"},
        wraps={"worry"},
        prep="wear a flower crown first",
        tail="wore the flower crown all the way back",
    ),
    "moonbeam": ComfortItem(
        id="moonbeam",
        label="moonlight on the path",
        phrase="moonlight on the path",
        helps={"night"},
        wraps={"dark"},
        prep="follow the moonlight on the path",
        tail="walked home by the moonlight",
    ),
}

NAMES = ["Milo", "Nina", "Toby", "Penny", "Arlo", "Mina", "Luna", "Cleo"]
TRAITS = ["curious", "gentle", "brave", "sniffly", "playful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a curious werewolf with a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--comfort", choices=COMFORTS)
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


def reasonableness_gate(trigger: CuriosityTrigger, comfort: ComfortItem, place: Place) -> bool:
    if trigger.id == "jar" and comfort.id != "lantern":
        return True
    if trigger.id == "tracks" and comfort.id in {"tree", "flower"}:
        return True
    if trigger.id == "owl" and comfort.id in {"lantern", "tree"}:
        return True
    if trigger.id == "music" and comfort.id in {"moonbeam", "flower"}:
        return True
    return False


def explain_rejection(trigger: CuriosityTrigger, comfort: ComfortItem) -> str:
    return (
        f"(No story: the curious choice around {trigger.thing} does not fit the comfort "
        f"item {comfort.label}. The ending must be a real help, not a random object.)"
    )


def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = []
    for place_id, place in PLACES.items():
        for trig_id, trig in TRIGGERS.items():
            for comfort_id, comfort in COMFORTS.items():
                if reasonableness_gate(trig, comfort, place):
                    combos.append((place_id, trig_id, comfort_id))
    combos = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.trigger is None or c[1] == args.trigger)
        and (args.comfort is None or c[2] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, trigger, comfort = select_combo(args, rng)
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, trigger=trigger, comfort=comfort, name=name)


def choose_gendered_type(name: str) -> str:
    return "wolf"


def predict_path(world: World, hero: Entity, trig: CuriosityTrigger) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["curiosity"] += 1
    sim.facts["followed"] = True
    sim.facts["found"] = trig.reveal
    if trig.id == "jar":
        sim.facts["worry"] = True
    return sim.facts


def narrate_intro(world: World, hero: Entity, trig: CuriosityTrigger) -> None:
    world.say(
        f"{hero.id} was a little werewolf who loved sniffing around the {world.place.label}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} was especially curious about {trig.thing}."
    )


def narrate_setup(world: World, hero: Entity, trig: CuriosityTrigger) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"One evening, {hero.id} stopped and wondered {trig.question}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {trig.draw}, so {hero.pronoun()} began to {trig.route}."
    )


def narrate_conflict(world: World, hero: Entity, trig: CuriosityTrigger) -> None:
    if trig.id == "jar":
        hero.memes["worry"] += 1
        world.say(
            f"Then {hero.id} saw the path get darker, and that made the glow feel a little tricky."
        )
    elif trig.id == "tracks":
        hero.meters["mud"] = hero.meters.get("mud", 0) + 1
        world.say(
            f"The mud was soft and slippery, and {hero.id}'s paws got messy while following the tracks."
        )
    else:
        hero.memes["worry"] += 0.5
        world.say(
            f"{hero.id}'s ears perked up, and the unknown sound felt big enough to be careful about."
        )


def choose_comfort(hero: Entity, trig: CuriosityTrigger) -> ComfortItem:
    for comfort in COMFORTS.values():
        if comfort.id == "lantern" and trig.id == "jar":
            return comfort
    return next(c for c in COMFORTS.values() if c.id in {"moonbeam", "flower", "tree", "lantern"})


def narrate_resolution(world: World, hero: Entity, comfort: ComfortItem, trig: CuriosityTrigger) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["curiosity"] = max(0.0, hero.memes["curiosity"] - 0.5)
    world.say(
        f"{hero.id}'s {comfort.label} helped, and that made the path feel friendly again."
    )
    world.say(
        f"With {comfort.label}, {hero.id} found that {trig.reveal}, and everyone felt safer."
    )
    world.say(
        f"At the end, {hero.id} went home happy, still curious, and smiling under the night sky."
    )


def tell_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    trig = TRIGGERS[params.trigger]
    comfort = COMFORTS[params.comfort]
    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=choose_gendered_type(params.name),
        label="werewolf",
        meters={"distance": 0.0, "mess": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "relief": 0.0},
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type="rabbit",
        label="rabbit friend",
        meters={},
        memes={"kindness": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, trigger=trig, comfort=comfort, place=place)

    narrate_intro(world, hero, trig)
    world.para()
    narrate_setup(world, hero, trig)
    narrate_conflict(world, hero, trig)
    world.para()
    world.say(
        f"{friend.label.capitalize()} noticed and suggested, \"Try {comfort.prep}.\""
    )
    narrate_resolution(world, hero, comfort, trig)

    world.facts["happy_ending"] = True
    return world


def generate_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    trig = f["trigger"]
    comfort = f["comfort"]
    return [
        f"Write a short animal story about a curious werewolf named {hero.id} who wonders about {trig.thing}.",
        f"Tell a gentle story where {hero.id} follows {trig.question} and gets a happy ending with {comfort.label}.",
        f"Write a child-friendly werewolf story that begins with curiosity, has a small worry, and ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    trig = f["trigger"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little werewolf who was very curious.",
        ),
        QAItem(
            question=f"What was {hero.id} curious about?",
            answer=f"{hero.id} was curious about {trig.thing}. {hero.pronoun().capitalize()} wanted to know {trig.question}.",
        ),
        QAItem(
            question=f"What helped {hero.id} have a happy ending?",
            answer=f"{comfort.label} helped {hero.id} feel safe, and that led to a happy ending.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} going home happy, still curious, and smiling under the night sky.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling of wanting to know more about something new or strange.",
        ),
        QAItem(
            question="What is a werewolf?",
            answer="A werewolf is a story creature that is part wolf and part person, often changing at night.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem is solved and the characters feel safe or glad at the end.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- werewolf(X).
curious(X) :- hero(X), curiosity(X).
happy_ending(X) :- hero(X), resolved(X).
valid_story(P,T,C) :- place(P), trigger(T), comfort(C), compatible(T,C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TRIGGERS:
        lines.append(asp.fact("trigger", tid))
        lines.append(asp.fact("werewolf", "hero"))
        lines.append(asp.fact("curiosity", "hero"))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    for tid, trig in TRIGGERS.items():
        for cid, comfort in COMFORTS.items():
            if reasonableness_gate(trig, comfort, PLACES["forest_edge"]):
                lines.append(asp.fact("compatible", tid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, place in PLACES.items():
        for t, trig in TRIGGERS.items():
            for c, comfort in COMFORTS.items():
                if reasonableness_gate(trig, comfort, place):
                    out.append((p, t, c))
    return out


def build_story(params: StoryParams) -> StorySample:
    world = tell_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
    StoryParams(place="forest_edge", trigger="owl", comfort="tree", name="Milo"),
    StoryParams(place="meadow", trigger="tracks", comfort="flower", name="Penny"),
    StoryParams(place="cabin", trigger="jar", comfort="lantern", name="Luna"),
    StoryParams(place="moonlit_hill", trigger="music", comfort="moonbeam", name="Arlo"),
]


def explain_gender(_: str, __: str) -> str:
    return ""


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible story combos.")
        for combo in asp_valid_combos():
            print(combo)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.trigger} at {p.place} (comfort: {p.comfort})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_combos_python() -> list[tuple[str, str, str]]:
    return valid_combos()


if __name__ == "__main__":
    main()
