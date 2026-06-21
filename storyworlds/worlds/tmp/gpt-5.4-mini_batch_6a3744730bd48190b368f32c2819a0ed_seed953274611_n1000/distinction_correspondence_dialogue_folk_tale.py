#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distinction_correspondence_dialogue_folk_tale.py
===============================================================================

A standalone folk-tale storyworld about a village child learning to make a
careful distinction and a matching correspondence. The world is small and
simulated: a lost token, two nearly alike objects, a wise elder, a helping animal,
and a choice that turns on listening, noticing, and speaking.

Seed words:
- distinction
- correspondence

Features:
- Dialogue
- Folk tale style
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "elder"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class StoryParams:
    setting: str
    task: str
    key: str
    decoy: str
    helper: str
    elder: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    scene: str
    opening: str
    home: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    ask: str
    need: str
    distinction: str
    correspondence: str
    trial: str
    success: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Key:
    id: str
    label: str
    phrase: str
    fits: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Decoy:
    id: str
    label: str
    phrase: str
    does_not_fit: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    words: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Elders:
    id: str
    label: str
    lesson: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["solved"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["relief"] += 1
        out.append("__relief__")
    return out


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


CAUSAL_RULES = [Rule("relief", _r_relief)]


def clever_question(world: World, child: Entity, task: Task, decoy: Decoy) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On the edge of the village, {child.id} looked at the two things and said, "
        f'"How can I know which one is the right one?"'
    )
    world.say(
        f"The old road, the home, and the river all lay in one quiet row, as if the land itself was listening."
    )
    world.say(
        f"Then {child.id} picked up the first and the second in turn, as careful as a fox counting moonbeams."
    )


def elder_speaks(world: World, elder: Entity, child: Entity, task: Task, key: Key, decoy: Decoy) -> None:
    elder.memes["calm"] += 1
    world.say(
        f'"Child," said {elder.id}, "there is a distinction between what looks alike and what truly belongs."'
    )
    world.say(
        f'"Look for correspondence," {elder.id} said. "{key.label} corresponds to the {task.need}, '
        f"but {decoy.label} does not.""
    )


def try_decoy(world: World, child: Entity, decoy: Decoy, task: Task) -> None:
    child.memes["worry"] += 1
    world.say(
        f'"Perhaps this one?" {child.id} whispered, holding up {decoy.phrase}. '
        f'"It shines like the proper thing."'
    )
    world.say(f'"No," said the elder. "{decoy.does_not_fit}."')


def succeed(world: World, child: Entity, helper: Entity, key: Key, task: Task) -> None:
    child.meters["solved"] += 1
    helper.memes["pleased"] += 1
    world.say(
        f'"Ah!" cried {child.id}. "{key.label} is the one that fits!"'
    )
    world.say(
        f'{helper.id} nodded and said, "{task.success}." '
        f"At once, the little lock opened, and the path to the cottage was clear."
    )
    world.say(
        f"{child.id} tucked the right {key.label_word if hasattr(key, 'label_word') else key.label} into {child.id}'s palm and laughed."
    )


def lesson(world: World, elder: Entity, child: Entity, task: Task, key: Key, helper: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'"Remember," said {elder.id}, "a wise heart makes a distinction before it chooses."'
    )
    world.say(
        f'"And when the thing and the need correspond, the right door opens."'
    )
    world.say(
        f'{child.id} smiled. "{task.need} for the key, and the key for the {task.need}," {child.id} said. '
        f'"I see it now."'
    )


def tell(setting: Setting, task: Task, key: Key, decoy: Decoy, helper: Helper, elder: Elders,
         child_name: str = "Mira", child_gender: str = "girl") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    old = world.add(Entity(id=elder.id, kind="character", type="woman", role="elder", label=elder.label))
    fox = world.add(Entity(id=helper.id, kind="character", type="fox", role="helper", label=helper.label))

    child.memes["hope"] += 1

    world.say(
        f"{child.id} lived where the {setting.scene}. {setting.opening}"
    )
    world.say(
        f'"{task.ask}," asked {child.id}.'
    )

    world.para()
    clever_question(world, child, task, decoy)
    elder_speaks(world, old, child, task, key, decoy)

    world.para()
    try_decoy(world, child, decoy, task)
    world.say(
        f'"Then what makes the right one different?" asked {child.id}.'
    )
    world.say(
        f'"Its shape answers the need," said {helper.id}, "and its use corresponds to the problem."'
    )

    world.para()
    succeed(world, child, fox, key, task)
    lesson(world, old, child, task, key, fox)

    world.facts.update(
        child=child,
        elder=old,
        helper=fox,
        task=task,
        key=key,
        decoy=decoy,
        setting=setting,
        outcome="solved",
    )
    return world


SETTINGS = {
    "brook": Setting(
        id="brook",
        scene="a brook wound past the willow trees and the mossy stones",
        opening="The mist was soft, and the birds kept a low, sleepy song.",
        home="the cottage",
        path="the river path",
        tags={"folk", "river"},
    ),
    "hill": Setting(
        id="hill",
        scene="a hill watched over the village and the bread ovens",
        opening="The wind smelled of warm loaf and rain.",
        home="the cottage",
        path="the hill path",
        tags={"folk", "hill"},
    ),
    "orchard": Setting(
        id="orchard",
        scene="an orchard slept under old apple trees and bright ropes of dew",
        opening="The apples shone like little red lanterns in the morning.",
        home="the cottage",
        path="the orchard path",
        tags={"folk", "orchard"},
    ),
}

TASKS = {
    "door": Task(
        id="door",
        ask="Which key opens the cottage door?",
        need="door",
        distinction="The right key is not the shiny one",
        correspondence="the key corresponds to the door's shape",
        trial="a lock",
        success="This key matches the lock like a song matches its tune",
        fail="that key only turns and slips, like a spoon in porridge",
        tags={"key", "door"},
    ),
    "gate": Task(
        id="gate",
        ask="Which key opens the garden gate?",
        need="gate",
        distinction="The gate key has a narrow tooth",
        correspondence="the key corresponds to the gate's narrow mouth",
        trial="a gate lock",
        success="This key fits the gate because it was made for it",
        fail="that key is too broad and kind, and the gate will not take it",
        tags={"key", "gate"},
    ),
    "chest": Task(
        id="chest",
        ask="Which key opens the little chest?",
        need="chest",
        distinction="The chest key is the smallest of the two",
        correspondence="the key corresponds to the chest's tiny latch",
        trial="a chest lock",
        success="This key belongs to the chest and turns it gently open",
        fail="that key is for a bigger thing and will not wake the chest",
        tags={"key", "chest"},
    ),
}

KEYS = {
    "silver": Key(id="silver", label="silver key", phrase="a silver key", fits="door", tags={"metal", "key"}),
    "iron": Key(id="iron", label="iron key", phrase="an iron key", fits="gate", tags={"metal", "key"}),
    "brass": Key(id="brass", label="brass key", phrase="a brass key", fits="chest", tags={"metal", "key"}),
}

DECOYS = {
    "spoon": Decoy(id="spoon", label="shining spoon", phrase="a shining spoon", does_not_fit="That spoon is bright, but it will not turn the lock", tags={"tool"}),
    "feather": Decoy(id="feather", label="white feather", phrase="a white feather", does_not_fit="A feather is light as a cloud, but it opens no door", tags={"tool"}),
    "ring": Decoy(id="ring", label="copper ring", phrase="a copper ring", does_not_fit="The ring is round, but it has no tooth for the lock", tags={"tool"}),
}

HELPERS = {
    "fox": Helper(id="Fox", label="fox", words="clever words", gift="a matching clue", tags={"animal"}),
    "goat": Helper(id="Goat", label="goat", words="patient words", gift="a matching clue", tags={"animal"}),
    "heron": Helper(id="Heron", label="heron", words="quiet words", gift="a matching clue", tags={"animal"}),
}

ELDERS = {
    "grandmother": Elders(id="Grandmother", label="Grandmother", lesson="wisdom came first", tags={"elder"}),
    "aunt": Elders(id="Auntie", label="Auntie", lesson="wisdom came first", tags={"elder"}),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Nora", "Sila", "Tara", "Esme", "Mina"]
BOY_NAMES = ["Oren", "Bram", "Pavel", "Jon", "Tomas", "Eli", "Kian", "Bela"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for k in KEYS:
                if KEYS[k].fits == t:
                    combos.append((s, t, k))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about distinction and correspondence.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--key", choices=KEYS)
    ap.add_argument("--decoy", choices=DECOYS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)
              and (args.key is None or c[2] == args.key)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, key = rng.choice(sorted(combos))
    task_obj = TASKS[task]
    decoy = args.decoy or rng.choice(sorted(d for d in DECOYS if d != key))
    helper = args.helper or rng.choice(sorted(HELPERS))
    elder = args.elder or rng.choice(sorted(ELDERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, task=task, key=key, decoy=decoy, helper=helper, elder=elder, child_name=name, child_gender=gender)


def _story_eligible(params: StoryParams) -> bool:
    return KEYS[params.key].fits == params.task


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.task not in TASKS or params.key not in KEYS:
        raise StoryError("Invalid params.")
    if params.decoy not in DECOYS or params.helper not in HELPERS or params.elder not in ELDERS:
        raise StoryError("Invalid params.")
    if not _story_eligible(params):
        raise StoryError("Those choices do not correspond well enough for a folk tale.")

    world = tell(SETTINGS[params.setting], TASKS[params.task], KEYS[params.key],
                 DECOYS[params.decoy], HELPERS[params.helper], ELDERS[params.elder],
                 child_name=params.child_name, child_gender=params.child_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    return [
        f'Write a folk tale for a young child that uses the words "distinction" and "correspondence" and includes dialogue.',
        f'Tell a gentle village story where {child.id} learns to tell apart two similar things and discover which one corresponds to {task.need}.',
        f'Write a story in which an elder says the word "distinction" and a helper says the word "correspondence" before the right object is chosen.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    task = f["task"]
    key = f["key"]
    decoy = f["decoy"]
    elder = f["elder"]
    helper = f["helper"]
    return [
        ("What kind of story is this?",
         f"It is a small folk tale about {child.id} learning to notice what truly belongs. The turning point comes from making a careful distinction and seeing correspondence."),
        (f"What did {child.id} have to figure out?",
         f"{child.id} had to figure out which thing matched the {task.need}. The other thing looked similar, but it did not correspond to the lock."),
        (f"What did {elder.id} tell {child.id}?",
         f"{elder.id} said there was a distinction between what looked alike and what truly belonged. {elder.id} also told {child.id} to look for correspondence before choosing."),
        (f"Why was {decoy.label} not the right choice?",
         f"{decoy.does_not_fit}. It looked shiny, but the story shows that appearance alone was not enough."),
        (f"How did the story end?",
         f"{child.id} chose the {key.label} and the way forward opened. The village felt a little brighter because the right thing and the right need finally met."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a distinction?",
         "A distinction is a way of telling one thing from another when they look or seem alike."),
        ("What is correspondence?",
         "Correspondence is a matching relationship, when one thing fits or belongs with another."),
        ("Why do folk tales often use dialogue?",
         "Dialogue lets the characters speak their wisdom aloud, so the lesson feels lively and easy to remember."),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
chosen_setting(S) :- setting(S).
chosen_task(T) :- task(T).
chosen_key(K) :- key(K), fits(K,T), chosen_task(T).
distinction :- chosen_task(T).
correspondence :- chosen_key(K), chosen_task(T), fits(K,T).
valid(S,T,K) :- setting(S), task(T), key(K), fits(K,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for k, obj in KEYS.items():
        lines.append(asp.fact("key", k))
        lines.append(asp.fact("fits", k, obj.fits))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.\n") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: clingo gate differs from valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, task=None, key=None, decoy=None, helper=None, elder=None, name=None, gender=None), random.Random(7)))
        _ = sample.story
        _ = sample.to_json()
        print("OK: generate() and serialization smoke test passed.")
    except Exception as e:
        print(f"FAIL: generate() smoke test crashed: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="brook", task="door", key="silver", decoy="spoon", helper="fox", elder="grandmother", child_name="Mira", child_gender="girl"),
    StoryParams(setting="hill", task="gate", key="iron", decoy="ring", helper="goat", elder="aunt", child_name="Oren", child_gender="boy"),
    StoryParams(setting="orchard", task="chest", key="brass", decoy="feather", helper="heron", elder="grandmother", child_name="Lina", child_gender="girl"),
]


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories:")
        for t in asp_valid_combos():
            print(" ", t)
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
