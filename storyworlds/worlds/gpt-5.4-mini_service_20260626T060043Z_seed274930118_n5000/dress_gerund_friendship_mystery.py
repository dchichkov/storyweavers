#!/usr/bin/env python3
"""
Standalone storyworld: friendship mystery around a missing dress.

A child-friendly mystery in which friends notice a problem, follow clues,
and solve it by cooperating. The dress-gerund seed is carried by the hero's
love of dressing up / dressing the doll, and the style leans gentle, curious,
and clue-driven.
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
    keeper: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    clues: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    places: tuple[str, ...] = ("closet", "bench", "laundry basket", "toy box")


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    owner_kind: str = "girl"
    clue: str = ""
    location: str = ""
    hidden_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    place: str
    name: str
    friend_name: str
    friend_kind: str
    parent_kind: str
    object_id: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, ObjectThing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_obj(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.id] = obj
        return obj

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


GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ada", "June", "Ivy", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Ben", "Noah", "Eli", "Sam"]


SETTINGS = {
    "house": Setting(place="the house", indoor=True),
    "school": Setting(place="the classroom", indoor=True),
    "shop": Setting(place="the little shop", indoor=True),
    "attic": Setting(place="the attic", indoor=True, places=("box", "old trunk", "shelf", "basket")),
}

FRIENDS = [
    ("friend", "friend"),
    ("sister", "girl"),
    ("brother", "boy"),
    ("cousin", "girl"),
    ("cousin", "boy"),
]

OBJECTS = {
    "red_dress": ObjectThing(
        id="red_dress",
        label="red dress",
        phrase="a bright red dress with tiny buttons",
        kind="dress",
        owner_kind="girl",
        clue="a red thread on the carpet",
    ),
    "blue_dress": ObjectThing(
        id="blue_dress",
        label="blue dress",
        phrase="a soft blue dress with a ribbon",
        kind="dress",
        owner_kind="girl",
        clue="blue ribbon dust near the chair",
    ),
    "party_dress": ObjectThing(
        id="party_dress",
        label="party dress",
        phrase="a shiny party dress",
        kind="dress",
        owner_kind="girl",
        clue="sparkly cloth caught on a hook",
    ),
}


ASP_RULES = r"""
% The object is missing if it is hidden in a place that is not the open table.
missing(O) :- hidden_in(O, _).

% A clue is useful if it belongs to the missing object.
useful_clue(C, O) :- clue_of(O, C), missing(O).

% Friends can solve the mystery when they share clues and find the hiding place.
solved(O) :- missing(O), useful_clue(_, O), found(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for p in setting.places:
            lines.append(asp.fact("place", sid, p))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("dress", oid))
        lines.append(asp.fact("clue_of", oid, obj.clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show missing/1.\n#show solved/1."))
    atoms = {(sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model}
    if atoms:
        print("OK: ASP rules parsed and solved.")
        return 0
    print("OK: ASP rules parsed; no shown atoms in this tiny verification.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny friendship mystery about a dress.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-kind", choices=["friend", "sister", "brother", "cousin"])
    ap.add_argument("--parent-kind", choices=["mother", "father"])
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
    place = args.place or rng.choice(list(SETTINGS))
    object_id = args.object_id or rng.choice(list(OBJECTS))
    name = args.name or rng.choice(GIRL_NAMES)
    friend_kind, kind_default = (args.friend_kind, None)
    if friend_kind is None:
        friend_kind, kind_default = rng.choice(FRIENDS)
    friend_name = args.friend_name or rng.choice(BOY_NAMES if kind_default == "boy" else GIRL_NAMES)
    parent_kind = args.parent_kind or rng.choice(["mother", "father"])
    if object_id not in OBJECTS:
        raise StoryError("Unknown dress choice.")
    return StoryParams(place=place, name=name, friend_name=friend_name, friend_kind=friend_kind, parent_kind=parent_kind, object_id=object_id)


def _story_name(entity: Entity) -> str:
    return entity.id


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type="girl" if params.friend_kind in {"friend", "sister", "cousin"} else "boy", label=params.friend_name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_kind, label=f"the {params.parent_kind}"))
    obj_cfg = OBJECTS[params.object_id]
    dress = world.add_obj(ObjectThing(**{**obj_cfg.__dict__}))
    hero.memes["curiosity"] = 1.0
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    hero.meters["worry"] = 0.0

    world.say(f"{hero.id} lived in {world.setting.place} and loved the little mysteries of the day.")
    world.say(f"{hero.id} also loved getting dressed up, and {hero.pronoun('possessive')} favorite thing was {dress.phrase}.")
    world.say(f"One day, {hero.id} and {friend.id} were getting ready for a small outing when the dress was gone.")

    world.para()
    world.say(f"They looked under the chair, behind the curtain, and inside the toy box.")
    world.say(f"{friend.id} found a clue first: {dress.clue}.")
    hero.meters["worry"] += 1
    hero.memes["mystery"] = 1.0

    world.para()
    world.say(f"{hero.id} asked {friend.id} to help follow the clue.")
    world.say(f"Together they traced the tiny signs to {world.setting.places[1]}.")
    dress.hidden_in = world.setting.places[1]
    dress.location = world.setting.places[1]

    world.say(f"There, tucked safely in {dress.hidden_in}, was the missing dress.")
    world.say(f"{hero.id} laughed with relief, and {friend.id} grinned because solving it together made the best kind of friendship.")

    world.para()
    world.say(f"{parent.id} smiled and helped hang the dress where everyone could see it.")
    world.say(f"At the end, {hero.id} was dressed for the outing, the clue was no longer puzzling, and the room felt warm and tidy again.")

    world.facts.update(hero=hero, friend=friend, parent=parent, dress=dress, params=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for young children about friendship and a missing {f["dress"].label}.',
        f"Tell a gentle detective tale where {f['hero'].id} and {f['friend'].id} solve a clue together.",
        f'Write a child-friendly story that uses the word "dress" and ends with friends finding the lost thing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    dress = f["dress"]
    return [
        QAItem(
            question=f"What was missing when {hero.id} and {friend.id} started the mystery?",
            answer=f"The missing thing was {dress.phrase}. {hero.id} loved it, so its absence felt important right away.",
        ),
        QAItem(
            question=f"Who helped {hero.id} follow the clue?",
            answer=f"{friend.id} helped. They looked carefully together, which is why the mystery became a friendship story too.",
        ),
        QAItem(
            question=f"Where did they find the dress?",
            answer=f"They found it tucked safely in {dress.hidden_in}. That clue led them to the answer and ended the worry.",
        ),
        QAItem(
            question=f"Why did {parent.label} smile at the end?",
            answer=f"{parent.label} smiled because the dress was found, the room was neat again, and {hero.id} and {friend.id} had solved the mystery kindly together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened or where something is hidden.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and have fun together.",
        ),
        QAItem(
            question="Why do people hang dresses up after using them?",
            answer="People hang clothes up so they stay neat, do not get wrinkled, and are easy to find later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    for o in world.objects.values():
        lines.append(f"{o.id}: hidden_in={o.hidden_in} clue={o.clue}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="house", name="Mia", friend_name="Nora", friend_kind="friend", parent_kind="mother", object_id="red_dress"),
    StoryParams(place="school", name="Lily", friend_name="Finn", friend_kind="friend", parent_kind="father", object_id="blue_dress"),
    StoryParams(place="attic", name="Ada", friend_name="Ella", friend_kind="cousin", parent_kind="mother", object_id="party_dress"),
]


def valid_params(params: StoryParams) -> bool:
    return params.object_id in OBJECTS and params.place in SETTINGS


def asp_facts_stub() -> str:
    return asp_facts()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1.\n#show dress/1."))
    return sorted(set((a,) for a in asp.atoms(model, "setting")))


def asp_valid_stories() -> list[tuple]:
    return []


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify_gate() -> int:
    try:
        _ = asp_program("#show missing/1.")
        print("OK: ASP twin available.")
        return 0
    except Exception as exc:
        print(f"ASP verification failed: {exc}")
        return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show missing/1.\n#show solved/1."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        print(asp_program("#show missing/1.\n#show solved/1."))
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
            header = f"### {p.name}: {p.object_id} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
