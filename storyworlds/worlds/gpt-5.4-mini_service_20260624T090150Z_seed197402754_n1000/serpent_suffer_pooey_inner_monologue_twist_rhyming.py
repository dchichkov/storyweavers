#!/usr/bin/env python3
"""
A small Storyweavers world: a serpent, a pooey mishap, an inner monologue,
and a rhyming twist.

The story starts with a serpent who wants to glide through a garden path and
ends with a surprising turn that changes the serpent's feelings and the scene.
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    keyword: str
    rhyme_a: str
    rhyme_b: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    clears: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    activity: str
    remedy: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden",
        scene="The garden was bright and green, with a stone path and a little pond nearby.",
        affords={"wriggle", "sing"},
    ),
    "pond": Place(
        id="pond",
        label="the pond",
        scene="The pond was still and shiny, with reeds swaying by the bank.",
        affords={"wriggle", "sing"},
    ),
    "yard": Place(
        id="yard",
        label="the yard",
        scene="The yard was wide and sunny, with soft dirt and a low fence.",
        affords={"wriggle", "sing"},
    ),
}

ACTIVITIES = {
    "wriggle": Activity(
        id="wriggle",
        verb="wriggle down the path",
        gerund="wriggling down the path",
        mess="pooey",
        soil="pooey and pale",
        keyword="serpent",
        rhyme_a="glide",
        rhyme_b="slide",
        tags={"serpent", "pooey"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing by the pond",
        gerund="singing by the pond",
        mess="muddy",
        soil="muddy and soft",
        keyword="twist",
        rhyme_a="song",
        rhyme_b="long",
        tags={"song", "twist"},
    ),
}

REMEDIES = {
    "bath": Remedy(
        id="bath",
        label="a warm bath",
        prep="take a warm bath first",
        tail="stopped to scrub and scrub until the day felt bright",
        clears={"pooey", "muddy"},
    ),
    "wipe": Remedy(
        id="wipe",
        label="a soft wipe",
        prep="wipe the tail with a soft cloth",
        tail="wiped away the sticky speck and skipped on with glee",
        clears={"pooey"},
    ),
    "leaf": Remedy(
        id="leaf",
        label="a big leaf",
        prep="use a big leaf as a wrap",
        tail="wrapped the tail in green and neat and laughed a little squeak",
        clears={"muddy"},
    ),
}

NAMES = ["Sera", "Nia", "Milo", "Pip", "Rosa", "Toby", "Luna", "Bea"]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def reasonableness_gate(place: Place, activity: Activity, remedy: Remedy) -> bool:
    if activity.mess not in remedy.clears:
        return False
    if activity.id not in place.affords:
        return False
    return True


def explain_rejection(place: Place, activity: Activity, remedy: Remedy) -> str:
    return (
        f"(No story: {remedy.label} does not reasonably help with {activity.mess} at {place.label}.)"
    )


def predict_soil(world: World, hero: Entity, activity: Activity) -> bool:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    hero2.meters[activity.mess] = hero2.meters.get(activity.mess, 0) + 1
    return hero2.meters[activity.mess] >= 1


def _do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0) + 1
    hero.memes["uneasy"] = hero.memes.get("uneasy", 0) + 1
    world.trace.append(f"{hero.id} got {activity.mess}")


def tell(place: Place, activity: Activity, remedy: Remedy, name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="serpent", label="serpent"))
    cloth = world.add(Entity(id="cloak", type="cloth", label="tail cloak", caretaker=hero.id))
    world.facts.update(hero=hero, cloth=cloth, activity=activity, remedy=remedy, place=place)

    world.say(f"{hero.id} was a little serpent who liked to {activity.verb} by the sun.")
    world.say(f"{place.scene}")
    world.say(f"{hero.id} hummed, 'I glide with pride, I shine inside.'")

    world.para()
    world.say(
        f"Then {hero.id} found a gooey trail and took a quick look."
    )
    world.say(
        f"'Oh no,' thought {hero.id}. 'If I wriggle there, I'll end up {activity.soil}, and that's a sad, sad nook.'"
    )
    if predict_soil(world, hero, activity):
        world.say(
            f"{hero.id} frowned and sighed, because the path looked pooey and sticky too."
        )

    world.para()
    world.say(
        f"{hero.id}'s friend offered {remedy.label} and said, 'We can {remedy.prep}.'"
    )
    if reasonableness_gate(place, activity, remedy):
        hero.memes["hope"] = hero.memes.get("hope", 0) + 1
        world.say(f"{hero.id} thought, 'A clean little plan is a lovely little span.'")
        hero.meters[activity.mess] = 0
        world.say(f"They {remedy.tail}.")
        if activity.id == "wriggle":
            world.say(
                f"So {hero.id} could {activity.verb} in a neat green beat, and the twist was this:"
            )
            world.say(
                f"the sticky trail was not poo at all, but berry jam from a picnic cart. What a surprise, what a treat!"
            )
        else:
            world.say(
                f"So {hero.id} could {activity.gerund} with a happy little song, and the twist was this:"
            )
            world.say(
                f"the muddy patch was really a place where tadpoles splashed along. The worry was wrong all along!"
            )
        hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    else:
        raise StoryError(explain_rejection(place, activity, remedy))

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    remedy = f["remedy"]
    return [
        f"Write a rhyming story about a serpent named {hero.id} who wants to {activity.verb} but meets a sticky surprise.",
        f"Tell a child-friendly rhyming tale with an inner monologue where {hero.id} worries about getting {activity.soil}, then finds a gentle fix.",
        f"Write a short story using the words serpent, suffer, and pooey, and end with a twist that changes the meaning of the mess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    remedy = f["remedy"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little serpent who wants to {activity.verb} at {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} worry about in the middle of the story?",
            answer=f"{hero.id} worried about ending up {activity.soil} if {hero.id} kept going down the sticky path.",
        ),
        QAItem(
            question=f"How did the helper solve the problem?",
            answer=f"The helper offered {remedy.label}, and that let {hero.id} stay clean enough to keep playing.",
        ),
        QAItem(
            question=f"What was the twist?",
            answer="The pooey-looking trail was not something bad at all; it turned out to be sweet berry jam from a picnic cart.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a serpent?",
            answer="A serpent is a snake. It has a long body and moves by slithering along the ground.",
        ),
        QAItem(
            question="What does suffer mean?",
            answer="To suffer means to have a hard or unpleasant time, like feeling worried, stuck, or uncomfortable.",
        ),
        QAItem(
            question="What does pooey mean?",
            answer="Pooey means sticky, smelly, or yucky in a child-friendly way.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes how you understand what is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- act(A).
remedy(R) :- fix(R).

valid(P,A,R) :- afford(P,A), clears(R,M), mess(A,M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("afford", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("act", aid))
        lines.append(asp.fact("mess", aid, a.mess))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("fix", rid))
        for m in sorted(r.clears):
            lines.append(asp.fact("clears", rid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for aid, a in ACTIVITIES.items():
            for rid, r in REMEDIES.items():
                if reasonableness_gate(p, a, r):
                    combos.append((pid, aid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming serpent storyworld with a sticky twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.activity or args.remedy:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.activity is None or c[1] == args.activity)
            and (args.remedy is None or c[2] == args.remedy)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, remedy = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, activity=activity, remedy=remedy, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ACTIVITIES[params.activity], REMEDIES[params.remedy], params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts.keys()}")
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
    StoryParams(place="garden", activity="wriggle", remedy="wipe", name="Sera"),
    StoryParams(place="yard", activity="wriggle", remedy="bath", name="Milo"),
    StoryParams(place="pond", activity="sing", remedy="leaf", name="Luna"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
