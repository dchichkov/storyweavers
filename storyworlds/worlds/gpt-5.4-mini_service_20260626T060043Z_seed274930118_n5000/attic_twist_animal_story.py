#!/usr/bin/env python3
"""
storyworlds/worlds/attic_twist_animal_story.py
==============================================

A small animal storyworld set in an attic, with a gentle twist.

Premise:
- An animal child wants to explore a dusty attic.
- A parent or helper worries about a fragile, forgotten object.
- The child discovers something surprising in the attic.
- The surprise changes the plan from trouble into a happy small adventure.

This world keeps the style close to an Animal Story: concrete animals, simple
feelings, soft conflict, and a twist that comes from the simulated world state.
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
    room: str = ""
    fragile: bool = False
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "scratch": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "joy": 0.0, "surprise": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"cat", "rabbit", "squirrel", "mouse", "fox"}
        male = {"dog", "bear", "badger", "owl", "frog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the attic"
    affords: set[str] = field(default_factory=lambda: {"search", "tidy", "peek"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    weather: str
    keyword: str
    twist: str


@dataclass
class Prize:
    label: str
    phrase: str
    room: str
    fragile: bool = False


@dataclass
class StoryParams:
    activity: str
    prize: str
    animal: str
    gender: str
    parent: str
    name: str
    seed: Optional[int] = None


THRESHOLD = 1.0


ANIMALS = {
    "cat": {"genders": {"girl"}, "names": ["Mimi", "Luna", "Pip", "Nora", "Cleo"]},
    "dog": {"genders": {"boy"}, "names": ["Toby", "Milo", "Rex", "Finn", "Otis"]},
    "rabbit": {"genders": {"girl"}, "names": ["Bea", "Daisy", "Poppy", "Ivy", "Lulu"]},
    "mouse": {"genders": {"girl", "boy"}, "names": ["Nib", "Tia", "Bun", "Mop", "Squeak"]},
    "fox": {"genders": {"boy"}, "names": ["Rory", "Jasper", "Theo", "Arlo", "Moss"]},
    "squirrel": {"genders": {"girl", "boy"}, "names": ["Hazel", "Nut", "Skippy", "Tess", "Wren"]},
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="search the attic",
        gerund="searching the attic",
        rush="scurry toward the old trunk",
        mess="dust",
        weather="quiet",
        keyword="attic",
        twist="a hidden hatch",
    ),
    "tidy": Activity(
        id="tidy",
        verb="tidy the attic",
        gerund="tidying the attic",
        rush="hurry to the boxes",
        mess="dust",
        weather="quiet",
        keyword="attic",
        twist="a loose curtain",
    ),
    "peek": Activity(
        id="peek",
        verb="peek behind the trunk",
        gerund="peeking behind trunks",
        rush="tiptoe to the corner",
        mess="dust",
        weather="quiet",
        keyword="attic",
        twist="a little door",
    ),
}

PRIZES = {
    "blanket": Prize(label="blanket", phrase="a soft old blanket", room="shelf", fragile=False),
    "photo": Prize(label="photo", phrase="a framed family photo", room="box", fragile=True),
    "toy": Prize(label="toy", phrase="a tiny wind-up toy", room="trunk", fragile=True),
    "hat": Prize(label="hat", phrase="a warm wool hat", room="hook", fragile=False),
}

SETTINGS = {"attic": Setting()}

CURATED = [
    StoryParams(activity="search", prize="toy", animal="mouse", gender="girl", parent="mother", name="Mimi"),
    StoryParams(activity="peek", prize="photo", animal="fox", gender="boy", parent="father", name="Rory"),
    StoryParams(activity="tidy", prize="blanket", animal="rabbit", gender="girl", parent="mother", name="Poppy"),
    StoryParams(activity="search", prize="hat", animal="squirrel", gender="boy", parent="father", name="Skippy"),
]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


def can_story(activity: Activity, prize: Prize) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, act_id, prize_id) for place in SETTINGS for act_id in ACTIVITIES for prize_id in PRIZES if can_story(ACTIVITIES[act_id], PRIZES[prize_id])]


def _dust(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.kind != "character":
            continue
        if e.meters["dust"] >= THRESHOLD and ("dust", e.id) not in world.fired:
            world.fired.add(("dust", e.id))
            e.memes["surprise"] += 1
            out.append(f"{e.name if hasattr(e, 'name') else e.id} sneezed softly in the dust.")
    return out


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, animal: str, parent_type: str) -> World:
    w = World(setting)
    child = w.add(Entity(id=name, kind="character", type=animal, label=name))
    parent = w.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = w.add(Entity(id="prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=parent.id, room=prize_cfg.room, fragile=prize_cfg.fragile))

    child.memes["curiosity"] += 1
    w.say(f"{child.id} was a little {child.type} who loved tiny adventures.")
    w.say(f"{child.id} liked the attic because {activity.keyword} hid in every corner.")
    w.say(f"One day, {child.id}'s {parent.label} pointed at {prize.phrase} and said to be gentle with it.")

    w.para()
    w.say(f"{child.id} wanted to {activity.verb}, but the attic was full of old dust.")
    child.meters["dust"] += 1
    w.say(f"{child.id} could feel the dust puff up around {child.pronoun('possessive')} paws.")
    parent.memes["worry"] += 1
    w.say(f'"Be careful," {parent.pronoun()} said. "That {prize.label} is a little fragile."')

    w.para()
    child.memes["curiosity"] += 1
    w.say(f"{child.id} {activity.rush}, and then something surprising happened.")
    if prize_cfg.fragile:
        prize.meters["found"] += 1
        child.memes["surprise"] += 1
        w.say(f"Behind the trunk, {child.id} found {prize.phrase} and a small note tucked under it.")
        w.say(f"The note showed that the attic had been hiding {activity.twist} all along.")
        w.say(f"{child.id} smiled, because the little surprise made the attic feel friendly instead of scary.")
    else:
        w.say(f"Instead of a mess, {child.id} found {prize.phrase} hanging neatly where nobody had seen it before.")
        w.say(f"The attic seemed to whisper {activity.twist}, like it had been saving the secret for {child.id}.")

    w.para()
    if prize_cfg.fragile:
        child.memes["joy"] += 1
        w.say(f"{child.id} helped carry the {prize.label} back carefully.")
        w.say(f"Then {child.id} and {parent.id if False else parent.label} sat together on an old blanket and looked at the new treasure.")
        w.say(f"The attic still smelled dusty, but now it felt warm, and {child.id} had a happy story to tell.")
    else:
        child.memes["joy"] += 1
        w.say(f"{child.id} and {parent.label} tidied the attic together.")
        w.say(f"When they were done, the room looked neat, and {child.id} grinned at the tiny secret they had found.")

    w.facts.update(child=child, parent=parent, prize=prize, activity=activity, setting=setting)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short animal story set in an attic where a little {child.type} wants to {act.verb} and finds a twist.',
        f'Tell a gentle story about {child.id} in the attic, with dust, a careful warning, and {prize.phrase}.',
        f'Write a child-friendly animal story that uses the word "attic" and ends with a surprising discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who is the story about in the attic?",
            answer=f"The story is about {child.id}, a little {child.type}, and {parent.label}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do in the attic?",
            answer=f"{child.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What surprising thing did {child.id} find?",
            answer=f"{child.id} found {prize.phrase}, and that became the twist in the story.",
        ),
        QAItem(
            question=f"Why did the parent worry?",
            answer=f"The parent worried because the attic was dusty and {prize.label} could be fragile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an attic?",
            answer="An attic is the room near the roof of a house, often used for storage.",
        ),
        QAItem(
            question="Why can dust make people sneeze?",
            answer="Dust can make the nose tickle, so some people sneeze when they breathe it in.",
        ),
        QAItem(
            question="What does fragile mean?",
            answer="Fragile means something can break or get damaged easily, so it must be handled gently.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "attic")]
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("fragile", pid) if p.fragile else asp.fact("sturdy", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(attic, A, P) :- activity(A), prize(P).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.room:
            bits.append(f"room={e.room}")
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld in an attic with a twist.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid animal attic story matches those options.")
    _, activity, prize = rng.choice(sorted(combos))
    if args.animal:
        animal = args.animal
    else:
        animal = rng.choice(sorted(ANIMALS))
    if args.gender:
        if args.gender not in ANIMALS[animal]["genders"]:
            raise StoryError(f"A {animal} is not a typical {args.gender} here.")
        gender = args.gender
    else:
        gender = rng.choice(sorted(ANIMALS[animal]["genders"]))
    name = args.name or rng.choice(ANIMALS[animal]["names"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(activity=activity, prize=prize, animal=animal, gender=gender, parent=parent, name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS["attic"], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.animal, params.parent)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combos")
        for combo in combos:
            print(combo)
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
            header = f"### {p.name}: {p.animal} in the attic ({p.activity}, prize={p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
