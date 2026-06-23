#!/usr/bin/env python3
"""
storyworlds/worlds/tilt_tulip_lesson_learned_quest_transformation_mystery.py
=============================================================================

A small mystery storyworld about a careful child, a tilted clue, a tulip,
a quest, a transformation, and a lesson learned.

The world is intentionally compact: one entity model, one world state,
a short causal chain, and a deterministic prose generator that turns simulated
state into a complete child-facing story plus QA.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

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
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    mystery: str
    afford: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    tilt_meaning: str
    truth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    leads_to: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    phrase: str
    change: str
    result_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "traits": list(e.traits), "role": e.role,
            "owner": e.owner, "caretaker": e.caretaker, "plural": e.plural,
            "tags": set(e.tags), "attrs": dict(e.attrs),
            "meters": defaultdict(float, dict(e.meters)),
            "memes": defaultdict(float, dict(e.memes)),
        }) for k, e in self.entities.items()}
        clone.facts = json.loads(json.dumps(self.facts))
        clone.history = list(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    clue: str
    quest: str
    transformation: str
    seed: int | None = None


PLACES = {
    "old_garden": Place(
        id="old_garden",
        name="the old garden",
        mystery="something hidden under the hedges",
        afford={"quest", "mystery"},
        tags={"garden", "mystery"},
    ),
    "quiet_museum": Place(
        id="quiet_museum",
        name="the quiet museum",
        mystery="a secret room behind a tilt of painted tiles",
        afford={"quest", "mystery"},
        tags={"museum", "mystery"},
    ),
    "moonlight_greenhouse": Place(
        id="moonlight_greenhouse",
        name="the moonlight greenhouse",
        mystery="a path of footprints beside the pots",
        afford={"quest", "mystery"},
        tags={"greenhouse", "mystery"},
    ),
}

CLUES = {
    "tilted_stone": Clue(
        id="tilted_stone",
        label="tilted stone",
        phrase="a stone that looked slightly tilted",
        tilt_meaning="tilt",
        truth="the stone was covering a tiny key",
        tags={"tilt", "stone", "mystery"},
    ),
    "tilted_frame": Clue(
        id="tilted_frame",
        label="tilted frame",
        phrase="a picture frame tilted on the wall",
        tilt_meaning="tilt",
        truth="the frame was hiding a note behind it",
        tags={"tilt", "frame", "mystery"},
    ),
    "tulip_petal": Clue(
        id="tulip_petal",
        label="tulip petal",
        phrase="a tulip with one petal bent to the side",
        tilt_meaning="tulip",
        truth="the bent petal pointed toward the next clue",
        tags={"tulip", "flower", "mystery"},
    ),
}

QUESTS = {
    "follow_clues": QuestItem(
        id="follow_clues",
        label="clue hunt",
        phrase="a little clue hunt",
        leads_to="the hidden answer",
        tags={"quest", "clue"},
    ),
    "find_key": QuestItem(
        id="find_key",
        label="key quest",
        phrase="a quest for the key",
        leads_to="the locked door",
        tags={"quest", "key"},
    ),
    "solve_note": QuestItem(
        id="solve_note",
        label="note quest",
        phrase="a quest to read the note",
        leads_to="the final hint",
        tags={"quest", "note"},
    ),
}

TRANSFORMATIONS = {
    "color_shift": Transformation(
        id="color_shift",
        label="color shift",
        phrase="a bright color shift",
        change="the dull clue turned bright and easy to notice",
        result_image="the flower seemed to glow",
        tags={"transformation", "color"},
    ),
    "bloom_open": Transformation(
        id="bloom_open",
        label="bloom open",
        phrase="a bloom that opened wide",
        change="the tulip opened and revealed the path",
        result_image="the tulip stood open like a tiny lantern",
        tags={"transformation", "tulip"},
    ),
    "message_clear": Transformation(
        id="message_clear",
        label="message clear",
        phrase="a message that became clear",
        change="the hidden note made sense at last",
        result_image="the note looked plain and readable",
        tags={"transformation", "note"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Iris", "Maya", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Ben", "Leo"]
TRAITS = ["curious", "careful", "patient", "quiet", "brave"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for quest in QUESTS:
                for trans in TRANSFORMATIONS:
                    if {"tilt", "tulip"} & (CLUES[clue].tags | TRANSFORMATIONS[trans].tags):
                        combos.append((place, clue, quest, trans))
    return combos


def explain_rejection() -> str:
    return "(No story: this combination does not fit the mystery quest and transformation pattern.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld about tilt, tulip, quest, and transformation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--transformation", choices=sorted(TRANSFORMATIONS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
              and (args.clue is None or c[1] == args.clue)
              and (args.quest is None or c[2] == args.quest)
              and (args.transformation is None or c[3] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, quest, trans = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        child_name=name,
        child_type=child_type,
        parent_type=parent_type,
        clue=clue,
        quest=quest,
        transformation=trans,
    )


def _setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity, Entity]:
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, traits=["curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="the parent"))
    clue = world.add(Entity(id=params.clue, type="clue", label=CLUES[params.clue].label, phrase=CLUES[params.clue].phrase, tags=set(CLUES[params.clue].tags)))
    transform = world.add(Entity(id=params.transformation, type="change", label=TRANSFORMATIONS[params.transformation].label, phrase=TRANSFORMATIONS[params.transformation].phrase, tags=set(TRANSFORMATIONS[params.transformation].tags)))
    quest = world.add(Entity(id=params.quest, type="quest", label=QUESTS[params.quest].label, phrase=QUESTS[params.quest].phrase, tags=set(QUESTS[params.quest].tags)))
    return child, parent, clue, transform


def _investigate(world: World, child: Entity, clue: Entity, quest: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(f"{child.id} wandered into {world.place.name}, where {world.place.mystery}.")
    world.say(f"{child.id} noticed {clue.phrase} and decided to begin {quest.phrase}.")
    world.event("quest_started", clue=clue.id, quest=quest.id)


def _turn(world: World, child: Entity, parent: Entity, clue: Entity, transform: Entity) -> None:
    child.memes["worry"] += 1
    world.para()
    world.say(f"{child.id} tilted the clue gently, and that small tilt changed everything.")
    if clue.id == "tilted_stone":
        world.say(f"Under the stone, {CLUES[clue.id].truth}.")
    elif clue.id == "tilted_frame":
        world.say(f"Behind the frame, {CLUES[clue.id].truth}.")
    else:
        world.say(f"Beside the tulip, {CLUES[clue.id].truth}.")
    world.say(f"{transform.change}.")

    world.event("clue_revealed", clue=clue.id, transform=transform.id)
    child.meters["discovered"] += 1
    child.memes["relief"] += 1
    parent.memes["pride"] += 1


def _resolve(world: World, child: Entity, parent: Entity, quest: Entity, transform: Entity, clue: Entity) -> None:
    world.para()
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    world.say(f"{child.id} followed the hint all the way to {quest.leads_to}.")
    world.say(f"In the end, {transform.result_image}, and the mystery made sense.")
    world.say(f"{parent.label_word.capitalize()} smiled because {child.id} had learned that careful eyes can solve a mystery.")
    world.say(f"That was the lesson learned: when something looks tilted, it may be asking to be noticed.")
    world.event("lesson_learned", lesson="look_closer", clue=clue.id)


def _story(world: World) -> str:
    return world.render()


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.quest not in QUESTS or params.transformation not in TRANSFORMATIONS:
        raise StoryError(explain_rejection())
    world = World(PLACES[params.place])
    child, parent, clue, transform = _setup(world, params)
    quest = world.get(params.quest)
    world.facts.update(
        child=child.id,
        parent=parent.id,
        clue=clue.id,
        quest=quest.id,
        transformation=transform.id,
        place=params.place,
        clue_tags=sorted(CLUES[params.clue].tags),
        quest_phrase=QUESTS[params.quest].phrase,
        transform_phrase=TRANSFORMATIONS[params.transformation].phrase,
    )
    _investigate(world, child, clue, quest)
    _turn(world, child, parent, clue, transform)
    _resolve(world, child, parent, quest, transform, clue)
    return StorySample(
        params=params,
        story=_story(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the words "tilt" and "tulip".',
        f"Tell a gentle quest story where {f['child']} explores {world.place.name} and learns a lesson from a tilted clue.",
        f"Write a story with a mystery, a quest, and a transformation ending where a clue helps solve the puzzle.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = world.get(f["child"])
    parent = world.get(f["parent"])
    clue = world.get(f["clue"])
    quest = world.get(f["quest"])
    trans = world.get(f["transformation"])
    return [
        QAItem(
            question=f"What made {child.id} start the quest in {world.place.name}?",
            answer=f"{child.id} saw {clue.phrase} and got curious. That clue looked important, so {child.id} began {quest.phrase}.",
        ),
        QAItem(
            question=f"Why did the tilted clue matter?",
            answer=f"It mattered because the tilt pointed to something hidden. The small change led {child.id} toward the answer.",
        ),
        QAItem(
            question=f"What changed at the end of the mystery?",
            answer=f"{trans.change.capitalize()}. That transformation helped {child.id} understand the clue and finish the quest.",
        ),
        QAItem(
            question=f"What lesson learned did {child.id} show?",
            answer=f"{child.id} learned to look carefully at small details. The mystery was solved because {child.id} did not rush past the clue.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not clear at first. People solve it by looking for clues.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. It usually has clues and a goal.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state to another. In stories, it can show that something has been revealed.",
        ),
        QAItem(
            question="What is a tulip?",
            answer="A tulip is a flower with smooth petals and a tall stem. It can look bright and cheerful in a garden.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for tag in sorted(PLACES[pid].tags):
            lines.append(asp.fact("place_tag", pid, tag))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in sorted(c.tags):
            lines.append(asp.fact("clue_tag", cid, tag))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for tag in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, tag))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("transform_tag", tid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, Q, T) :- place(P), clue(C), quest(Q), transformation(T),
                     (clue_tag(C, tilt); clue_tag(C, tulip); transform_tag(T, tulip); transform_tag(T, transformation)).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        import io
        from contextlib import redirect_stdout
        sample = generate(CURATED[0])
        _ = sample.story
        with redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:
        print(f"FAIL: smoke test failed: {exc}")
        return 1
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP valid combos.")
        if py - cl:
            print("only in python:", sorted(py - cl))
        if cl - py:
            print("only in clingo:", sorted(cl - py))
        return 1
    print(f"OK: verify passed with {len(py)} combos.")
    return 0


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  history={world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_garden", child_name="Mina", child_type="girl", parent_type="mother", clue="tulip_petal", quest="follow_clues", transformation="bloom_open"),
    StoryParams(place="quiet_museum", child_name="Theo", child_type="boy", parent_type="father", clue="tilted_frame", quest="solve_note", transformation="message_clear"),
    StoryParams(place="moonlight_greenhouse", child_name="Nora", child_type="girl", parent_type="mother", clue="tilted_stone", quest="find_key", transformation="color_shift"),
]


def explain_gender(name: str, gender: str) -> str:
    return f"(No story: {name} is not a typical {gender}-only choice here.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.quest is None or c[2] == args.quest)
              and (args.transformation is None or c[3] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, quest, transformation = rng.choice(sorted(combos))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        clue=clue,
        quest=quest,
        transformation=transformation,
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


def generate_from_seed(args: argparse.Namespace, seed: int) -> StorySample:
    params = resolve_params(args, random.Random(seed))
    params.seed = seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            sample = generate_from_seed(args, base_seed + i)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.clue} / {p.quest} / {p.transformation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
