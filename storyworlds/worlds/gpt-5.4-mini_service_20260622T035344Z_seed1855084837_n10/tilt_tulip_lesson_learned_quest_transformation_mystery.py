#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035344Z_seed1855084837_n10/tilt_tulip_lesson_learned_quest_transformation_mystery.py
=========================================================================================================

A small mystery-style story world about a garden clue, a tilted object, a tulip,
a quest to solve what is missing, and a transformation when the truth is found.

The world models typed entities with physical meters and emotional memes, then
renders a compact child-facing story with a clear beginning, turn, and ending.
"""

from __future__ import annotations

import argparse
import json
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


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "role": v.role,
            "owner": v.owner, "caretaker": v.caretaker, "plural": v.plural,
            "tags": set(v.tags), "attrs": dict(v.attrs),
            "meters": defaultdict(float, v.meters), "memes": defaultdict(float, v.memes),
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [list(p) for p in self.paragraphs]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Setting:
    name: str
    place: str
    clue_place: str
    has_tilt: bool = True
    mood: str = "quiet"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    objective: str
    search: str
    end_action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    before: str
    after: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    clue: str
    quest: str
    transformation: str
    name: str
    gender: str
    companion: str
    companion_gender: str
    seed: int | None = None


SETTINGS = {
    "garden": Setting(name="garden", place="the garden", clue_place="by the stone bench", has_tilt=True, mood="quiet"),
    "greenhouse": Setting(name="greenhouse", place="the greenhouse", clue_place="near the glass shelf", has_tilt=True, mood="humid"),
    "courtyard": Setting(name="courtyard", place="the courtyard", clue_place="beside the fountain", has_tilt=False, mood="still"),
}

CLUES = {
    "tilted_marker": Clue(id="tilted_marker", label="tilted marker", phrase="a little marker that leaned to one side", reveal="the marker had been nudged", tags={"tilt", "mystery"}),
    "muddy_note": Clue(id="muddy_note", label="muddy note", phrase="a muddy note tucked under a pot", reveal="the note pointed toward the tulip", tags={"mystery", "tulip"}),
    "broken_stake": Clue(id="broken_stake", label="broken stake", phrase="a broken garden stake near the path", reveal="the stake had fallen when the wind blew", tags={"tilt", "mystery"}),
}

QUESTS = {
    "find_tulip": Quest(id="find_tulip", objective="find the missing tulip", search="search for the tulip", end_action="plant the tulip again", tags={"quest", "tulip"}),
    "solve_tilt": Quest(id="solve_tilt", objective="solve the tilted clue", search="follow the tilted clue", end_action="straighten the sign", tags={"quest", "tilt"}),
    "learn_lesson": Quest(id="learn_lesson", objective="learn why the clue mattered", search="look carefully before guessing", end_action="say sorry for the rush", tags={"lesson"}),
}

TRANSFORMATIONS = {
    "bud_to_bloom": Transformation(id="bud_to_bloom", before="a tight bud", after="a bright tulip bloom", image="the tulip stood up straight and opened like a tiny sun", tags={"tulip", "transformation"}),
    "mess_to_clue": Transformation(id="mess_to_clue", before="a small mess", after="a helpful clue", image="the tilted thing became a clue that made sense", tags={"tilt", "mystery", "transformation"}),
    "worry_to_pride": Transformation(id="worry_to_pride", before="a worried face", after="a proud smile", image="their faces changed from worry to proud smiles", tags={"lesson", "transformation"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Sam", "Ben"]
TRAITS = ["curious", "careful", "bright-eyed", "patient", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for clue_id, clue in CLUES.items():
            for quest_id, quest in QUESTS.items():
                if "tulip" in quest.tags and "tulip" not in clue.tags and setting.has_tilt:
                    continue
                if "tilt" in quest.tags and "tilt" not in clue.tags and setting.has_tilt:
                    continue
                if setting_id == "courtyard" and clue_id == "broken_stake" and quest_id == "find_tulip":
                    continue
                combos.append((setting_id, clue_id, quest_id))
    return combos


def _choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery-style story world about a tilt, a tulip, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.quest is None or c[2] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, quest = rng.choice(sorted(combos))
    transformation = args.transformation or rng.choice(sorted(TRANSFORMATIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    name = args.name or _choose_name(rng, gender)
    companion = args.companion or _choose_name(rng, companion_gender)
    if companion == name:
        companion = _choose_name(rng, "boy" if companion_gender == "boy" else "girl")
    return StoryParams(setting=setting, clue=clue, quest=quest, transformation=transformation, name=name, gender=gender, companion=companion, companion_gender=companion_gender)


def _act_search(world: World, hero: Entity, companion: Entity, clue: Clue, quest: Quest, setting: Setting) -> None:
    hero.memes["curiosity"] += 1
    companion.memes["curiosity"] += 1
    world.say(f"{hero.id} and {companion.id} went to {setting.place}, where the air felt {setting.mood}.")
    world.say(f"They were on a quest to {quest.objective}, and they chose to {quest.search}.")
    world.say(f"Near {setting.clue_place}, they found {clue.phrase}.")


def _act_turn(world: World, hero: Entity, companion: Entity, clue: Clue, quest: Quest, transformation: Transformation) -> None:
    hero.memes["wonder"] += 1
    companion.memes["wonder"] += 1
    world.say(f"{hero.id} tilted their head and looked again.")
    world.say(f"Then they noticed that {clue.reveal}.")
    world.say(f"That turned the search from confusion into a clue, and the mystery began to open.")
    world.say(f"At the center of it all was the tulip, which changed through {transformation.image}.")
    hero.meters["understanding"] += 1
    companion.meters["understanding"] += 1
    world.event("discovered", clue=clue.id, quest=quest.id)


def _act_end(world: World, hero: Entity, companion: Entity, quest: Quest, transformation: Transformation) -> None:
    hero.memes["pride"] += 1
    companion.memes["pride"] += 1
    hero.memes["lesson"] += 1
    companion.memes["lesson"] += 1
    world.say(f"In the end, they did not need to guess wildly. They learned that careful looking matters.")
    world.say(f"They finished the quest by {quest.end_action}, and their faces changed into {transformation.after}.")
    world.say(f"The tulip was no longer a mystery to them; it stood there like a small bright answer.")


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    clue = CLUES[params.clue]
    quest = QUESTS[params.quest]
    transformation = TRANSFORMATIONS[params.transformation]
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, role="hero"))
    companion = world.add(Entity(id=params.companion, kind="character", type=params.companion_gender, role="companion"))
    world.facts.update(setting=setting, clue=clue, quest=quest, transformation=transformation, hero=hero, companion=companion)
    world.say(f"One quiet day, {hero.id} and {companion.id} entered {setting.place}.")
    world.say(f"They were curious about a tulip that was missing from its spot.")
    world.para()
    _act_search(world, hero, companion, clue, quest, setting)
    world.para()
    _act_turn(world, hero, companion, clue, quest, transformation)
    world.para()
    _act_end(world, hero, companion, quest, transformation)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    clue: Clue = f["clue"]
    quest: Quest = f["quest"]
    return [
        f"Write a child-friendly mystery story where {hero.id} and {companion.id} search the garden for a tulip and notice a tilt clue.",
        f"Tell a short story in a mystery style about a quest to {quest.objective}, using the words tilt and tulip.",
        f"Write a story where careful looking turns a small tilt into the answer and ends with a happy transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    clue: Clue = f["clue"]
    quest: Quest = f["quest"]
    setting: Setting = f["setting"]
    transformation: Transformation = f["transformation"]
    return [
        QAItem(
            question=f"Why did {hero.id} and {companion.id} go to {setting.place}?",
            answer=f"They went there to {quest.objective}. They also wanted to solve the mystery of the tulip by following a clue carefully instead of guessing too fast.",
        ),
        QAItem(
            question=f"What did they find near {setting.clue_place}?",
            answer=f"They found {clue.phrase}. That tilted clue helped them notice what was really going on.",
        ),
        QAItem(
            question=f"How did the story change at the end?",
            answer=f"The worry turned into {transformation.after}. The tulip and the clue became part of a lesson learned, so the ending felt calm and proud.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that careful looking can solve a mystery. When something seems strange, it helps to pause, tilt your head, and pay attention before deciding.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting: Setting = f["setting"]
    clue: Clue = f["clue"]
    quest: Quest = f["quest"]
    qa: list[QAItem] = [
        QAItem(
            question="What is a tulip?",
            answer="A tulip is a flower with soft petals. It grows from a bulb in the ground and can open into a bright bloom.",
        ),
        QAItem(
            question="What does tilt mean?",
            answer="Tilt means to lean to one side instead of standing straight. A tilted thing can look like it is trying to point somewhere.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. In stories, a quest often means following clues until you find the answer.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a big change. In a story, it can mean a feeling, a clue, or a place becomes something new and clearer.",
        ),
    ]
    if "tulip" in clue.tags or quest.id == "find_tulip":
        qa.append(QAItem(
            question=f"Why might a tulip matter in {setting.place}?",
            answer="A tulip can matter because it stands out as a small bright flower. In a mystery, something that special can become the key detail that helps solve the puzzle.",
        ))
    return qa


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", clue="tilted_marker", quest="find_tulip", transformation="bud_to_bloom", name="Mia", gender="girl", companion="Theo", companion_gender="boy", seed=1),
    StoryParams(setting="greenhouse", clue="muddy_note", quest="learn_lesson", transformation="worry_to_pride", name="Leo", gender="boy", companion="Nora", companion_gender="girl", seed=2),
    StoryParams(setting="garden", clue="broken_stake", quest="solve_tilt", transformation="mess_to_clue", name="Ava", gender="girl", companion="Finn", companion_gender="boy", seed=3),
]


def explain_rejection(setting: str, clue: str, quest: str) -> str:
    return f"(No story: the chosen setting, clue, and quest do not fit together for a clear mystery.)"


ASP_RULES = r"""
valid(S,C,Q) :- setting(S), clue(C), quest(Q), fit(S,C,Q).
fit(S,C,Q) :- setting(S), clue(C), quest(Q), quest_tag(Q,tulip), clue_tag(C,tulip).
fit(S,C,Q) :- setting(S), clue(C), quest(Q), quest_tag(Q,tilt), clue_tag(C,tilt).
fit(S,C,Q) :- setting(S), clue(C), quest(Q), quest_tag(Q,lesson).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_tilt:
            lines.append(asp.fact("has_tilt", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for tag in sorted(c.tags):
            lines.append(asp.fact("clue_tag", cid, tag))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for tag in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = True
    if python_set != clingo_set:
        ok = False
        print("MISMATCH between ASP and Python valid_combos():")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        if not buf.getvalue().strip():
            raise RuntimeError("empty emit output")
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    if ok:
        print(f"OK: ASP matches Python on {len(python_set)} combos; smoke test passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.clue not in CLUES or params.quest not in QUESTS or params.transformation not in TRANSFORMATIONS:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.clue} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
