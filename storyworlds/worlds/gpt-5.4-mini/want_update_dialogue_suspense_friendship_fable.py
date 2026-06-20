#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/want_update_dialogue_suspense_friendship_fable.py
==================================================================================

A small standalone storyworld for a fable-like tale about wanting news, waiting
for an update, friendship, and a suspenseful turn resolved by honest dialogue.

The world is intentionally tiny: two friends, one messenger, one task, and a
single update that can arrive on time, arrive late, or arrive with a surprise.
The simulated state drives the story text, Q&A, trace, and ASP parity checks.
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

NAMES = ["Mina", "Tavi", "Lina", "Niko", "Pia", "Rafi", "Suri", "Oren"]
FRIEND_NAMES = ["Ari", "Bea", "Cleo", "Dara", "Eli", "Faye", "Gus", "Hana"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wait": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    place: str
    mood: str
    waiting_spot: str
    messenger_route: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Task:
    id: str
    want_text: str
    update_text: str
    suspense_text: str
    reveal_text: str
    risk: int
    helpful: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Outcome:
    id: str
    delay: int
    surprised: bool
    success: bool

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    setting: str
    task: str
    delay: int
    reveal_kind: str
    hero: str
    friend: str
    messenger: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


SETTINGS = {
    "market": Setting("the market square", "busy", "the fountain", "the stone lane"),
    "garden": Setting("the old garden", "quiet", "the lilac bench", "the ivy path"),
    "harbor": Setting("the little harbor", "windy", "the dock post", "the wooden pier"),
}

TASKS = {
    "lost_bird": Task(
        "lost_bird",
        "want to find the lost bird",
        "the bird is safe and near the chapel",
        "they waited and worried as the sky darkened",
        "the bird had flown home on its own",
        risk=2,
        helpful=True,
    ),
    "broken_gate": Task(
        "broken_gate",
        "want to fix the broken gate",
        "the gate needs a new pin from the smith",
        "the latch still hung crooked, and the road felt lonely",
        "the smith had already sent the pin",
        risk=3,
        helpful=True,
    ),
    "rain_note": Task(
        "rain_note",
        "want to carry the rain note",
        "the rain note says to wait under cover",
        "the clouds gathered and the path grew dim",
        "the note was only a reminder, not bad news",
        risk=2,
        helpful=True,
    ),
}

REVEALS = {
    "simple": "The update was simple and kind.",
    "surprise": "The update carried a small surprise.",
    "late": "The update came late, after a long wait.",
}

MORALS = {
    "simple": "Friends are strongest when they tell the truth early.",
    "surprise": "A calm answer can turn worry into wonder.",
    "late": "Patience is easier when friendship keeps you company.",
}


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_wait(world: World) -> list[str]:
    out: list[str] = []
    task = world.get("task")
    if task.meters["waiting"] < THRESHOLD:
        return out
    sig = ("wait",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        world.get(eid).memes["hope"] += 1
        world.get(eid).memes["fear"] += 1
    out.append("__wait__")
    return out


def _r_truth(world: World) -> list[str]:
    out: list[str] = []
    msg = world.get("message")
    if msg.meters["arrived"] < THRESHOLD:
        return out
    sig = ("truth",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["trust"] += 1
    world.get("friend").memes["trust"] += 1
    out.append("__truth__")
    return out


CAUSAL_RULES = [Rule("wait", _r_wait), Rule("truth", _r_truth)]


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


def tell(setting: Setting, task: Task, reveal_kind: str, delay: int,
         hero: str, friend: str, messenger: str) -> World:
    world = World(setting)
    h = world.add(Entity(hero, kind="character", type="child", role="hero"))
    f = world.add(Entity(friend, kind="character", type="child", role="friend"))
    m = world.add(Entity(messenger, kind="character", type="adult", role="messenger"))
    task_ent = world.add(Entity("task", type="task", label=task.id))
    msg = world.add(Entity("message", type="message", label="the update"))
    outcome = Outcome(reveal_kind, delay, reveal_kind == "surprise", True)

    h.memes["want"] = 1.0
    f.memes["want"] = 1.0
    h.memes["trust"] = 1.0
    f.memes["trust"] = 1.0

    world.say(
        f"In {setting.place}, {hero} and {friend} were good friends who liked to "
        f"solve small troubles together."
    )
    world.say(
        f"They sat by {setting.waiting_spot} and said they would {task.want_text}."
    )
    world.say(
        f'"We want an update," {friend} said. "{hero}, do you think it will come soon?"'
    )
    world.say(
        f'"I hope so," {hero} said, peering down {setting.messenger_route} '
        f"while the wind moved the leaves."
    )

    world.para()
    task_ent.meters["waiting"] += 1
    h.memes["hope"] += 1
    f.memes["hope"] += 1
    world.say(
        f"They kept listening for footsteps. {task.suspense_text}."
    )
    propagate(world, narrate=False)

    if delay > 0:
        world.say(
            f'"Maybe the messenger took the long way," {friend} whispered. '
            f'"Maybe we should just wait."'
        )
        task_ent.meters["waiting"] += delay

    world.para()
    msg.meters["arrived"] += 1
    world.say(
        f"At last, {messenger} came along the path and held up a note."
    )
    if reveal_kind == "simple":
        world.say(f'"Here is the update," {messenger} said. "It says that {task.update_text}."')
    elif reveal_kind == "surprise":
        world.say(f'"Here is the update," {messenger} said, smiling. "It says that {task.update_text}."')
        world.say(f"{hero} and {friend} blinked, because the news was smaller and kinder than they feared.")
    else:
        world.say(f'"Here is the update," {messenger} said at last. "It says that {task.update_text}."')

    world.para()
    if reveal_kind == "simple":
        world.say(
            f"{hero} and {friend} looked at one another and laughed softly. "
            f"They had worried for nothing."
        )
    elif reveal_kind == "surprise":
        world.say(
            f"{hero} and {friend} listened carefully, then smiled as the surprise "
            f"turned into a good plan."
        )
    else:
        world.say(
            f"{hero} and {friend} let out a long breath together. The wait had been "
            f"hard, but friendship made it bearable."
        )
    world.say(f"The moral was plain: {MORALS[reveal_kind]}")

    world.facts.update(
        hero=h, friend=f, messenger=m, task=task, task_ent=task_ent, message=msg,
        setting=setting, reveal_kind=reveal_kind, outcome=outcome, delay=delay
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for r in REVEALS:
                combos.append((s, t, r))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-style story for a child that includes the words "want" and "update".',
        f"Tell a friendship story in dialogue where {f['hero'].id} and {f['friend'].id} want an update and must wait for it.",
        f"Write a suspenseful, gentle fable about friends who hear news at {f['setting'].place} and learn a moral.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    h, fr, task = f["hero"], f["friend"], f["task"]
    qa = [
        ("Who is the story about?",
         f"It is about {h.id} and {fr.id}, two friends who stayed together while they waited for news."),
        ("What did they want?",
         f"They wanted an update about how to {task.want_text}. They did not want to guess; they wanted to hear the truth."),
        ("Why was the middle of the story suspenseful?",
         f"They had to wait in the wind and listen for footsteps. The waiting made them worry until the messenger arrived."),
    ]
    if f["reveal_kind"] == "surprise":
        qa.append((
            "How did the friends react to the update?",
            f"They were surprised, but they stayed calm and listened. The surprise turned into a better plan because they trusted one another."
        ))
    elif f["reveal_kind"] == "late":
        qa.append((
            "How did the friends handle the delay?",
            f"They kept each other company and waited patiently. The friendship helped them through the long delay."
        ))
    else:
        qa.append((
            "How did the friends feel at the end?",
            f"They felt relieved and happy. The update answered their worry and let them breathe again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    out = []
    for topic, qa in [
        ("want", [("What does it mean to want something?",
                  "To want something means to wish for it or hope to have it.")]),
        ("update", [("What is an update?",
                     "An update is new information that tells you what is happening now.")]),
        ("friendship", [("What is friendship?",
                        "Friendship is when people care about each other, help each other, and stay kind.")]),
        ("suspense", [("What is suspense?",
                      "Suspense is the feeling of waiting and wondering what will happen next.")]),
        ("dialogue", [("What is dialogue in a story?",
                     "Dialogue is when characters speak to each other using words in quotation marks.")]),
        ("fable", [("What is a fable?",
                   "A fable is a short story that often uses animals or people to teach a lesson.")]),
    ]:
        if topic in {"want", "update", "friendship", "suspense", "dialogue", "fable"}:
            out.extend(qa)
    return out


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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("market", "lost_bird", 0, "simple", "Mina", "Ari", "Nora"),
    StoryParams("garden", "broken_gate", 1, "late", "Tavi", "Bea", "Ilan"),
    StoryParams("harbor", "rain_note", 0, "surprise", "Lina", "Eli", "Mara"),
]


def explain_rejection() -> str:
    return "(No story: the seed world is too loose; use one of the valid settings, tasks, and reveals.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable-like story world about want, update, dialogue, suspense, and friendship."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
    ap.add_argument("--messenger")
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
              and (args.reveal is None or c[2] == args.reveal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task, reveal = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != hero])
    messenger = args.messenger or rng.choice(["the crow", "the aunt", "the baker", "the owl"])
    return StoryParams(setting, task, 0 if reveal == "simple" else rng.randint(0, 2), reveal, hero, friend, messenger)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], TASKS[params.task], params.reveal,
                 params.delay, params.hero, params.friend, params.messenger)
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


ASP_RULES = r"""
valid(S,T,R) :- setting(S), task(T), reveal(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for rid in REVEALS:
        lines.append(asp.fact("reveal", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero} & {p.friend}: {p.task} in {p.setting} ({p.reveal})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
