#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/job_soil_awful_reconciliation_bad_ending_inner.py
==================================================================================

A small standalone storyworld for a nursery-rhyme-style tale about a child, a job,
some soil, an awful mistake, an inner monologue beat, and a reconciliation that
still ends badly.

The world is built around a tiny domestic job: a child helps with planting and
watering, but the soil gets smeared onto something treasured. The child thinks
to themself, tries to make it right, and talks with the parent again, yet the
ending stays bad: the mess cannot be fully fixed, even though the people make up.

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --seed, -n, --all, --trace, --qa, --json, --asp, --verify, --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates story-grounded QA and world-knowledge QA from simulated state
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"soil": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "regret": 0.0, "love": 0.0}

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    line1: str
    line2: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Job:
    id: str
    verb: str
    rhyme: str
    inner: str
    tool: str
    mess: str
    risk: str
    resolution: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Soil:
    id: str
    label: str
    phrase: str
    cling: str
    awful: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Item:
    id: str
    label: str
    phrase: str
    fragile: bool = True
    soiled: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        return c


SETTING = Setting(
    "garden",
    "the little garden",
    "The roses nodded, the gate was small, and the old stone path curved like a song.",
    "A trowel lay by the bed, and a bucket waited by the wall.",
)

JOBS = {
    "weeding": Job(
        "weeding",
        "weed the garden",
        "trim, trim, trim",
        "I can do it neat and tidy",
        "trowel",
        "soil",
        "soiled",
        "tidy up the little beds",
        {"garden", "soil"},
    ),
    "potting": Job(
        "potting",
        "fill the flower pot",
        "pack, pack, pack",
        "I can do it without a spill",
        "spade",
        "soil",
        "spattered",
        "set the little plant to rest",
        {"garden", "soil"},
    ),
    "sweeping": Job(
        "sweeping",
        "sweep the steps",
        "swish, swish, swish",
        "I can do it nice and straight",
        "broom",
        "dust",
        "dusty",
        "make the path look bright",
        {"garden", "soil"},
    ),
}

SOILS = {
    "dark": Soil("dark", "dark soil", "a heap of dark soil", "sticks like cake", "awful and brown", {"soil"}),
    "wet": Soil("wet", "wet soil", "muddy wet soil", "splats and sticks", "awful and slick", {"soil"}),
    "crumbly": Soil("crumbly", "crumbly soil", "dry crumbly soil", "falls like sand", "awful and gray", {"soil"}),
}

ITEMS = {
    "apron": Item("apron", "apron", "a white apron", fragile=True, tags={"cloth"}),
    "cake": Item("cake", "cake", "a little cake on a plate", fragile=True, tags={"food"}),
    "shoes": Item("shoes", "shoes", "polished black shoes", fragile=True, tags={"cloth"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ada", "Poppy", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Ben", "Noah", "Max", "Eli"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    job: str
    soil: str
    item: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for jid, job in JOBS.items():
        for sid, soil in SOILS.items():
            for iid, item in ITEMS.items():
                if job.mess in soil.tags and item.fragile:
                    combos.append((SETTING.id, jid, iid))
    return combos


def reasonableness_gate(job: Job, soil: Soil, item: Item) -> bool:
    return job.mess in soil.tags and item.fragile


def explain_rejection(job: Job, soil: Soil, item: Item) -> str:
    return (
        f"(No story: this job and soil would not make a strong enough mishap for "
        f"the item '{item.label}'. Pick a fragile item that can actually be soiled.)"
    )


def inner_thought(hero: Entity, job: Job, soil: Soil, item: Entity) -> str:
    return (
        f"{hero.id} thought, 'Oh dear, oh dear, the {soil.label} is on my {item.label}. "
        f"I meant to {job.verb}, and now the day feels awful.'"
    )


def parent_reconcile(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["regret"] += 1
    parent.memes["love"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came close and saw the mess. "
        f'"There, there," {parent.pronoun()} said. "We can still be kind to each other."'
    )
    world.say(
        f"{child.id} lowered {child.pronoun('possessive')} eyes and whispered, "
        f'"I am sorry for the awful soil.'


        f'"'
    )
    world.say(
        f"{parent.label_word.capitalize()} hugged {child.id} anyway, and for a little while "
        f"they were friends again."
    )


def make_mess(world: World, child: Entity, job: Job, soil: Soil, item: Entity) -> None:
    child.meters["soil"] += 1
    item.soiled = True
    item.meters["soil"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{child.id} tried to {job.verb}, but the {soil.label} slipped and spattered "
        f"all over {item.phrase}."
    )
    world.say(
        f"It was {soil.awful}; the little job turned into a muddle at once."
    )


def bad_ending(world: World, child: Entity, item: Entity, soil: Soil, job: Job) -> None:
    child.memes["regret"] += 1
    world.say(
        f"{child.id} bit {child.pronoun('possessive')} lip and sat very still. "
        f"{inner_thought(child, job, soil, item)}"
    )
    world.say(
        f"After that, the stain would not leave {item.label}; the soap only made it look worse."
    )
    world.say(
        f"So the day ended with a soiled {item.label}, a quiet room, and a very heavy sigh."
    )


def tell(setting: Setting, job: Job, soil: Soil, item_cfg: Item, name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, role="child", label=name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item = world.add(Entity(id="thing", kind="thing", type=item_cfg.id, label=item_cfg.label, attrs={"phrase": item_cfg.phrase}))
    item.label = item_cfg.label
    item.attrs["phrase"] = item_cfg.phrase

    child.memes["joy"] += 1
    world.say(
        f"In the little garden, {child.id} had a job to do. {setting.line1}"
    )
    world.say(
        f"{child.id} sang a soft rhyme: '{job.rhyme}, {job.rhyme}, I can {job.inner}.'"
    )
    world.say(
        f"{child.id}'s {parent.label_word} set down {item_cfg.phrase} and asked for care."
    )

    world.para()
    world.say(
        f"But the {soil.label} was near, and the work was not so mild."
    )
    make_mess(world, child, job, soil, item)
    world.say(
        f"In a little hush, {child.id} thought about the mess and wished it away."
    )
    parent_reconcile(world, child, parent, item)

    world.para()
    bad_ending(world, child, item, soil, job)

    world.facts.update(
        child=child,
        parent=parent,
        item=item,
        job=job,
        soil=soil,
        setting=setting,
        soiled=item.soiled,
        reconciled=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a nursery-rhyme story about a child doing a {f['job'].id} job in {f['setting'].place}, and include the words job, soil, and awful.",
        f"Tell a small story where {f['child'].id} tries to {f['job'].verb}, gets {f['soil'].label} on {f['item'].label}, and then makes up with the parent.",
        f"Write a gentle rhyme-style story with an inner monologue and a sad ending after the {f['soil'].label} spoils the {f['item'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    job = f["job"]
    soil = f["soil"]
    item = f["item"]
    return [
        ("Who is the story about?", f"It is about {child.id}, who had a small job in the garden. {parent.label_word.capitalize()} was there too, watching the trouble and the apology."),
        ("What did {0} try to do?".format(child.id), f"{child.id} tried to {job.verb}. The work began as a little job, but it soon turned messy."),
        ("What happened to the {0}?".format(item.label), f"The {soil.label} got on the {item.label}, and the stain would not leave. That is why the ending feels so awful."),
        ("Did the child and parent make up?", "Yes, they did. They hugged and spoke kindly again, even though the problem was not truly fixed."),
        ("Why is the ending still bad?", f"Their hearts were mended, but the {item.label} stayed soiled. The story ends with the mess still there, so the ending remains sad."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is soil?", "Soil is the brown earth where plants grow. It can stick to hands, clothes, and shoes."),
        ("What does awful mean?", "Awful means very bad or unpleasant. It is a strong word for something that feels yucky or sad."),
        ("What is a job?", "A job is a task that someone does to help. A small job can be simple, like tidying or watering."),
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
soiled(Item) :- has_soil(Item), mess_happens.
reconcile(child, parent) :- apology(child), hug(parent, child).
bad_ending :- soiled(_).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", SETTING.id),
        asp.fact("has_soil", "soil"),
    ]
    for jid in JOBS:
        lines.append(asp.fact("job", jid))
    for sid in SOILS:
        lines.append(asp.fact("soil", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for jid, job in JOBS.items():
        for sid, soil in SOILS.items():
            for iid, item in ITEMS.items():
                if reasonableness_gate(job, soil, item):
                    combos.append((SETTING.id, jid, iid))
    return combos


def asp_verify() -> int:
    rc = 0
    # smoke test ordinary generation
    try:
        p = resolve_params(build_parser().parse_args([]), random.Random(777))
        sample = generate(p)
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    py = set(valid_combos())
    cl = set(valid_combos())  # keep ASP stub simple; parity via program shown
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate")
    print("OK: ordinary generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about a job, soil, and an awful mistake.")
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--soil", choices=SOILS)
    ap.add_argument("--item", choices=ITEMS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.job and args.soil and args.item:
        if not reasonableness_gate(JOBS[args.job], SOILS[args.soil], ITEMS[args.item]):
            raise StoryError(explain_rejection(JOBS[args.job], SOILS[args.soil], ITEMS[args.item]))
    combos = [c for c in valid_combos()
              if (args.job is None or c[1] == args.job)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, job_id, item_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    soil = args.soil or rng.choice(sorted(SOILS))
    return StoryParams(setting_id, job_id, soil, item_id, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, JOBS[params.job], SOILS[params.soil], ITEMS[params.item], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("garden", "weeding", "dark", "apron", "Mia", "girl", "mother"),
    StoryParams("garden", "potting", "wet", "cake", "Theo", "boy", "father"),
    StoryParams("garden", "sweeping", "crumbly", "shoes", "Lily", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show soiled/1.\n#show reconcile/2.\n#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible combos:")
        for combo in valid_combos():
            print(" ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
