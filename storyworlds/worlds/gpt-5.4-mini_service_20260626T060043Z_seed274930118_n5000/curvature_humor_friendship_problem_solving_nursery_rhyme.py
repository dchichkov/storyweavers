#!/usr/bin/env python3
"""
A small story world about curvature, friendship, humor, and problem solving,
told in a nursery-rhyme style.

Premise:
- A child and a friend are carrying something along a curved little bridge or path.
- The curve makes things funny and tricky.
- They solve the problem together with a clever, gentle fix.

The world is deliberately simple and state-driven:
- Physical meters track tilt, bend, wobble, and carried weight.
- Emotional memes track joy, worry, humor, and friendship.
- The ending image proves the change: the curved path is still curved, but the
  characters have learned how to cross it safely and happily.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
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
class Place:
    name: str
    curved: bool = False
    curve_kind: str = "bend"
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    burden: str
    fixable_by: str
    risk: str
    place: str


@dataclass
class StoryParams:
    place: str
    object_id: str
    name: str
    friend_name: str
    gender: str
    friend_gender: str
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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("wobble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["wobble"] = ent.meters.get("wobble", 0.0) + 1
        out.append(f"{ent.label} felt a little wobble in their knees.")
    return out


def _r_lift_help(world: World) -> list[str]:
    out: list[str] = []
    carrier = world.entities.get("child")
    friend = world.entities.get("friend")
    bundle = world.entities.get("bundle")
    if not carrier or not friend or not bundle:
        return out
    if carrier.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("help", "lift")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    carrier.memes["worry"] = max(0.0, carrier.memes.get("worry", 0.0) - 1)
    friend.memes["kindness"] = friend.memes.get("kindness", 0.0) + 1
    carrier.memes["friendship"] = carrier.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    bundle.meters["care"] = bundle.meters.get("care", 0.0) + 1
    out.append("So their friend gave a helpful hand, and the load grew light.")
    return out


CAUSAL_RULES = [_r_wobble, _r_lift_help]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
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


SETTINGS = {
    "hill": Place(name="the curved little hill", curved=True, curve_kind="bend", affords={"carry"}),
    "bridge": Place(name="the curly little bridge", curved=True, curve_kind="arch", affords={"carry"}),
    "path": Place(name="the winding little path", curved=True, curve_kind="turn", affords={"carry"}),
}

OBJECTS = {
    "basket": ObjectDef(
        id="basket",
        label="basket",
        phrase="a small basket of berries",
        burden="heavy",
        fixable_by="two hands",
        risk="spill",
        place="path",
    ),
    "kite": ObjectDef(
        id="kite",
        label="kite",
        phrase="a kite with a long string",
        burden="tangled",
        fixable_by="a steady hand",
        risk="twirl",
        place="hill",
    ),
    "teacup": ObjectDef(
        id="teacup",
        label="teacup",
        phrase="a tiny teacup and saucer",
        burden="wobbly",
        fixable_by="a slow step",
        risk="slosh",
        place="bridge",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Rose", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Theo", "Noah", "Eli"]


def nursery_opening(place: Place, obj: ObjectDef) -> str:
    if place.curved:
        return f"Over {place.name}, where the stones all curl, a small {obj.label} wished not to spill or whirl."
    return f"On {place.name}, so soft and wide, a small {obj.label} went side by side."


def tell(place: Place, obj: ObjectDef, hero_name: str, friend_name: str, gender: str, friend_gender: str) -> World:
    world = World(place)

    child = world.add(Entity(id="child", kind="character", type=gender, label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name))
    bundle = world.add(Entity(id="bundle", kind="thing", type=obj.label, label=obj.label, phrase=obj.phrase, owner="child"))

    child.meters["carrying"] = 1
    bundle.meters["weight"] = 1
    if place.curved:
        child.meters["bend"] = 1
        friend.meters["bend"] = 1

    world.say(
        f"{hero_name} and {friend_name} were two small friends with bright-eyed grins, "
        f"and they loved to walk where the curly road begins."
    )
    world.say(nursery_opening(place, obj))
    world.say(
        f"They sang a tiny rhyme: 'Tip-tap, clip-clap, careful on the way; "
        f"we'll cross the curve together and laugh the bumps away.'"
    )

    world.para()
    world.say(
        f"But when they came to the bend, the {obj.label} leaned and swayed, "
        f"for curved paths make straight little feet behave in a swirly way."
    )
    child.memes["worry"] = 1
    child.memes["humor"] = 1
    friend.memes["humor"] = 1
    world.say(
        f"{hero_name} giggled, 'My toes are doing a noodle dance!' and {friend_name} laughed too, "
        f"though the {obj.label} was still a bit too {obj.burden}."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{friend_name} looked at the curve and said, 'Two small hands may do the trick; "
        f"if we carry low and slow, our load won't slip or kick.'"
    )
    child.meters["careful"] = child.meters.get("careful", 0.0) + 1
    friend.meters["careful"] = friend.meters.get("careful", 0.0) + 1
    world.say(
        f"So they held the {obj.label} between them, one on each side, and walked like a bunny hop "
        f"with a turtle's patient stride."
    )
    propagate(world, narrate=True)

    world.para()
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    child.memes["friendship"] = child.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    bundle.meters["steady"] = 1
    world.say(
        f"At the far side of the curve, the {obj.label} stayed safe and sound, "
        f"and the little friends were smiling all around."
    )
    world.say(
        f"The bend was still bendy, the day was still bright, but their clever plan had made the crossing right."
    )

    world.facts.update(
        child=child,
        friend=friend,
        bundle=bundle,
        place=place,
        object=obj,
        resolved=True,
        humorous=True,
        friendship=True,
        problem_solving=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    obj = f["object"]
    return [
        f'Write a short nursery-rhyme story about {child.label} and {friend.label} on a curved path with a {obj.label}.',
        f"Tell a gentle story where two friends solve a little problem on {world.place.name} and keep it funny.",
        f'Write a child-friendly rhyme that includes a curved road, a shared burden, and a happy fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    obj = f["object"]
    place = f["place"]
    qa = [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {child.label} and {friend.label}, two small friends who travel together.",
        ),
        QAItem(
            question=f"What made the walk tricky on {place.name}?",
            answer=f"The curved shape of {place.name} made the {obj.label} sway, so carrying it was a little hard.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They held the {obj.label} together, moved slowly, and used both of their small hands so it would stay steady.",
        ),
        QAItem(
            question=f"What funny thing helped them stay brave?",
            answer=f"They laughed about their silly feet and kept the mood light, which made the problem feel smaller.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="What changed by the end of the story?",
                answer=f"By the end, the {obj.label} was safe, the friends felt closer, and the curved path was no longer a worry.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a curve?",
            answer="A curve is a shape that bends instead of going perfectly straight.",
        ),
        QAItem(
            question="Why can a curved path be tricky to carry across?",
            answer="A curved path can make a load tip or sway, so careful hands and slow steps help.",
        ),
        QAItem(
            question="What does friendship help people do?",
            answer="Friendship helps people share work, solve little problems, and feel cheerful together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  place={world.place.name} curved={world.place.curved} curve_kind={world.place.curve_kind}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", object_id="kite", name="Mia", friend_name="Leo", gender="girl", friend_gender="boy"),
    StoryParams(place="bridge", object_id="teacup", name="Nora", friend_name="Ava", gender="girl", friend_gender="girl"),
    StoryParams(place="path", object_id="basket", name="Finn", friend_name="Maya", gender="boy", friend_gender="girl"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.curved:
            lines.append(asp.fact("curved", pid, place.curve_kind))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("risk", oid, obj.risk))
        lines.append(asp.fact("fixable_by", oid, obj.fixable_by))
        lines.append(asp.fact("at_place", oid, obj.place))
    return "\n".join(lines)


ASP_RULES = r"""
curvature(Place) :- curved(Place, _).
problem(Place, Obj) :- curvature(Place), object(Obj), at_place(Obj, Place).
humor(Place, Obj) :- problem(Place, Obj), risk(Obj, _).
friendship(Child, Friend) :- child(Child), companion(Friend).
solution(Place, Obj) :- problem(Place, Obj), fixable_by(Obj, _).
story_ok(Place, Obj) :- problem(Place, Obj), humor(Place, Obj), solution(Place, Obj).
#show story_ok/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = {(p, o) for p in SETTINGS for o, obj in OBJECTS.items() if SETTINGS[p].curved and obj.place == p}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP parity matches Python gate ({len(py)} cases).")
        return 0
    print("MISMATCH:")
    print(" python only:", sorted(py - cl))
    print(" asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme curvature story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    place_id = args.place or rng.choice(list(SETTINGS))
    obj_id = args.object_id or rng.choice([oid for oid, o in OBJECTS.items() if o.place == place_id])
    obj = OBJECTS[obj_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    if SETTINGS[place_id].name != obj.place and args.object_id:
        raise StoryError("That object does not belong on that place in this story world.")
    return StoryParams(
        place=place_id,
        object_id=obj_id,
        name=name,
        friend_name=friend_name,
        gender=gender,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    obj = OBJECTS[params.object_id]
    world = tell(place, obj, params.name, params.friend_name, params.gender, params.friend_gender)
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
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks in --verify.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
