#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/novocaine_hinder_bravery_quest_foreshadowing_bedtime_story.py
==============================================================================================

A small bedtime-story storyworld about a child, a careful quest, a brave trip to
the dentist, and the quiet foreshadowing that the ache will be soothed. The
required seed words appear naturally: **novocaine** and **hinder**.

The world is a tiny simulation: a child has a sore tooth, a grown-up explains
the plan, the child gathers bravery for a quest to the dentist chair, and the
story resolves when numbing medicine makes the tooth calm enough for a gentle
fix. The tone stays bedtime-soft, with a cozy ending image proving what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/novocaine_hinder_bravery_quest_foreshadowing_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/novocaine_hinder_bravery_quest_foreshadowing_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/novocaine_hinder_bravery_quest_foreshadowing_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/novocaine_hinder_bravery_quest_foreshadowing_bedtime_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/novocaine_hinder_bravery_quest_foreshadowing_bedtime_story.py --verify
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    cozy: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Hinder:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Quest:
    id: str
    label: str
    goal: str
    steps: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    power: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime quest storyworld with novocaine and a gentle hinder.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hinder", choices=HINDERS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--remedy", choices=REMEDIES)
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


def _import_asp():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    import asp  # noqa: F401
    return asp


def hazard_ok(hinder: Hinder, remedy: Remedy) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, h, q) for p in PLACES for h in HINDERS for q in QUESTS if hazard_ok(HINDERS[h], REMEDIES["novocaine"]) ]


def explain_rejection(_: Hinder, __: Quest) -> str:
    return "(No story: this choice does not support the bedtime quest.)"


def outcome_of(params: "StoryParams") -> str:
    return "resolved"


@dataclass
class StoryParams:
    place: str
    hinder: str
    quest: str
    clue: str
    remedy: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _story_start(world: World, child: Entity, parent: Entity, quest: Quest, clue: Clue) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"On a sleepy evening, {child.id} and {parent.label_word} sat in the gentle glow of {world.place.label}. "
        f"{world.place.cozy}"
    )
    world.say(
        f"{child.id} was on a little {quest.label} to do the brave thing: {quest.goal}. "
        f"A tiny {clue.phrase} seemed to whisper that the sore tooth would not last forever."
    )


def _foreshadow(world: World, child: Entity, hinder: Hinder) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"Still, there was one {hinder.label} that could hinder the plan: {hinder.phrase}. "
        f"{child.id} looked at the pillow and imagined needing courage before the night was done."
    )


def _quest_step(world: World, child: Entity, parent: Entity, quest: Quest) -> None:
    world.para()
    world.say(
        f"{child.id} took a deep breath and followed {parent.label_word} on the quest. "
        f"{quest.steps[0]} {quest.steps[1]} "
        f"{child.pronoun('possessive').capitalize()} hands stayed small and still."
    )


def _remedy(world: World, child: Entity, parent: Entity, clue: Clue, remedy: Remedy) -> None:
    child.memes["bravery"] += 1
    child.meters["tooth_ache"] = 0.0
    child.meters["calm"] += 1
    world.say(
        f"At the chair, {parent.label_word} spoke softly, and the dentist gave {child.id} {remedy.phrase}. "
        f"The novocaine began to numb the tooth, and the buzzing sounds felt far away."
    )
    world.say(
        f"{clue.label_word if hasattr(clue, 'label_word') else clue.label} was right: the ache loosened, then floated off. "
        f"The brave little quest was already turning into relief."
    )


def _ending(world: World, child: Entity, parent: Entity) -> None:
    child.memes["peace"] += 1
    world.say(
        f"When it was all over, {child.id} leaned against {parent.pronoun('object')} with a sleepy smile. "
        f"The pillow waited at home, and the night felt soft again."
    )
    world.say(
        f"{child.id}'s tooth was quiet, {parent.label_word} tucked the blanket up high, and the brave child fell asleep "
        f"holding the memory of a quest finished well."
    )


def tell(place: Place, hinder: Hinder, quest: Quest, clue: Clue, remedy: Remedy,
         name: str = "Mia", gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    child.meters["tooth_ache"] = 1.0
    child.memes["bravery"] = 0.0
    world.facts.update(child=child, parent=parent, place=place, hinder=hinder, quest=quest, clue=clue, remedy=remedy)

    _story_start(world, child, parent, quest, clue)
    _foreshadow(world, child, hinder)
    _quest_step(world, child, parent, quest)
    world.para()
    _remedy(world, child, parent, clue, remedy)
    _ending(world, child, parent)

    world.facts["resolved"] = True
    world.facts["outcome"] = "resolved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "{f["remedy"].label}" and "{f["hinder"].label}".',
        f"Tell a cozy quest story where {f['child'].id} is brave, something can hinder the plan, and novocaine helps the sore tooth feel better.",
        f"Write a soft bedtime tale with foreshadowing, a small quest, and a gentle ending where a child finds courage at the dentist.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, p, h, q, r = f["child"], f["parent"], f["hinder"], f["quest"], f["remedy"]
    return [
        ("Who is the story about?",
         f"It is about {c.id}, who went on a little {q.label} with {p.label_word}. The story stays close to {c.id}'s brave night-time feelings."),
        ("What could hinder the plan?",
         f"{h.phrase} could hinder the plan. That worry showed up early, so the story could foreshadow that the child would need courage."),
        ("How did the child get help?",
         f"The dentist used {r.phrase}, and novocaine made the sore tooth numb. That helped the brave quest end in relief instead of worry."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is novocaine?",
               "Novocaine is medicine that can numb part of your mouth so a tooth can be treated without as much pain. It is used by a grown-up dentist."),
        QAItem("What does it mean to hinder something?",
               "To hinder something means to slow it down or make it harder. A hinder can be a small problem that gets in the way."),
        QAItem("What is a quest?",
               "A quest is a brave journey to reach an important goal. In bedtime stories, a quest can be as small as going somewhere scary but safe."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(e.meters)} memes={dict(e.memes)} role={e.role}")
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


PLACES = {
    "home": Place(id="home", label="the quiet house", cozy="The hall was warm, and the bedroom lamp made a little gold pool on the floor."),
    "clinic": Place(id="clinic", label="the moonlit clinic", cozy="A soft blanket waited on the chair, and the room smelled clean and calm."),
    "bathroom": Place(id="bathroom", label="the little bathroom", cozy="The faucet whispered, and the towel hung ready like a small cloud."),
}

HINDERS = {
    "worry": Hinder(id="worry", label="worry", phrase="the worry that the chair would feel too big", tags={"foreshadowing"}),
    "noise": Hinder(id="noise", label="noise", phrase="the buzzing sound of the small dental lamp", tags={"foreshadowing"}),
    "timing": Hinder(id="timing", label="timing", phrase="the way bedtime was already calling", tags={"foreshadowing"}),
}

QUESTS = {
    "dentist": Quest(id="dentist", label="quest", goal="to sit very still and let the tooth get fixed", steps=["First they walked down the hall.", "Then they climbed into the big chair."], tags={"quest", "bravery"}),
    "medicine": Quest(id="medicine", label="quest", goal="to swallow the worry and take the helpful medicine", steps=["First they held the cup with both hands.", "Then they took a tiny sip."], tags={"quest", "bravery"}),
}

CLUES = {
    "moonlight": Clue(id="moonlight", label="moonlight", phrase="the silver moonlight on the window", tags={"foreshadowing"}),
    "blanket": Clue(id="blanket", label="blanket", phrase="the waiting blanket on the chair", tags={"foreshadowing"}),
    "pillow": Clue(id="pillow", label="pillow", phrase="the pillow tucked on the couch", tags={"foreshadowing"}),
}

REMEDIES = {
    "novocaine": Remedy(id="novocaine", label="novocaine", phrase="a little bit of novocaine", power=3, tags={"novocaine"}),
    "medicine": Remedy(id="medicine", label="medicine", phrase="sweet sleepy medicine", power=2, tags={"novocaine"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Ben"]


@dataclass
class StoryParams:
    place: str
    hinder: str
    quest: str
    clue: str
    remedy: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(place="clinic", hinder="noise", quest="dentist", clue="moonlight", remedy="novocaine", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="home", hinder="timing", quest="medicine", clue="pillow", remedy="novocaine", name="Eli", gender="boy", parent="father"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.remedy and args.remedy not in REMEDIES:
        raise StoryError("Unknown remedy.")
    place = args.place or rng.choice(list(PLACES))
    hinder = args.hinder or rng.choice(list(HINDERS))
    quest = args.quest or rng.choice(list(QUESTS))
    clue = args.clue or rng.choice(list(CLUES))
    remedy = args.remedy or "novocaine"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, hinder=hinder, quest=quest, clue=clue, remedy=remedy, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hinder not in HINDERS or params.quest not in QUESTS or params.clue not in CLUES or params.remedy not in REMEDIES:
        raise StoryError("Invalid parameters.")
    world = tell(PLACES[params.place], HINDERS[params.hinder], QUESTS[params.quest], CLUES[params.clue], REMEDIES[params.remedy], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
selected_remedy(novocaine).
hinder(hinder).
quest(quest).
valid(P,H,Q) :- place(P), hinder(H), quest(Q).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        *(asp.fact("place", k) for k in PLACES),
        *(asp.fact("hinder", k) for k in HINDERS),
        *(asp.fact("quest", k) for k in QUESTS),
        *(asp.fact("clue", k) for k in CLUES),
        *(asp.fact("remedy", k) for k in REMEDIES),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    asp = _import_asp()
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAILED: generate smoke test: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(CURATED[i % len(CURATED)]) for i in range(args.n)] if args.all else []
    if not samples:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i if args.seed is not None else None
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
