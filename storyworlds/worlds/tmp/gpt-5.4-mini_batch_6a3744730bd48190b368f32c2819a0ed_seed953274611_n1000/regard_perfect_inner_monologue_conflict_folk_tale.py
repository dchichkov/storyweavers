#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/regard_perfect_inner_monologue_conflict_folk_tale.py
====================================================================================

A small folk-tale story world about a child, a boast, a test of regard, and a
perfect repair.  The world keeps a tiny simulated state with physical meters and
emotional memes, includes inner monologue and conflict, and renders a complete
child-facing story from the evolving world model.

Seed words:
- regard
- perfect

Features:
- Inner Monologue
- Conflict

Style:
- Folk Tale
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    light: str
    quiet: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    wish: str
    risk: str
    spoil: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


PLACES = {
    "village": Place(id="village", label="a small village", light="golden light", quiet="soft and close", tags={"folk", "village"}),
    "orchard": Place(id="orchard", label="an old orchard", light="apple-blossom light", quiet="rustling and sweet", tags={"folk", "orchard"}),
    "mill": Place(id="mill", label="a narrow mill", light="dusty light", quiet="creaking and low", tags={"folk", "mill"}),
}

TASKS = {
    "basket": Task(id="basket", verb="carry the berry basket", wish="bring the berries home", risk="the berries would spill", spoil="spill", zone="hands", tags={"basket"}),
    "lamp": Task(id="lamp", verb="lift the lantern", wish="see the path", risk="the lamp could wobble and dim", spoil="dim", zone="hands", tags={"lamp"}),
    "bread": Task(id="bread", verb="bring the warm bread", wish="keep it perfect for supper", risk="the crust would break", spoil="break", zone="arms", tags={"bread"}),
}

OBJECTS = {
    "basket": ObjectCfg(id="basket", label="basket", phrase="a woven berry basket", region="hands", fragile=True, tags={"basket"}),
    "lantern": ObjectCfg(id="lantern", label="lantern", phrase="a little brass lantern", region="hands", fragile=True, tags={"lantern"}),
    "bread": ObjectCfg(id="bread", label="loaf", phrase="a round loaf of bread", region="arms", fragile=True, tags={"bread"}),
}

REMEDIES = {
    "mend": Remedy(id="mend", sense=3, power=3,
                   text="mended the break with a strip of cloth and a careful knot",
                   fail="tried to mend the break, but the crack spread too far",
                   qa_text="mended the break with a strip of cloth and a careful knot",
                   tags={"mend"}),
    "rest": Remedy(id="rest", sense=3, power=2,
                   text="rested the basket on a soft stool and carried it with both hands",
                   fail="rested too late, and the berries still tumbled out",
                   qa_text="rested the basket on a soft stool and carried it with both hands",
                   tags={"rest"}),
    "glue": Remedy(id="glue", sense=1, power=1,
                   text="used a dab of glue and hoped for the best",
                   fail="used a dab of glue, but it was far too weak",
                   qa_text="used a dab of glue",
                   tags={"glue"}),
}

GIRL_NAMES = ["Mara", "Elin", "Tilda", "Nina", "Bela", "Suri"]
BOY_NAMES = ["Jon", "Perrin", "Oren", "Leif", "Dara", "Milo"]
TRAITS = ["careful", "brave", "thoughtful", "gentle", "clever"]


@dataclass
class StoryParams:
    place: str
    task: str
    object: str
    remedy: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS.values():
            for o in OBJECTS.values():
                if t.zone == o.region:
                    combos.append((p, t.id, o.id))
    return combos


def reasonableness_gate(task: Task, obj: ObjectCfg) -> bool:
    return task.zone == obj.region and obj.fragile


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def story_severity(task: Task) -> int:
    return 2 if task.id == "bread" else 1


def is_contained(remedy: Remedy, task: Task) -> bool:
    return remedy.power >= story_severity(task)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about regard, conflict, and a perfect repair.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.object_:
        if not reasonableness_gate(TASKS[args.task], OBJECTS[args.object_]):
            raise StoryError("No story: this task and object do not truly fit together.")
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError("No story: that remedy is too weak and not a sensible folk-tale fix.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.object_ is None or c[2] == args.object_)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, task, obj = rng.choice(sorted(combos))
    remedy = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(GIRL_NAMES + BOY_NAMES).capitalize()
    return StoryParams(place=place, task=task, object=obj, remedy=remedy,
                       hero=hero, hero_gender=hero_gender, elder=elder, elder_gender=elder_gender)


def _do_task(world: World, hero: Entity, task: Task, obj: Entity, narrate: bool = True) -> None:
    hero.memes["desire"] += 1
    hero.meters[task.id] += 1
    obj.meters["risk"] += 1
    if narrate:
        world.say(f"{hero.id} tried to {task.verb}, and the {obj.label_word} trembled in {hero.pronoun('possessive')} hands.")


def _do_conflict(world: World, hero: Entity, elder: Entity, task: Task) -> None:
    hero.memes["conflict"] += 1
    world.say(f"{hero.id} wished to be obedient, yet {hero.pronoun('possessive')} own heart answered: {task.wish}.")


def _do_inner(world: World, hero: Entity, task: Task, obj: Entity) -> None:
    world.say(f'In {hero.id}\'s mind a little voice said, "If I hurry, I may lose the {obj.label}; if I wait, I may lose the chance."')


def _do_remedy(world: World, elder: Entity, remedy: Remedy, obj: Entity) -> None:
    obj.meters["fixed"] += remedy.power
    world.say(f"{elder.id} {remedy.text}.")


def tell(place: Place, task: Task, obj_cfg: ObjectCfg, remedy: Remedy,
         hero: str = "Mara", hero_gender: str = "girl",
         elder: str = "Grandmother", elder_gender: str = "woman") -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero"))
    e = world.add(Entity(id=elder, kind="character", type=elder_gender, role="elder"))
    obj = world.add(Entity(id=obj_cfg.label, type="thing", label=obj_cfg.label, tags=set(obj_cfg.tags)))
    world.facts["place"] = place
    world.facts["task"] = task
    world.facts["object_cfg"] = obj_cfg
    world.facts["remedy"] = remedy
    world.say(f"Once in {place.label}, where the days were {place.quiet}, {h.id} carried {obj_cfg.phrase}.")
    world.say(f"{h.id} longed to {task.wish}, and everything looked {place.light}.")
    world.para()
    _do_inner(world, h, task, obj)
    _do_conflict(world, h, e, task)
    world.say(f'{h.id} thought, "If I keep my regard for what is right, I may still find the perfect way."')
    world.para()
    _do_task(world, h, task, obj)
    if is_contained(remedy, task):
        _do_remedy(world, e, remedy, obj)
        obj.meters["fixed"] += 1
        world.say(f"In the end, the trouble was made right, and the {obj.label} was perfect again.")
        ending = "perfect"
    else:
        world.say(f"The trouble grew too large, and even the wise hands could not set it right.")
        ending = "failed"
    world.facts.update(hero=h, elder=e, object=obj, ending=ending, conflict=True, contained=is_contained(remedy, task))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a child that uses the words "regard" and "perfect" and includes an inner conflict.',
        f"Tell a small folk tale about {f['hero'].id} in {f['place'].label} who wrestles with a choice in their mind and ends with a perfect repair.",
        f"Write a gentle story where {f['elder'].id} helps {f['hero'].id} after a conflict, and the word regard appears naturally.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h: Entity = f["hero"]
    e: Entity = f["elder"]
    t: Task = f["task"]
    o: Entity = f["object"]
    qa = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {h.id}, who faced a hard choice while carrying {o.label_word} in {f['place'].label}. {e.id} helped guide the trouble toward a kinder ending."
        ),
        QAItem(
            question=f"What did {h.id} want to do?",
            answer=f"{h.id} wanted to {t.verb}, but {h.pronoun('possessive')} mind worried about what might go wrong. That inner conflict made the story feel tense for a moment."
        ),
        QAItem(
            question=f"How did {e.id} help?",
            answer=f"{e.id} answered with a calm remedy and showed regard for {h.id}'s feelings. That gentle help turned the problem toward a perfect ending."
        ),
    ]
    if f.get("contained"):
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the trouble made right and the {o.label} perfect again. The folk-tale ending proves the worry did not win."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does regard mean?",
            answer="To show regard is to treat someone or something with care and respect. In a story, that means listening kindly instead of acting careless."
        ),
        QAItem(
            question="What does perfect mean?",
            answer="Perfect means just right, with nothing left wrong or broken. Folk tales often use that kind of ending when a problem has been fixed well."
        ),
        QAItem(
            question="What is an inner conflict?",
            answer="An inner conflict is a struggle inside a person's own mind. They may want one thing, but another feeling warns them to do something wiser."
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,O) :- place(P), task(T), object(O), zone(T,Z), region(O,Z), fragile(O).
sensible(R) :- remedy(R), sense(R,S), sense_min(M), S >= M.
outcome(perfect) :- chosen_remedy(R), chosen_task(T), power(R,P), severity(T,S), P >= S.
outcome(failed) :- chosen_remedy(R), chosen_task(T), power(R,P), severity(T,S), P < S.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("zone", tid, t.zone))
        lines.append(asp.fact("severity", tid, story_severity(t)))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region", oid, o.region))
        if o.fragile:
            lines.append(asp.fact("fragile", oid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_remedy", params.remedy), asp.fact("chosen_task", params.task)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {r.id for r in sensible_remedies()}:
        rc = 1
        print("MISMATCH: ASP sensible remedies differ from Python.")
    else:
        print("OK: sensible remedies match.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    cases = [StoryParams(place=p, task=t, object=o, remedy="mend", hero="Mara", hero_gender="girl", elder="Grandmother", elder_gender="woman")
             for p, t, o in valid_combos()[:3]]
    if all(asp_outcome(c) == ("perfect" if is_contained(REMEDIES[c.remedy], TASKS[c.task]) else "failed") for c in cases):
        print("OK: outcome model matches Python on sample cases.")
    else:
        rc = 1
        print("MISMATCH: outcome model differs from Python.")
    return rc


def explain_rejection(task: Task, obj: ObjectCfg) -> str:
    return "No story: this task and object do not truly fit together, so the folk-tale conflict would be false."


def explain_remedy(rid: str) -> str:
    r = REMEDIES[rid]
    better = ", ".join(sorted(x.id for x in sensible_remedies()))
    return f"No story: remedy '{rid}' is too weak for this world. Try one of: {better}."


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.object not in OBJECTS or params.remedy not in REMEDIES:
        raise StoryError("Invalid parameters for this story world.")
    world = tell(PLACES[params.place], TASKS[params.task], OBJECTS[params.object], REMEDIES[params.remedy],
                 hero=params.hero, hero_gender=params.hero_gender, elder=params.elder, elder_gender=params.elder_gender)
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
    StoryParams(place="village", task="basket", object="basket", remedy="mend", hero="Mara", hero_gender="girl", elder="Grandmother", elder_gender="woman"),
    StoryParams(place="orchard", task="lamp", object="lantern", remedy="rest", hero="Jon", hero_gender="boy", elder="Uncle", elder_gender="man"),
    StoryParams(place="mill", task="bread", object="bread", remedy="mend", hero="Tilda", hero_gender="girl", elder="Aunt", elder_gender="woman"),
]


def resolve_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.hero}: {p.task} in {p.place} ({p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
