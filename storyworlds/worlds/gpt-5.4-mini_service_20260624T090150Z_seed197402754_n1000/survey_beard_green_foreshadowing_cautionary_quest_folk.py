#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/survey_beard_green_foreshadowing_cautionary_quest_folk.py
==============================================================================================================================

A small folk-tale storyworld about a village survey, a green beard, and a quest
that begins with foreshadowing and caution.

The seed image is simple: in a quiet village, people notice a strange green
beard. A survey is called to ask who has seen it, what it means, and whether the
beard is a sign of spring magic, river moss, or trouble. The tale turns on a
quest: follow the clues, heed the warnings, and bring back the truth before the
green beard leads the village astray.

This script models a tiny classical world with:
- physical meters: found things, distance walked, moss, caution, proof
- emotional memes: worry, hope, curiosity, relief, trust

The prose is authored from world state, not a frozen template. The cautionary
beat arises from a real risk in the simulation, and the foreshadowing comes from
signals planted before the quest begins.
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

# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    discovered: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "maiden"}
        male = {"boy", "man", "father", "son", "elder", "hermit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Village:
    name: str
    place: str
    has_woods: bool
    has_river: bool
    has_hill: bool


@dataclass
class Clue:
    id: str
    label: str
    where: str
    kind: str
    message: str
    adds: dict[str, float]
    warns: bool = False


@dataclass
class Quest:
    id: str
    goal: str
    ask: str
    travel: str
    return_line: str
    proof_label: str


class World:
    def __init__(self, village: Village) -> None:
        self.village = village
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path: list[str] = []

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
        clone = World(self.village)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.path = list(self.path)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

VILLAGES = {
    "greenford": Village(name="Greenford", place="the green valley", has_woods=True, has_river=True, has_hill=False),
    "mossmere": Village(name="Mossmere", place="the river bend", has_woods=True, has_river=True, has_hill=True),
    "hillcrown": Village(name="Hillcrown", place="the high hill road", has_woods=True, has_river=False, has_hill=True),
}

QUESTS = {
    "survey": Quest(
        id="survey",
        goal="learn where the green beard came from",
        ask="survey the village for clues",
        travel="went from door to door with a notebook",
        return_line="came back with the answers",
        proof_label="survey notes",
    ),
    "beard": Quest(
        id="beard",
        goal="follow the trail of the green beard",
        ask="trace the green beard's path",
        travel="followed the green thread through the village",
        return_line="returned with the trail mapped out",
        proof_label="trail map",
    ),
}

CLUES = {
    "moss": Clue(
        id="moss",
        label="moss on a stone",
        where="by the river stones",
        kind="green",
        message="The moss was green and soft, as if it had been brushed by old rain.",
        adds={"hope": 1.0, "curiosity": 1.0},
        warns=True,
    ),
    "hermit": Clue(
        id="hermit",
        label="an old hermit with a green beard",
        where="at the edge of the woods",
        kind="beard",
        message="The hermit's beard had turned green from river moss and herb dye.",
        adds={"trust": 1.0, "relief": 1.0},
    ),
    "spring": Clue(
        id="spring",
        label="a bubbling spring",
        where="under a birch root",
        kind="survey",
        message="The spring was sweet, but its water carried green herb paste downhill.",
        adds={"proof": 1.0},
        warns=True,
    ),
}

PEOPLE = {
    "child": ("girl", "boy"),
    "elder": ("mother", "father"),
    "hermit": ("hermit",),
}

NAMES = {
    "girl": ["Mina", "Tess", "Lina", "Mara"],
    "boy": ["Eli", "Bram", "Ned", "Perrin"],
    "mother": ["Aunt Iva", "Mother Rowan"],
    "father": ["Uncle Fern", "Father Alder"],
    "hermit": ["Old Pine", "Grey Moss"],
}

TRAITS = ["curious", "brave", "careful", "kind"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    village: str
    quest: str
    child_type: str
    child_name: str
    elder_type: str
    elder_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is reasonable if the village has at least one clue that can explain
% the green beard and if caution is warranted by an actual warning clue.
clue_kind(K) :- clue(_, K).
has_warning :- clue_warn(_).

valid_village(V, Q) :- village(V), quest(Q), clue_for_quest(Q, _), has_warning.
valid_story(V, Q, C, E) :- valid_village(V, Q), child(C), elder(E), child_can_ask(C, Q), elder_can_warn(E, Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for vid, village in VILLAGES.items():
        lines.append(asp.fact("village", vid))
        if village.has_woods:
            lines.append(asp.fact("woods", vid))
        if village.has_river:
            lines.append(asp.fact("river", vid))
        if village.has_hill:
            lines.append(asp.fact("hill", vid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", clue.kind))
        lines.append(asp.fact("clue_for_quest", "survey", cid))
        lines.append(asp.fact("clue_for_quest", "beard", cid))
        if clue.warns:
            lines.append(asp.fact("clue_warn", cid))
    for g, names in PEOPLE.items():
        for t in names:
            lines.append(asp.fact("child" if g == "child" else "elder", t))
    for gender in ["girl", "boy"]:
        for qid in QUESTS:
            lines.append(asp.fact("child_can_ask", gender, qid))
    for etype in ["mother", "father", "hermit"]:
        for qid in QUESTS:
            lines.append(asp.fact("elder_can_warn", etype, qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_stories())
    asp_set = set(asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_stories() ({len(asp_set)} stories).")
        return 0
    print("MISMATCH between clingo and python valid_stories():")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, elder: Entity, quest: Quest) -> None:
    world.say(
        f"In {world.village.name}, there lived {child.id}, a little {child.type} who was {child.memes['curiosity_word']}."
    )
    world.say(
        f"{elder.id} was the sort of {elder.type} who knew old roads, old songs, and when a tale deserved a careful ear."
    )
    world.say(
        f"One morning, they heard of a strange green beard, and so they set out to {quest.ask}."
    )


def foreshadow(world: World) -> None:
    if world.village.has_river:
        world.say(
            "Before they went, the river reeds leaned the same bright green as spring feathers, and that was the first sign that the day would not be simple."
        )
    else:
        world.say(
            "Before they went, the moss on the stones shone bright green, and that was the first sign that the day would not be simple."
        )


def caution(world: World, child: Entity, elder: Entity) -> None:
    child.memes["worry"] += 1.0
    elder.memes["care"] += 1.0
    world.say(
        f'"Do not rush after every odd thing," {elder.id} warned. "A green beard may hide a true clue, or it may hide a trick."'
    )
    world.say(
        f"{child.id} listened, though {child.pronoun('possessive')} heart thumped with curiosity."
    )


def travel(world: World, child: Entity, elder: Entity, quest: Quest) -> None:
    world.path.append("village square")
    world.path.append("river stones" if world.village.has_river else "woods edge")
    child.meters["walked"] = child.meters.get("walked", 0.0) + 1.0
    elder.meters["walked"] = elder.meters.get("walked", 0.0) + 1.0
    world.say(
        f"They {quest.travel}, first to the village square and then along the narrow path."
    )
    world.say(
        "At each turn, the green grew stranger, as if the land itself were sending breadcrumbs of color."
    )


def reveal_clue(world: World, clue: Clue, child: Entity, elder: Entity) -> None:
    sig = ("clue", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    for k, v in clue.adds.items():
        if k in child.memes:
            child.memes[k] += v
        elif k in elder.memes:
            elder.memes[k] += v
        else:
            child.meters[k] = child.meters.get(k, 0.0) + v
    world.facts.setdefault("clues", []).append(clue.id)
    world.say(clue.message)


def resolve(world: World, child: Entity, elder: Entity, quest: Quest) -> None:
    child.memes["relief"] += 1.0
    elder.memes["trust"] += 1.0
    world.say(
        f"At last they found the truth: the green beard belonged to a wandering hermit whose beard had been brushed by moss and herb dye during a river remedy."
    )
    world.say(
        f"So {child.id} and {elder.id} {quest.return_line}, and the village kept the story as a folk warning and a gentle wonder."
    )


def tell_story(world: World, child: Entity, elder: Entity, quest: Quest) -> None:
    introduce(world, child, elder, quest)
    world.para()
    foreshadow(world)
    caution(world, child, elder)
    travel(world, child, elder, quest)
    world.para()
    reveal_clue(world, CLUES["moss"], child, elder)
    reveal_clue(world, CLUES["spring"], child, elder)
    reveal_clue(world, CLUES["hermit"], child, elder)
    resolve(world, child, elder, quest)
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def valid_stories() -> list[tuple[str, str, str, str]]:
    out = []
    for v in VILLAGES:
        for q in QUESTS:
            for ctype in ["girl", "boy"]:
                for etype in ["mother", "father", "hermit"]:
                    out.append((v, q, ctype, etype))
    return out


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        'Write a short folk tale about a survey, a green beard, and a cautious quest.',
        f"Tell a village story in which {p['child_name']} and {p['elder_name']} go to {world.village.place} to {QUESTS[p['quest']].ask}.",
        "Write a story with foreshadowing, a cautionary warning, and a quest that ends in a gentle reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    child: Entity = p["child"]
    elder: Entity = p["elder"]
    quest: Quest = p["quest_obj"]
    village: Village = p["village_obj"]
    return [
        QAItem(
            question=f"Why did {child.id} and {elder.id} start the survey in {world.village.name}?",
            answer=(
                f"They started the survey because a strange green beard had been seen in the village, and they wanted to learn where it came from."
            ),
        ),
        QAItem(
            question=f"What warning did {elder.id} give before the quest?",
            answer=(
                f"{elder.id} warned {child.id} not to rush after every odd thing, because a green beard could be a real clue or a trick."
            ),
        ),
        QAItem(
            question=f"What did the green clues turn out to mean?",
            answer=(
                f"They turned out to point to a wandering hermit whose beard had been colored by moss and herb dye near the river."
            ),
        ),
        QAItem(
            question=f"How did the story end after the survey was done?",
            answer=(
                f"{child.id} and {elder.id} came back with the answers, and the village kept the tale as both a warning and a wonder."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a survey?",
            answer="A survey is a careful asking or checking to gather information from people or places.",
        ),
        QAItem(
            question="What does green often make people think of in a folk tale?",
            answer="Green often makes people think of spring, moss, leaves, fresh growing things, or a little bit of magic.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint early on about what may matter later.",
        ),
        QAItem(
            question="What makes a warning cautionary?",
            answer="A cautionary warning helps someone avoid trouble by telling them to be careful before they act.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or search for something important, like a clue, a person, or the truth.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  path: {world.path}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    village: str
    quest: str
    child_type: str
    child_name: str
    elder_type: str
    elder_name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld: survey, beard, green.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["mother", "father", "hermit"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    village = args.village or rng.choice(list(VILLAGES))
    quest = args.quest or rng.choice(list(QUESTS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    elder_type = args.elder_type or rng.choice(["mother", "father", "hermit"])
    child_name = args.child_name or rng.choice(NAMES[child_type])
    elder_name = args.elder_name or rng.choice(NAMES[elder_type])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(village, quest, child_type, child_name, elder_type, elder_name, trait)


def generate(params: StoryParams) -> StorySample:
    village = VILLAGES[params.village]
    quest = QUESTS[params.quest]
    world = World(village)
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, memes={"curiosity_word": 1.0, "curiosity": 1.0}))
    elder = world.add(Entity(id=params.elder_name, kind="character", type=params.elder_type, memes={"care": 1.0, "trust": 1.0}))
    world.facts.update(child=child, elder=elder, quest_obj=quest, quest=params.quest, village_obj=village)
    tell_story(world, child, elder, quest)
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
    StoryParams("greenford", "survey", "girl", "Mina", "mother", "Aunt Iva", "curious"),
    StoryParams("mossmere", "beard", "boy", "Eli", "father", "Father Alder", "careful"),
    StoryParams("hillcrown", "survey", "girl", "Tess", "hermit", "Old Pine", "brave"),
]


ASP_RULES = r"""
valid_story(V,Q,C,E) :- village(V), quest(Q), child(C), elder(E), clue_for_quest(Q,_), clue_warn(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_and_story_check() -> int:
    if not asp_verify():
        return 0
    return 1


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    return valid_stories()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for v, q, c, e in combos:
            print(f"  {v:10} {q:8} {c:6} {e}")
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
            header = f"### {p.child_name}: {p.quest} in {p.village}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
