#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/helmet_elevator_foreshadowing_friendship_myth.py
=================================================================================

A standalone storyworld for a tiny myth-like tale set in an elevator: a child
finds a helmet, receives a small omen, and with a friend's help turns worry into
trust and a safe ride.

The world is built from typed entities with physical meters and emotional memes.
The simulated state drives the prose: the elevator can stall, a helmet can shift
from odd object to meaningful protection, and a friendship can change the way the
ending feels.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/helmet_elevator_foreshadowing_friendship_myth.py
    python storyworlds/worlds/gpt-5.4-mini/helmet_elevator_foreshadowing_friendship_myth.py --all
    python storyworlds/worlds/gpt-5.4-mini/helmet_elevator_foreshadowing_friendship_myth.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/helmet_elevator_foreshadowing_friendship_myth.py --trace --qa
    python storyworlds/worlds/gpt-5.4-mini/helmet_elevator_foreshadowing_friendship_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""        # seeker, friend, elder, place, object
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    protective: bool = False
    wise_sign: bool = False
    risky: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    elder: str
    elder_gender: str
    helmet: str
    elevator: str
    sign: str
    omen: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


CHILD_NAMES = ["Milo", "Nia", "Lina", "Arlo", "Tess", "Ezra", "Oona", "Iris"]
FRIEND_NAMES = ["Bea", "Jonah", "Kai", "Rumi", "Pia", "Soren", "Mara", "Leo"]
ELDER_NAMES = ["Aunt Sera", "Uncle Ben", "Grandma Asha", "Grandpa Eli"]
SIGNS = [
    "the lights trembled like stars behind clouds",
    "the floor hummed softly under their feet",
    "a tiny bell gave one lonely ring",
    "the cable gave a low singing note",
]
OMENS = [
    "a whisper of trouble",
    "a hint that the ride was not ordinary",
    "a small warning from the quiet air",
    "a sign that the day wanted patience",
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("elevator", "helmet", "friendship")]


ASP_RULES = r"""
valid(E, H, F) :- setting(E), word(H), feature(F), E = elevator, H = helmet, F = friendship.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "elevator"),
        asp.fact("word", "helmet"),
        asp.fact("feature", "friendship"),
    ])


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def reasonableness_gate(params: StoryParams) -> None:
    if params.elevator != "elevator":
        raise StoryError("This world only tells stories in an elevator.")
    if params.helmet != "helmet":
        raise StoryError("This world needs the word helmet.")
    if params.sign not in SIGNS:
        raise StoryError("Unknown omen-sign.")
    if params.child == params.friend or params.child == params.elder or params.friend == params.elder:
        raise StoryError("The characters must be distinct.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like elevator storyworld with foreshadowing and friendship.")
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDER_NAMES)
    ap.add_argument("--elder-gender", choices=["girl", "boy"])
    ap.add_argument("--helmet", default="helmet")
    ap.add_argument("--elevator", default="elevator")
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--omen", choices=OMENS)
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
    if args.elevator and args.elevator != "elevator":
        raise StoryError("This world only tells stories in an elevator.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILD_NAMES)
    friend_pool = [n for n in FRIEND_NAMES if n != child]
    friend = args.friend or rng.choice(friend_pool)
    elder = args.elder or rng.choice(ELDER_NAMES)
    omen = args.omen or rng.choice(OMENS)
    sign = args.sign or rng.choice(SIGNS)
    params = StoryParams(child, child_gender, friend, friend_gender, elder, "adult", args.helmet or "helmet", args.elevator or "elevator", sign, omen)
    reasonableness_gate(params)
    return params


def prophecy(world: World, child: Entity, sign: str, omen: str) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"In the old building, {child.id} stepped into the elevator with {child.label_word} in hand. "
        f"Before the doors closed, {sign}; it felt like {omen}."
    )


def friendship(world: World, child: Entity, friend: Entity) -> None:
    child.memes["trust"] += 1
    friend.memes["loyalty"] += 1
    world.say(
        f"{friend.id} smiled at {child.id} and stood beside {child.pronoun('object')} like a true friend. "
        f'"If the ride grows strange," {friend.id} said, "we stay together."'
    )


def enter_elevator(world: World, child: Entity, friend: Entity, elder: Entity, elevator: Entity) -> None:
    child.meters["inside"] += 1
    friend.meters["inside"] += 1
    elder.meters["inside"] += 1
    elevator.meters["closed"] += 1
    world.say(
        f"{child.id}, {friend.id}, and {elder.id} rode the elevator up toward the quiet rooms above. "
        f"The doors shut like a careful gate."
    )


def foreshadow(world: World, elevator: Entity, sign: str) -> None:
    elevator.meters["worry"] += 1
    world.say(
        f"The {elevator.label_word} gave a soft shiver, and {sign}. "
        f"No one spoke, but the little warning stayed in the air."
    )


def stall_rule(world: World) -> list[str]:
    out = []
    elevator = world.get("elevator")
    if elevator.meters["worry"] < THRESHOLD:
        return out
    sig = ("stall",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    elevator.meters["stalled"] += 1
    for ent in list(world.entities.values()):
        if ent.kind == "character":
            ent.memes["surprise"] += 1
    out.append("__stall__")
    return out


def rescue_rule(world: World) -> list[str]:
    out = []
    helmet = world.get("helmet")
    if helmet.meters["used"] < THRESHOLD:
        return out
    sig = ("safe",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("elevator").meters["safe"] += 1
    out.append("__safe__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for fn in (stall_rule, rescue_rule):
            got = fn(world)
            if got:
                changed = True
                produced.extend([g for g in got if not g.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def stall(world: World, elevator: Entity) -> None:
    propagate(world, narrate=False)
    elevator.meters["stalled"] += 1
    world.say(
        f"At once the elevator stopped between floors. The numbers above the door faded, and the room held its breath."
    )


def use_helmet(world: World, child: Entity, helmet: Entity) -> None:
    helmet.meters["used"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} lifted the helmet and put it on. It was odd in an elevator, but it made the child stand taller."
    )


def elder_speaks(world: World, elder: Entity, child: Entity, friend: Entity, helmet: Entity) -> None:
    elder.memes["calm"] += 1
    world.say(
        f"{elder.id} did not panic. {elder.id} only said, "
        f'"A true ride tests courage, and friends make courage easier to carry."'
    )
    world.say(
        f"{elder.id} nodded at the helmet. " 
        f'"Keep it on if it helps you remember to breathe."'
    )


def repair_and_release(world: World, elevator: Entity, child: Entity, friend: Entity, elder: Entity) -> None:
    elevator.meters["safe"] += 1
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"Then the light returned with a small click, the doors opened, and the elevator began to move again."
    )
    world.say(
        f"{child.id} laughed first, then {friend.id}, and even {elder.id} smiled as they stepped out together."
    )
    world.say(
        f"From that day on, the helmet was remembered as a lucky sign, and the friendship between {child.id} and {friend.id} felt stronger than the little fear."
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.child, kind="character", type=params.child_gender, role="seeker"))
    friend = world.add(Entity(params.friend, kind="character", type=params.friend_gender, role="friend"))
    elder = world.add(Entity(params.elder, kind="character", type="adult", role="elder"))
    elevator = world.add(Entity("elevator", kind="place", type="place", label="elevator", role="place"))
    helmet = world.add(Entity("helmet", kind="thing", type="thing", label="helmet", protective=True, wise_sign=True))
    child.memes["hope"] = 1
    friend.memes["loyalty"] = 1
    world.facts["helmet"] = helmet
    world.facts["child"] = child
    world.facts["friend"] = friend
    world.facts["elder"] = elder
    world.facts["elevator"] = elevator

    prophecy(world, child, params.sign, params.omen)
    friendship(world, child, friend)
    world.para()
    enter_elevator(world, child, friend, elder, elevator)
    foreshadow(world, elevator, params.sign)
    child.memes["fear"] += 1
    friend.memes["fear"] += 1
    stall(world, elevator)
    world.para()
    use_helmet(world, child, helmet)
    elder_speaks(world, elder, child, friend, helmet)
    repair_and_release(world, elevator, child, friend, elder)
    world.facts["ended_safe"] = elevator.meters["safe"] >= THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, fr = f["child"], f["friend"]
    return [
        f'Write a myth-like story in an elevator that includes the word "helmet" and a small omen before the good ending.',
        f"Tell a friendship story where {c.id} and {fr.id} share a strange ride in an elevator, notice a warning sign, and stay brave together.",
        f"Write a child-friendly myth about a helmet becoming a lucky sign during an elevator ride.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, fr, el = f["child"], f["friend"], f["elder"]
    qa = [
        ("Who are the main characters?",
         f"The story is about {c.id}, {fr.id}, and {el.id}. {c.id} and {fr.id} are friends, and {el.id} helps them stay calm."),
        ("What warning did they notice?",
         f"They noticed a small omen in the elevator: {world.get('elevator').label_word} shivered and {world.get('elevator').meters['worry']} became enough to matter. The sign made them careful before anything worse happened."),
        ("What did the helmet do in the story?",
         f"The helmet became a lucky and brave thing for {c.id} to wear. It did not fix the elevator by magic, but it helped {c.id} remember to stay calm and trust {fr.id}."),
        ("How did the story end?",
         f"The elevator started moving again, and all three stepped out safely. The ending shows that friendship and calm courage carried them through the strange ride."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is an elevator?",
         "An elevator is a machine that carries people up and down in a building. It moves between floors so people do not need to use stairs."),
        ("What is a helmet?",
         "A helmet is a hard piece of protective gear worn on the head. It helps keep the head safe."),
        ("What is a foreshadowing sign?",
         "A foreshadowing sign is a little hint that something important may happen soon. Stories use it to prepare the reader for what comes next."),
        ("What does friendship mean?",
         "Friendship means caring about someone, helping them, and staying beside them when things feel strange or hard."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append("protective=True")
        if e.wise_sign:
            bits.append("wise_sign=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Milo", "boy", "Bea", "girl", "Aunt Sera", "adult", "helmet", "elevator", SIGNS[0], OMENS[0]),
    StoryParams("Nia", "girl", "Kai", "boy", "Grandma Asha", "adult", "helmet", "elevator", SIGNS[2], OMENS[2]),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def explain_rejection() -> str:
    return "(No story: this world only tells the helmet-in-the-elevator myth.)"


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combo).")
    else:
        ok = 1
        print("MISMATCH between ASP and Python combo gates.")
        print("python:", sorted(py))
        print("asp:", sorted(cl))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        ok = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return ok


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.elevator and args.elevator != "elevator":
        raise StoryError("This world only tells stories in an elevator.")
    if args.helmet and args.helmet != "helmet":
        raise StoryError("This world needs the word helmet.")
    return StoryParams(
        child=args.child or rng.choice(CHILD_NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        friend=args.friend or rng.choice(FRIEND_NAMES),
        friend_gender=args.friend_gender or rng.choice(["girl", "boy"]),
        elder=args.elder or rng.choice(ELDER_NAMES),
        elder_gender="adult",
        helmet="helmet",
        elevator="elevator",
        sign=args.sign or rng.choice(SIGNS),
        omen=args.omen or rng.choice(OMENS),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
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
        header = ""
        if args.all:
            header = f"### {sample.params.child} and {sample.params.friend}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
