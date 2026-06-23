#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T045816Z_seed1855084837_n10/scrub_reconciliation_surprise_moral_value_slice_of.py
===============================================================================================================

A small slice-of-life storyworld about a child, a messy little accident,
a scrubby cleanup, a surprise, and a gentle reconciliation.

The world stays compact: one entity model, one world state, a small set of
registries, a short forward rule engine, and a state-driven renderer.
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
from typing import Callable, Optional

def _repo_root() -> str:
    here = os.path.abspath(__file__)
    cur = os.path.dirname(here)
    while True:
        if os.path.exists(os.path.join(cur, "results.py")):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return os.path.dirname(os.path.dirname(here))
        cur = parent

sys.path.insert(0, _repo_root())
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    caretaker: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)
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

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Job:
    id: str
    verb: str
    noun: str
    mess: str
    stain: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_scrub(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["scrubbing"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.id != world.facts.get("target_id"):
                continue
            sig = ("scrubbed", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = max(0.0, item.meters["dirty"] - 1)
            item.meters["clean"] += 1
            out.append(f"{item.label_word.capitalize()} looked brighter after the scrubbing.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["apology"] < THRESHOLD or actor.memes["forgive"] < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["sadness"] = 0.0
        actor.memes["warmth"] += 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("scrub", "physical", _r_scrub), Rule("reconcile", "social", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_cleanup(world: World, actor: Entity, item_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["scrubbing"] = 1
    sim.facts["target_id"] = item_id
    propagate(sim, narrate=False)
    return sim.get(item_id).meters["clean"] >= THRESHOLD


def setup_sentence(place: Place, job: Job) -> str:
    if place.indoors:
        return f"The room was quiet, and the little {job.keyword} job waited near the window."
    return f"{place.label.capitalize()} was bright and calm, with the little {job.keyword} job waiting outside."


def _scrub(world: World, actor: Entity, item: Entity) -> None:
    actor.meters["scrubbing"] += 1
    world.zone = set(world.facts["zone"])
    propagate(world, narrate=True)


def tell(place: Place, job: Job, item_cfg: Item, surprise_cfg: Surprise, hero_name: str,
         hero_type: str, friend_name: str, friend_type: str, parent_type: str = "mother") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    item = world.add(Entity(
        id="target", kind="thing", type="thing", label=item_cfg.label, phrase=item_cfg.phrase,
        owner=hero.id, caretaker=parent.id, plural=item_cfg.plural, tags=set(item_cfg.tags)
    ))
    tool = world.add(Entity(id="sponge", kind="thing", type="thing", label="sponge", phrase="a soft sponge"))
    note = world.add(Entity(id="surprise", kind="thing", type="thing", label=surprise_cfg.label, phrase=surprise_cfg.phrase))

    world.facts.update(hero=hero, friend=friend, parent=parent, item=item, tool=tool, note=note,
                       place=place, job=job, target_id=item.id, zone=sorted(job.zone))

    hero.memes["hurt"] += 1
    friend.memes["guilt"] += 1
    parent.memes["worry"] += 1
    item.meters["dirty"] += 1

    world.say(f"{hero.id} was a little {hero.type} who liked to keep things neat.")
    world.say(f"{friend.id} came by, and together they were planning to {job.verb}.")
    world.say(f"{setup_sentence(place, job)}")
    world.say(f"Then an accident made {item.label} {job.stain}, and {hero.id} frowned.")

    world.para()
    world.say(f"{friend.id} took a breath and said sorry.")
    hero.memes["forgive"] += 1
    friend.memes["apology"] += 1
    friend.memes["sadness"] += 1
    world.say(f"{hero.id} listened, and {hero.id}'s {parent.label_word} brought out {tool.phrase} so they could scrub.")

    world.para()
    if predict_cleanup(world, hero, item.id):
        _scrub(world, hero, item)
    else:
        world.say("They scrubbed carefully, but the stain did not lift right away.")
    world.say(f"Just then, {note.phrase} was found tucked under the mat.")
    world.say(f"It was a small surprise, and it made the room feel softer again.")
    if friend.id:
        friend.memes["forgive"] += 1
        hero.memes["forgive"] += 1
    propagate(world, narrate=True)
    if friend.memes["warmth"] >= THRESHOLD:
        world.say(f"{hero.id} and {friend.id} smiled at each other again, and the day felt okay.")
    else:
        world.say(f"{hero.id} and {friend.id} were still working it out, but the apology had started it.")

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "porch": Place(id="porch", label="the porch", indoors=False, affords={"scrub"}, tags={"porch"}),
    "kitchen": Place(id="kitchen", label="the kitchen", indoors=True, affords={"scrub"}, tags={"kitchen"}),
    "garden": Place(id="garden", label="the garden path", indoors=False, affords={"scrub"}, tags={"garden"}),
}

JOBS = {
    "scrub_bench": Job(id="scrub_bench", verb="scrub the bench", noun="bench", mess="scrub", stain="a little muddy", zone={"hands", "legs"}, keyword="scrub", tags={"scrub", "clean"}),
    "scrub_steps": Job(id="scrub_steps", verb="scrub the steps", noun="steps", mess="scrub", stain="dull and dusty", zone={"hands", "feet"}, keyword="scrub", tags={"scrub", "clean"}),
    "scrub_table": Job(id="scrub_table", verb="scrub the table", noun="table", mess="scrub", stain="sticky with juice", zone={"hands", "torso"}, keyword="scrub", tags={"scrub", "clean"}),
}

ITEMS = {
    "bench": Item(id="bench", label="bench", phrase="a little wooden bench", region="hands", plural=False, tags={"bench", "dirty"}),
    "steps": Item(id="steps", label="steps", phrase="the stone steps", region="feet", plural=True, tags={"steps", "dirty"}),
    "table": Item(id="table", label="table", phrase="the picnic table", region="torso", plural=False, tags={"table", "dirty"}),
}

SURPRISES = {
    "cookie_note": Surprise(id="cookie_note", label="note", phrase="a note with a cookie sketch", tags={"note", "surprise"}),
    "flower": Surprise(id="flower", label="flower", phrase="a small flower in a cup", tags={"flower", "surprise"}),
    "sticker": Surprise(id="sticker", label="sticker", phrase="a bright sticker on the fridge", tags={"sticker", "surprise"}),
}

GIRL_NAMES = ["Maya", "Nora", "Lily", "Ava", "Zoe", "Mia", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Noah", "Eli", "Max"]


@dataclass
class StoryParams:
    place: str
    job: str
    item: str
    surprise: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    parent_type: str = "mother"
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="porch", job="scrub_bench", item="bench", surprise="cookie_note", hero="Maya", hero_type="girl", friend="Nora", friend_type="girl", parent_type="mother"),
    StoryParams(place="kitchen", job="scrub_table", item="table", surprise="flower", hero="Leo", hero_type="boy", friend="Ben", friend_type="boy", parent_type="father"),
    StoryParams(place="garden", job="scrub_steps", item="steps", surprise="sticker", hero="Ava", hero_type="girl", friend="Eli", friend_type="boy", parent_type="mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for job_id, job in JOBS.items():
            if job.mess != "scrub" or "scrub" not in SETTINGS[place].affords:
                continue
            for item_id, item in ITEMS.items():
                if item.region in job.zone:
                    out.append((place, job_id, item_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item"]
    job = f["job"]
    surprise = f["note"]
    return [
        f'Write a slice-of-life story for a young child that includes the word "scrub" and a small surprise after {hero.id} and {friend.id} make a mess with {item.label}.',
        f"Tell a gentle story where {hero.id} and {friend.id} have to scrub {item.label}, say sorry, and find a surprise {surprise.label} at the end.",
        f'Write a simple reconciliation story in which a child learns a moral value from scrubbing {item.label} and seeing {surprise.phrase}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    parent: Entity = f["parent"]
    item: Entity = f["item"]
    job: Job = f["job"]
    note: Entity = f["note"]
    place: Place = f["place"]
    qa = [
        QAItem(
            question=f"Who were the story children in {place.label}?",
            answer=f"It was about {hero.id} and {friend.id}. They were trying to {job.verb}, and {hero.id}'s {parent.label_word} stayed nearby to help.",
        ),
        QAItem(
            question=f"What had to be scrubbed after the accident?",
            answer=f"{item.label.capitalize()} had to be scrubbed because it got {job.stain}. {hero.id} used a sponge, and the cleanup made the mess fade.",
        ),
        QAItem(
            question=f"Why did {friend.id} say sorry to {hero.id}?",
            answer=f"{friend.id} said sorry because the accident hurt {hero.id}'s feelings and left {item.label} messy. The apology helped them start over instead of staying cross.",
        ),
    ]
    if item.meters["clean"] >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did the scrubbing help {item.label}?",
            answer=f"The scrubbing made {item.label} look brighter again. It was a careful fix, and the clean spot showed that work can repair a little mistake.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What surprise did they find after they scrubbed?",
            answer=f"They found {note.phrase}. It was a small surprise, and it made the afternoon feel kinder after the apology.",
        ))
        qa.append(QAItem(
            question=f"What moral value does the story show?",
            answer=f"It shows that owning a mistake, apologizing, and helping clean up can bring people back together. The story ends with reconciliation instead of hurt feelings.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does scrub mean?",
            answer="To scrub means to rub something hard with water or soap so dirt can come off. People scrub when they want to clean a spot or a surface.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again. It can happen after someone says sorry and the other person is ready to forgive.",
        ),
        QAItem(
            question="Why can a surprise make a day feel better?",
            answer="A surprise can make a day feel lighter because it gives people something new and pleasant to notice. A small kind surprise can help the mood change after a hard moment.",
        ),
        QAItem(
            question="What is a moral value in a story?",
            answer="A moral value is a good lesson about how to act, like telling the truth, being kind, or helping fix a mistake. It gives the story a gentle point to remember.",
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
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def ASP_RULES() -> str:
    return r"""
valid(Place, Job, Item) :- place(Place), job(Job), item(Item), afford(Place, scrub), job_zone(Job, Z), item_region(Item, Z).
reconcile(Event) :- apology(Event), forgive(Event).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("afford", pid, a))
    for jid, j in JOBS.items():
        lines.append(asp.fact("job", jid))
        lines.append(asp.fact("job_zone", jid, sorted(j.zone)[0]))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_region", iid, it.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES()}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos()")
        return 1
    sample = generate(resolve_params(argparse.Namespace(place=None, job=None, item=None, surprise=None, hero=None, hero_type=None, friend=None, friend_type=None, parent_type=None), random.Random(777)))
    if not sample.story or "scrub" not in sample.story:
        print("SMOKE TEST FAILED")
        return 1
    print("OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life scrub storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
              if args.place is None or c[0] == args.place
              and (args.job is None or c[1] == args.job)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, job, item = rng.choice(sorted(combos))
    surprise = args.surprise or rng.choice(sorted(SURPRISES))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or ("boy" if hero_type == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_type == "girl" else BOY_NAMES) if n != hero])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    return StoryParams(place=place, job=job, item=item, surprise=surprise, hero=hero, hero_type=hero_type, friend=friend, friend_type=friend_type, parent_type=parent_type)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    job = JOBS[params.job]
    item = ITEMS[params.item]
    surprise = SURPRISES[params.surprise]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, role="parent", label="the parent"))
    target = world.add(Entity(id="target", kind="thing", type="thing", label=item.label, phrase=item.phrase, plural=item.plural, owner=hero.id, caretaker=parent.id, tags=set(item.tags)))
    sponge = world.add(Entity(id="sponge", kind="thing", type="thing", label="sponge", phrase="a soft sponge"))
    note = world.add(Entity(id="note", kind="thing", type="thing", label=surprise.label, phrase=surprise.phrase))
    world.facts.update(hero=hero, friend=friend, parent=parent, item=target, job=job, place=place, note=note, sponge=sponge, target_id=target.id, zone=sorted(job.zone))
    hero.meters["scrubbing"] += 1
    friend.memes["apology"] += 1
    friend.memes["forgive"] += 1
    target.meters["dirty"] += 1

    world.say(f"{hero.id} and {friend.id} had a small disagreement, but they stayed together.")
    world.say(f"They wanted to {job.verb}, and {place.label} felt calm around them.")
    world.say(f"An accident left {item.label} {job.stain}, so {hero.id} frowned and {friend.id} looked sorry.")
    world.para()
    world.say(f"{friend.id} said sorry, and {hero.id}'s {parent.label_word} handed over {sponge.phrase}.")
    if predict_cleanup(world, hero, target.id):
        world.say(f"{hero.id} began to scrub, and {item.label} slowly looked better.")
        target.meters["clean"] += 1
    else:
        world.say(f"{hero.id} tried to scrub, but the mess needed more time.")
    world.para()
    world.say(f"Then a surprise appeared: {note.phrase}.")
    world.say("That little surprise made the whole moment softer, and the apology felt real.")
    friend.memes["warmth"] += 1
    hero.memes["warmth"] += 1
    world.say(f"By the end, {hero.id} and {friend.id} were smiling again, because a mistake can be fixed.")
    world.facts["resolved"] = True
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/3."))
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
