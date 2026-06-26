#!/usr/bin/env python3
"""
A small fable-like storyworld about a stickery trail, a shared task, and a
reconciliation after a sticky mishap.

This world is intentionally compact:
- a child-facing animal fable style
- foreshadowing that hints at trouble before it lands
- sound effects woven into the narration
- reconciliation as the ending turn
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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "bear", "lion", "he", "him", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"rabbit", "mouse", "hedgehog", "bird", "she", "her", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    affords: set[str] = field(default_factory=set)
    detail: str = ""


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    sound: str
    foreshadow: str
    stickiness: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Token:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"fox", "rabbit", "bear", "mouse", "bird"})


@dataclass
class StoryParams:
    place: str
    task: str
    token: str
    hero: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.parts: list[list[str]] = [[]]
        self.current_task: Optional[Task] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.parts[-1].append(text)

    def para(self) -> None:
        if self.parts[-1]:
            self.parts.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.parts if p)

    def carry(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.parts = [[]]
        w.current_task = self.current_task
        return w


def _r_stick(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("stickery", 0.0) < THRESHOLD:
            continue
        for item in world.carry(actor):
            if item.meters.get("protected", 0.0) >= THRESHOLD:
                continue
            sig = ("stick", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["stickery"] = item.meters.get("stickery", 0.0) + 1.0
            item.meters["messy"] = item.meters.get("messy", 0.0) + 1.0
            out.append(f"{item.label.capitalize()} got all stuck to {actor.pronoun('possessive')} paw.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("stickery", 0.0) < THRESHOLD:
            continue
        sig = ("spill", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1.0
        out.append("Uh-oh, the sticky bit spread farther than anyone hoped.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.memes.get("grudge", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["grudge"] = 0.0
        actor.memes["warmth"] = actor.memes.get("warmth", 0.0) + 1.0
        out.append(f"{actor.id} softened and looked ready to forgive.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_stick, _r_spill, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "orchard": Place("the orchard", affords={"honey", "jam"}, detail="The orchard smelled sweet and bright."),
    "kitchen": Place("the kitchen", affords={"jam", "honey"}, detail="The kitchen was warm and busy."),
    "garden": Place("the garden", affords={"sap"}, detail="The garden had shiny leaves and narrow paths."),
}

TASKS = {
    "honey": Task(
        id="honey",
        verb="carry the honey jar",
        gerund="carrying the honey jar",
        sound="glug-glug",
        foreshadow="The lid wobbled with a tiny creak before anyone lifted it.",
        stickiness="sticky gold spilled",
        risk="stuck paws and a mess on the trail",
        tags={"honey", "sticky"},
    ),
    "jam": Task(
        id="jam",
        verb="carry the jam bowl",
        gerund="carrying the jam bowl",
        sound="plip-plop",
        foreshadow="A red drop trembled at the rim like it wanted to jump.",
        stickiness="sticky jam splashed",
        risk="red paws and a sweet spill",
        tags={"jam", "sticky"},
    ),
    "sap": Task(
        id="sap",
        verb="carry the sap cup",
        gerund="carrying the sap cup",
        sound="drip-drop",
        foreshadow="The sap shone in the cup as if it were already planning trouble.",
        stickiness="thick sap smeared",
        risk="glued toes and a slow trail",
        tags={"sap", "sticky"},
    ),
}

TOKENS = {
    "scarf": Token("scarf", "a little scarf", "neck", genders={"fox", "rabbit", "bird"}),
    "apron": Token("apron", "a neat apron", "torso", genders={"fox", "rabbit", "bear", "mouse"}),
    "wrap": Token("wrap", "a cloth wrap", "paws", genders={"fox", "rabbit", "bear", "mouse", "bird"}),
}

HEROES = [
    ("Pip", "mouse"),
    ("Mina", "rabbit"),
    ("Tobin", "fox"),
    ("Bram", "bear"),
]

HELPERS = [
    ("Nora", "rabbit"),
    ("Sage", "fox"),
    ("Lila", "mouse"),
    ("Gus", "bear"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like sticky storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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


def reason_ok(place: Place, task: Task, token: Token) -> bool:
    return task.id in place.affords and token.region in {"paws", "neck", "torso"}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = []
    for p in PLACES:
        if args.place and p != args.place:
            continue
        for t in TASKS:
            if args.task and t != args.task:
                continue
            for tok in TOKENS:
                if args.token and tok != args.token:
                    continue
                if reason_ok(PLACES[p], TASKS[t], TOKENS[tok]):
                    choices.append((p, t, tok))
    if not choices:
        raise StoryError("No reasonable sticky tale fits those options.")
    p, t, tok = rng.choice(choices)
    hero = args.hero or rng.choice([h for h, _ in HEROES])
    helper = args.helper or rng.choice([h for h, _ in HELPERS if h != hero])
    return StoryParams(place=p, task=t, token=tok, hero=hero, helper=helper)


def predict(world: World, hero: Entity, task: Task, token: Entity) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.meters["stickery"] = 1.0
    h.memes["worry"] = 1.0
    item = sim.get(token.id)
    item.carried_by = h.id
    propagate(sim, narrate=False)
    return {"messy": item.meters.get("messy", 0.0) >= THRESHOLD}


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    task = TASKS[params.task]
    token = TOKENS[params.token]
    world.current_task = task

    hero = world.add(Entity(id=params.hero, kind="character", type="fox"))
    helper = world.add(Entity(id=params.helper, kind="character", type="rabbit"))
    trinket = world.add(Entity(id="trinket", type=params.token, label=token.label, phrase=token.phrase, owner=hero.id))
    trinket.carried_by = hero.id

    world.say(f"{hero.id} lived in a quiet place where small choices mattered.")
    world.say(f"{hero.id} liked {task.gerund}, but {task.foreshadow.lower()}")  # foreshadowing
    world.say(f"At the edge of the day, the path went {task.sound}; the sticky story had begun.")
    world.say(f"{hero.id} wore {token.phrase}, and that made the work feel special.")

    world.para()
    world.say(f"One morning in {world.place.name}, {world.place.detail}")
    world.say(f"{hero.id} and {helper.id} set out to {task.verb}.")
    world.say(f"{hero.id} whispered, \"{task.sound}!\" as {token.label} brushed close to the jar.")
    hero.meters["stickery"] = 1.0

    if predict(world, hero, task, trinket)["messy"]:
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
        helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
        world.say(f"{helper.id} saw the wobble and said, \"Careful now.\"")
        world.say(f"{hero.id} tried to hurry anyway, and then came a soft {task.sound}.")
        propagate(world, narrate=True)
        hero.memes["grudge"] = 1.0
        world.say(f"{hero.id} frowned because the spill had turned the path into a sticky puzzle.")
    else:
        world.say(f"The task stayed neat, which was a relief.")

    world.para()
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1.0
    world.say(f"Then {helper.id} fetched cool water and a cloth wrap.")
    world.say(f"Together they cleaned the {task.id} mess, {helper.id} humming, \"swish-swish.\"")
    trinket.meters["protected"] = 1.0
    world.say(f"{hero.id} apologized, and {helper.id} smiled back.")
    world.say(f"They shared the last bit of honey or jam only after the trail was clean.")
    world.say(f"{hero.id} and {helper.id} walked home side by side, no longer cross, only careful and kind.")
    world.say("The little moral was simple: when a sticky mistake happens, a gentle apology can make room for friendship again.")

    world.facts.update(hero=hero, helper=helper, task=task, token=trinket, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for young children about "{f["task"].id}" and a sticky mistake.',
        f"Tell a story where {f['hero'].id} and {f['helper'].id} share {f['task'].gerund} and then make up.",
        f'Create a child-friendly fable with foreshadowing, a sticky spill, and a happy reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = f["task"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    token: Entity = f["token"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {world.place.name}?",
            answer=f"{hero.id} was trying to {task.verb}.",
        ),
        QAItem(
            question=f"What warning did the story give before the sticky trouble?",
            answer=task.foreshadow,
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the problem?",
            answer=f"They cleaned the sticky mess together, and {hero.id} apologized. After that, they were kind to each other again.",
        ),
        QAItem(
            question=f"What did {hero.id} wear that made the job feel special?",
            answer=f"{hero.id} wore {token.phrase}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    task: Task = world.facts["task"]
    if task.id == "honey":
        return [QAItem(question="What is honey?", answer="Honey is a sweet, sticky food made by bees.")]
    if task.id == "jam":
        return [QAItem(question="What is jam?", answer="Jam is a sweet spread made from cooked fruit and sugar.")]
    return [QAItem(question="What is sap?", answer="Sap is a sticky liquid that comes from plants and trees.")]


ASP_RULES = r"""
task_ok(P,T) :- place(P), task(T), affords(P,T).
story_ok(P,T,K) :- task_ok(P,T), token(K).
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for kid in TOKENS:
        lines.append(asp.fact("token", kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    asp_set = set(asp.atoms(model, "story_ok"))
    py_set = set()
    for p in PLACES:
        for t in TASKS:
            for k in TOKENS:
                if reason_ok(PLACES[p], TASKS[t], TOKENS[k]):
                    py_set.add((p, t, k))
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    if asp_set - py_set:
        print("Only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("Only in Python:", sorted(py_set - asp_set))
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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(place="orchard", task="honey", token="scarf", hero="Pip", helper="Nora"),
    StoryParams(place="kitchen", task="jam", token="apron", hero="Mina", helper="Sage"),
    StoryParams(place="garden", task="sap", token="wrap", hero="Tobin", helper="Lila"),
]


def build_asp_show() -> str:
    return asp_program("#show story_ok/3.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(build_asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(build_asp_show())
        vals = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(vals)} compatible stories:")
        for v in vals:
            print(" ", v)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.hero}: {p.task} at {p.place} with {p.token}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
