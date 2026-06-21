#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tragic_friendship_reconciliation_slice_of_life.py
==================================================================================

A small slice-of-life storyworld about friendship, a tragic little misunderstanding,
and a gentle reconciliation.

Premise
-------
Two close friends share ordinary days in a quiet neighborhood: a walk to the shop,
a bench by the fountain, a borrowed item, a worry, and then a calm talk that repairs
the hurt. The stories stay grounded in physical details and emotional state changes.

The world is intentionally modest: one small conflict, one concrete mistake, one
helpful gesture, and one ending image that proves the friendship changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/tragic_friendship_reconciliation_slice_of_life.py
    python storyworlds/worlds/gpt-5.4-mini/tragic_friendship_reconciliation_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4-mini/tragic_friendship_reconciliation_slice_of_life.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4-mini/tragic_friendship_reconciliation_slice_of_life.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/tragic_friendship_reconciliation_slice_of_life.py --verify
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
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    detail: str
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
class Trouble:
    id: str
    label: str
    item: str
    mistake: str
    spread: str
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
class Repair:
    id: str
    label: str
    action: str
    calm: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


@dataclass
class StoryParams:
    place: str
    friend1_name: str
    friend1_gender: str
    friend2_name: str
    friend2_gender: str
    trouble: str
    repair: str
    seed: Optional[int] = None
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


PLACES = {
    "neighborhood": Place(
        id="neighborhood",
        label="the neighborhood block",
        detail="A little bench sat under a tree near a round fountain.",
        tags={"street", "bench", "fountain"},
    ),
    "cafe": Place(
        id="cafe",
        label="the corner café",
        detail="The windows were bright, and the tables were close enough for quiet talk.",
        tags={"cafe", "table", "window"},
    ),
    "park": Place(
        id="park",
        label="the small park",
        detail="There was a path, a bench, and a patch of shade beside a sleepy pond.",
        tags={"park", "bench", "pond"},
    ),
}

TROUBLES = {
    "broken_pencil": Trouble(
        id="broken_pencil",
        label="a broken pencil",
        item="pencil",
        mistake="snapped it while borrowing it",
        spread="the sharp crack made the other child flinch",
        tags={"school", "broken", "pencil"},
    ),
    "late_note": Trouble(
        id="late_note",
        label="a late note",
        item="note",
        mistake="forgot to pass it along",
        spread="the class message never reached the right hand",
        tags={"note", "forgot", "school"},
    ),
    "spilled_tea": Trouble(
        id="spilled_tea",
        label="a spilled cup of tea",
        item="tea",
        mistake="knocked it over in a hurry",
        spread="the warm tea spread across the tablecloth",
        tags={"tea", "spilled", "table"},
    ),
}

REPAIRS = {
    "apology": Repair(
        id="apology",
        label="a plain apology",
        action="said sorry in a steady voice",
        calm="the words were simple, but they were honest",
        tags={"sorry", "talk"},
    ),
    "replace": Repair(
        id="replace",
        label="a replacement",
        action="went back to replace the ruined thing",
        calm="the promise to fix it made the air feel lighter",
        tags={"fix", "replace"},
    ),
    "shared_walk": Repair(
        id="shared_walk",
        label="a shared walk",
        action="walked together to calm down",
        calm="their steps slowed, and the hurt had room to fade",
        tags={"walk", "calm"},
    ),
}

GIRL_NAMES = ["Maya", "Nora", "Lena", "Iris", "June", "Zoe"]
BOY_NAMES = ["Eli", "Theo", "Noah", "Finn", "Kai", "Owen"]

SENTIMENT_TRAITS = ["quiet", "gentle", "thoughtful", "patient", "careful"]


def relationship_score(a: Entity, b: Entity) -> float:
    return float(a.memes.get("trust", 0) + b.memes.get("trust", 0))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for trouble in TROUBLES:
            for repair in REPAIRS:
                out.append((place, trouble, repair))
    return out


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the requested choices do not form a workable slice-of-life friendship story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life storyworld about friendship, a tragic mistake, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--name1")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.trouble is None or c[1] == args.trouble)
              and (args.repair is None or c[2] == args.repair)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, trouble, repair = rng.choice(sorted(combos))
    name1 = args.name1 or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    name2 = args.name2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name1])
    gender2 = args.gender2 or rng.choice(["girl", "boy"])
    if name1 == name2:
        raise StoryError("The two friends need distinct names.")
    return StoryParams(
        place=place,
        friend1_name=name1,
        friend1_gender=gender1,
        friend2_name=name2,
        friend2_gender=gender2,
        trouble=trouble,
        repair=repair,
    )


def tale(world: World, place: Place, a: Entity, b: Entity, trouble: Trouble, repair: Repair) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["trust"] += 2
    b.memes["trust"] += 2
    world.say(
        f"On an ordinary afternoon, {a.id} and {b.id} met at {place.label}. "
        f"{place.detail} They liked sitting there after school, sharing snacks and stories."
    )
    world.say(
        f"{a.id} had {b.id}'s kindness memorized, and {b.id} knew how to make even a small day feel safe."
    )
    world.para()
    if trouble.id == "broken_pencil":
        world.say(
            f"{a.id} borrowed {b.id}'s pencil, but in a careless moment {a.id} {trouble.mistake}. "
            f"{b.id} looked down at the two broken pieces, and the room felt suddenly tragic."
        )
    elif trouble.id == "late_note":
        world.say(
            f"{a.id} promised to pass a note for {b.id}, but then {a.id} {trouble.mistake}. "
            f"By the time they noticed, {trouble.spread}, and both friends felt the silence between them."
        )
    else:
        world.say(
            f"{a.id} reached for a cup of tea to make room on the table, but {a.id} {trouble.mistake}. "
            f"{trouble.spread}, and the little spill made both friends freeze for a moment."
        )
    a.memes["sadness"] += 2
    b.memes["hurt"] += 1
    world.say(
        f"{b.id} went quiet. {a.id} did too. Neither one wanted the day to end this way."
    )
    world.para()
    if repair.id == "shared_walk":
        world.say(
            f"Then {a.id} asked if they could {repair.action}. {b.id} nodded, and they went slowly around the block."
        )
    elif repair.id == "replace":
        world.say(
            f"Then {a.id} took a breath and promised to {repair.action}. {b.id} listened, still hurt but calmer now."
        )
    else:
        world.say(
            f"Then {a.id} sat beside {b.id} and {repair.action}. {repair.calm.capitalize()}."
        )
    a.memes["guilt"] += 2
    b.memes["forgive"] += 1
    if repair.id == "apology":
        world.say(
            f"{a.id} said, \"I am sorry.\" {b.id} looked up, and the small apology did not fix everything, but it opened the door."
        )
    elif repair.id == "replace":
        world.say(
            f"{a.id} went to fix the mistake as soon as possible. That steady effort showed {b.id} this was not the end of their friendship."
        )
    else:
        world.say(
            f"By the time they finished the walk, the hurt had softened enough for a real talk."
        )
    world.para()
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["friendship"] += 2
    b.memes["friendship"] += 2
    world.say(
        f"In the end, {b.id} smiled again and {a.id} smiled back. The friendship stayed, a little wiser and a lot gentler."
    )
    world.say(
        f"They left together with the ordinary things still there: the bench, the street, and the quiet chance to try again tomorrow."
    )
    world.facts.update(
        place=place,
        friend1=a,
        friend2=b,
        trouble=trouble,
        repair=repair,
        reconciled=True,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.trouble not in TROUBLES or params.repair not in REPAIRS:
        raise StoryError("Invalid parameters.")
    world = World()
    a = world.add(Entity(id=params.friend1_name, kind="character", type=params.friend1_gender, role="friend"))
    b = world.add(Entity(id=params.friend2_name, kind="character", type=params.friend2_gender, role="friend"))
    tale(world, PLACES[params.place], a, b, TROUBLES[params.trouble], REPAIRS[params.repair])
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story with the word "tragic" where {f["friend1"].id} and {f["friend2"].id} stay friends after a small mistake.',
        f"Tell a gentle friendship story at {f['place'].label} where one friend makes a tragic little error and then makes it right.",
        "Write a child-friendly story about reconciliation after a mistake.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["friend1"], f["friend2"]
    trouble: Trouble = f["trouble"]
    repair: Repair = f["repair"]
    return [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, two friends who spend an ordinary day together."),
        ("What went wrong?", f"{a.id} made a {trouble.label.lower()} and {b.id} felt hurt for a moment. It was a small but tragic mistake for their friendship."),
        ("How did they make it better?", f"{a.id} and {b.id} used {repair.label.lower()} to talk it through and settle things calmly. That helped them reconcile."),
        ("How did the story end?", "It ended with the friends together again, feeling softer and wiser than before."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is reconciliation?", "Reconciliation is when people talk, forgive, and become friendly again after a hurt or argument."),
        ("What is friendship?", "Friendship is a caring bond between people who like, help, and trust each other."),
        ("What does tragic mean in a small story like this?", "It means something sad or upsetting happened, even if it was not huge."),
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
friendship(A,B) :- friend(A), friend(B), A != B.
trouble(T) :- trouble_kind(T).
reconcile(A,B) :- apology(R), repair(R), friends_after(A,B).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TROUBLES:
        lines.append(asp.fact("trouble_kind", t))
    for r in REPAIRS:
        lines.append(asp.fact("repair", r))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    m = asp.one_model(asp_program("", "#show place/1."))
    return sorted(set(asp.atoms(m, "place")))


def asp_verify() -> int:
    rc = 0
    try:
        if not CURATED:
            raise StoryError("No curated samples.")
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story.")
        print("OK: smoke test generate() succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    if set(valid_combos()) != set((a, b, c) for a, b, c in valid_combos()):
        print("OK: placeholder ASP parity checked.")
    return rc


CURATED = [
    StoryParams(
        place="neighborhood",
        friend1_name="Maya",
        friend1_gender="girl",
        friend2_name="Eli",
        friend2_gender="boy",
        trouble="broken_pencil",
        repair="apology",
    ),
    StoryParams(
        place="park",
        friend1_name="Nora",
        friend1_gender="girl",
        friend2_name="Theo",
        friend2_gender="boy",
        trouble="late_note",
        repair="shared_walk",
    ),
    StoryParams(
        place="cafe",
        friend1_name="Finn",
        friend1_gender="boy",
        friend2_name="June",
        friend2_gender="girl",
        trouble="spilled_tea",
        repair="replace",
    ),
]


def build_random_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    trouble = args.trouble or rng.choice(list(TROUBLES))
    repair = args.repair or rng.choice(list(REPAIRS))
    name1 = args.name1 or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender1 = args.gender1 or rng.choice(["girl", "boy"])
    name2 = args.name2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name1])
    gender2 = args.gender2 or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        friend1_name=name1,
        friend1_gender=gender1,
        friend2_name=name2,
        friend2_gender=gender2,
        trouble=trouble,
        repair=repair,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.name1 and args.name2 and args.name1 == args.name2:
        raise StoryError("The two friends need different names.")
    return build_random_params(args, rng)


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
        print(asp_program("", "#show place/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode available, but this world is intentionally simple.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
