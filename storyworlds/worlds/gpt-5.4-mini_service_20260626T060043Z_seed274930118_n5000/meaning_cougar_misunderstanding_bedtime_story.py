#!/usr/bin/env python3
"""
storyworlds/worlds/meaning_cougar_misunderstanding_bedtime_story.py
===================================================================

A tiny bedtime-story world about a small misunderstanding at night.

Seed tale:
---
At bedtime, Mina heard a deep growl outside her window and thought a cougar was
lurking in the dark garden. She got frightened and woke her dad. Dad listened
carefully and smiled: the sound was not a cougar at all, but the neighbor's cat
answering an owl. They opened the curtain together, found the moonlit garden
safe, and Mina learned the meaning of the sound.

World idea:
- The child has a sleepy-but-alert emotional state.
- A nighttime sound can be misread as "cougar".
- A careful parent can investigate the meaning of the sound.
- The turn is a misunderstanding: fear becomes understanding.
- The ending image proves the change: the window is calm, the garden is safe,
  and the child can settle back to sleep.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    heard_as: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
    place: str = "the house"
    bedtime: bool = True


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A bedtime-story world about a cougar misunderstanding."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


PLACES = {
    "bedroom": Setting(place="the bedroom", bedtime=True),
    "upstairs": Setting(place="the upstairs hall", bedtime=True),
    "porch": Setting(place="the porch", bedtime=True),
}

CHILDREN = {
    "girl": ["Mina", "Luna", "Ruby", "Ivy", "Nora"],
    "boy": ["Eli", "Noah", "Theo", "Finn", "Ben"],
}
PARENTS = ["mother", "father"]


ASP_RULES = r"""
#show valid_place/1.
#show valid_story/3.

valid_place(P) :- place(P).
valid_story(P,C,G) :- valid_place(P), child_gender(G), child_name(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("valid_place", pid))
    for g in ("girl", "boy"):
        lines.append(asp.fact("child_gender", g))
    for g, names in CHILDREN.items():
        for n in names:
            lines.append(asp.fact("child_name", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    if set(asp_valid_places()) == {(p,) for p in PLACES}:
        print(f"OK: clingo gate matches valid places ({len(PLACES)}).")
        return 0
    print("MISMATCH between clingo and python valid places.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILDREN[gender])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, child_name=name, child_gender=gender, parent_type=parent)


def make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        traits=["little", "sleepy", "curious"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
    ))
    sound = world.add(Entity(
        id="sound",
        type="thing",
        label="night sound",
        phrase="a deep sound from the dark garden",
        heard_as="cougar",
    ))
    cat = world.add(Entity(
        id="cat",
        type="cat",
        label="neighbor's cat",
        phrase="the neighbor's cat",
    ))
    owl = world.add(Entity(
        id="owl",
        type="owl",
        label="owl",
        phrase="an owl in the tree",
    ))
    moon = world.add(Entity(
        id="moon",
        type="thing",
        label="moonlight",
        phrase="soft moonlight on the window",
    ))
    world.facts.update(child=child, parent=parent, sound=sound, cat=cat, owl=owl, moon=moon)
    return world


def predict_misunderstanding(world: World) -> bool:
    sound = world.facts["sound"]
    return sound.heard_as == "cougar"


def tell(world: World) -> None:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    sound: Entity = world.facts["sound"]
    cat: Entity = world.facts["cat"]
    owl: Entity = world.facts["owl"]
    moon: Entity = world.facts["moon"]

    child.memes["sleepy"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"At bedtime, {child.id} lay in {world.setting.place} and listened to "
        f"{moon.phrase}."
    )
    world.say(
        f"Then {sound.phrase} drifted in from the dark garden, and {child.id} "
        f"thought it sounded like a cougar."
    )

    world.para()
    child.memes["fear"] += 1
    child.meters["startle"] += 1
    world.say(
        f"{child.id} sat up fast, because a cougar in the dark would be a very "
        f"big meaning for such a little room."
    )
    world.say(
        f"{child.id} called for {parent.pronoun('object')} and clutched the blanket."
    )

    world.para()
    parent.memes["calm"] += 1
    parent.meters["investigation"] += 1
    world.say(
        f"{parent.pronoun().capitalize()} listened carefully, then opened the curtain "
        f"just a little."
    )
    world.say(
        f"It was not a cougar at all. It was {cat.phrase}, and from the tree came "
        f"{owl.phrase}, answering back."
    )
    world.say(
        f"{parent.pronoun().capitalize()} smiled and said that the sound had a kinder "
        f"meaning than fear had first guessed."
    )

    world.para()
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["understanding"] += 2
    child.meters["startle"] = 0.0
    world.say(
        f"{child.id} peered out, saw only the moonlit garden, and learned the meaning "
        f"of the sound."
    )
    world.say(
        f"With the curtain tucked back in place, {child.id} settled under the blanket "
        f"and the room grew soft and quiet again."
    )

    world.facts["misunderstanding"] = True
    world.facts["resolved"] = True
    world.facts["meaning"] = "a cat and an owl can sound bigger in the dark"


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    return [
        'Write a gentle bedtime story about a child who hears something scary and then learns the meaning of it.',
        f"Tell a quiet story where {child.id} thinks a cougar is outside, but {parent.pronoun('subject')} discovers the real sound.",
        "Write a bedtime tale with moonlight, a misunderstanding, and a calm ending in the garden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    parent: Entity = world.facts["parent"]
    return [
        QAItem(
            question=f"What did {child.id} think was outside the window?",
            answer=f"{child.id} thought a cougar was outside the window because the sound in the dark garden felt so big and surprising.",
        ),
        QAItem(
            question=f"Who listened carefully and checked the curtain?",
            answer=f"{parent.pronoun('subject').capitalize()} listened carefully and checked the curtain so {child.id} would know what the sound really was.",
        ),
        QAItem(
            question="What was the meaning of the sound?",
            answer="The meaning of the sound was that it was the neighbor's cat and an owl talking back and forth, not a cougar at all.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt calm and understanding at the end, because the dark garden was safe and the bedtime room was quiet again.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "cougar": [(
        "What is a cougar?",
        "A cougar is a large wild cat. It usually lives outdoors and can move quietly in the dark."
    )],
    "meaning": [(
        "What does meaning mean?",
        "Meaning is what something tells us or what it stands for, like the true idea behind a sound or a word."
    )],
    "bedtime": [(
        "Why do children go to bed at bedtime?",
        "Children go to bed at bedtime so their bodies and minds can rest and get ready for a new day."
    )],
    "owl": [(
        "Why do owls sound spooky at night?",
        "Owls can sound spooky because their calls are low and quiet, and nighttime makes every sound seem bigger."
    )],
    "cat": [(
        "What do cats do at night?",
        "Cats often walk, listen, and call out at night because they are curious animals and like to explore."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for items in WORLD_KNOWLEDGE.values() for q, a in items]


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.heard_as:
            bits.append(f"heard_as={e.heard_as}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for gender, names in CHILDREN.items():
            for name in names:
                out.append((place, name, gender))
    return out


def explain_rejection() -> str:
    return "(No story: the requested options do not fit this bedtime misunderstanding.)"


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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
    StoryParams(place="bedroom", child_name="Mina", child_gender="girl", parent_type="father"),
    StoryParams(place="upstairs", child_name="Eli", child_gender="boy", parent_type="mother"),
    StoryParams(place="porch", child_name="Luna", child_gender="girl", parent_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.child_name}: bedtime misunderstanding in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
