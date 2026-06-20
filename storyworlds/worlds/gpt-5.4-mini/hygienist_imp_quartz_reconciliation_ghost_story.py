#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hygienist_imp_quartz_reconciliation_ghost_story.py
==================================================================================

A standalone storyworld in a small ghost-story domain: a night hygienist meets
a mischievous imp, a quartz object that keeps making eerie sounds, and the two
find reconciliation instead of a haunting that stays angry.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- forward-chained causal rules
- a reasonableness gate plus inline ASP twin
- grounded prompts and Q&A generated from simulated state
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    spectral: bool = False
    dusty: bool = False
    gleams: bool = False
    haunted: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hygienist"}
        male = {"boy", "father", "dad", "man", "imp"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



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
    mood: str
    echo: str
    hiding_spot: str

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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    sound: str
    cold: bool = False
    gleams: bool = False
    haunted: bool = False
    tags: set[str] = field(default_factory=set)

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
class Action:
    id: str
    approach: str
    cleanup: str
    soothe: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)

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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.focus: str = ""

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.focus = self.focus
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_haunt(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if not e.haunted or e.meters["dust"] < THRESHOLD:
            continue
        sig = ("haunt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["cold"] += 1
        e.memes["unease"] += 1
        out.append("__haunt__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    hygienist = world.entities.get("hygienist")
    imp = world.entities.get("imp")
    quartz = world.entities.get("quartz")
    if not hygienist or not imp or not quartz:
        return out
    if hygienist.memes["kindness"] < THRESHOLD:
        return out
    if imp.memes["shame"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hygienist.memes["peace"] += 1
    imp.memes["peace"] += 1
    quartz.memes["peace"] += 1
    quartz.meters["dust"] = 0.0
    quartz.haunted = False
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("haunt", "physical", _r_haunt),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(obj: ObjectCfg, action: Action) -> bool:
    return action.sense >= SENSE_MIN and (obj.gleams or obj.haunted)


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for oid, obj in OBJECTS.items():
        for aid, act in ACTIONS.items():
            if reasonableness_gate(obj, act):
                out.append((oid, aid))
    return out


def predict(world: World) -> dict:
    sim = world.copy()
    run_cycle(sim, narrate=False)
    q = sim.get("quartz")
    return {"reconciled": not q.haunted, "dust": q.meters["dust"], "peace": q.memes["peace"]}


def run_cycle(world: World, narrate: bool = True) -> None:
    propagate(world, narrate=narrate)


def setup_story(world: World, setting: Setting, obj: ObjectCfg, action: Action) -> None:
    hyg = world.add(Entity(id="hygienist", kind="character", type="hygienist", label="the hygienist", role="keeper"))
    imp = world.add(Entity(id="imp", kind="character", type="imp", label="the imp", role="mischief"))
    quartz = world.add(Entity(id="quartz", kind="thing", type="thing", label="the quartz", spectral=True, dusty=obj.haunted, gleams=obj.gleams, haunted=obj.haunted))
    world.focus = obj.id
    hyg.memes["kindness"] = 2.0
    imp.memes["trouble"] = 2.0
    imp.memes["shame"] = 0.0
    quartz.meters["dust"] = 1.0 if obj.haunted else 0.0
    if obj.cold:
        quartz.meters["cold"] = 1.0
    world.facts.update(setting=setting, object=obj, action=action, hygienist=hyg, imp=imp, quartz=quartz)


def tell(setting: Setting, obj: ObjectCfg, action: Action) -> World:
    world = World()
    setup_story(world, setting, obj, action)
    hyg = world.get("hygienist")
    imp = world.get("imp")
    quartz = world.get("quartz")

    world.say(f"At {setting.place}, where {setting.echo} lingered in the air, the hygienist stepped softly past {setting.hiding_spot}.")
    world.say(f"On the shelf sat {obj.phrase}, and when it made its {obj.sound}, the imp grinned from the shadows.")

    world.para()
    world.say(f'The imp whispered, "I can hide the noise if I pull at it," but the hygienist shook {hyg.pronoun("possessive")} head.')
    world.say(f'"No," {hyg.id} said gently. "{action.approach} is better than a trick."')
    pred = predict(world)
    world.facts["predicted"] = pred
    if pred["reconciled"]:
        imp.memes["shame"] += 1
        world.say(f"The imp looked down at the dusty quartz and suddenly felt small.")
    else:
        world.say(f"The air stayed prickly, as if the room still wanted a quarrel.")

    world.para()
    world.say(f"The hygienist took a cloth, a bowl of warm water, and a calm voice.")
    world.say(f"{hyg.id} wiped the quartz clean, then set it in the light.")
    quartz.meters["dust"] = 0.0
    quartz.meters["polished"] += 1
    quartz.gleams = True
    imp.memes["shame"] += 1
    run_cycle(world, narrate=False)
    if quartz.memes["peace"] < THRESHOLD:
        quartz.memes["peace"] += 1
    world.say(f"The little stone answered with a clear, bright glimmer instead of a spooky rattle.")
    world.say(f"The imp crept closer, and this time {imp.pronoun()} did not grin; {imp.pronoun()} watched and waited.")

    world.para()
    if quartz.haunted:
        world.say(f'The imp said, "I am sorry for making you uneasy."')
        world.say(f'{hyg.id} nodded. "And I am sorry I came in like a storm. Let us start again."')
        quartz.haunted = False
        quartz.memes["peace"] += 1
        imp.memes["peace"] += 1
        hyg.memes["peace"] += 1
    else:
        hyg.memes["peace"] += 1
        imp.memes["peace"] += 1
        quartz.memes["peace"] += 1
        world.say(f'The imp said, "I did not mean to scare anyone."')
        world.say(f'{hyg.id} smiled. "Thank you for telling the truth. We can mend the mood together."')
    world.say(f"By the end, the quartz was clean, the imp was quiet, and the old room felt less like a haunting and more like a home.")

    world.facts["outcome"] = "reconciled" if not quartz.haunted else "unsettled"
    return world


SETTINGS = {
    "attic": Setting("attic", "the attic", "old boards creaked", "a cracked beam", "a narrow trunk"),
    "church": Setting("church", "the little church", "soft bells echoed", "a candle niche", "the side aisle"),
    "museum": Setting("museum", "the museum", "footsteps whispered", "a glass case", "a velvet rope"),
}

OBJECTS = {
    "quartz": ObjectCfg("quartz", "quartz", "a pale quartz stone", "tiny knocking sound", cold=True, gleams=False, haunted=True, tags={"quartz", "ghost"}),
    "mirror": ObjectCfg("mirror", "mirror", "an old mirror", "thin sigh", cold=True, gleams=False, haunted=True, tags={"mirror", "ghost"}),
    "bell": ObjectCfg("bell", "bell", "a small bell", "trembling ring", cold=False, gleams=True, haunted=False, tags={"bell"}),
}

ACTIONS = {
    "cleanse": Action("cleanse", "clean the quartz with warm water", "wiped it clean", "made it feel calm", 3, 3, tags={"clean"}),
    "dust": Action("dust", "dust the shelf and polish the stone", "polished it carefully", "gave it a softer shine", 2, 2, tags={"clean"}),
    "listen": Action("listen", "listen until the room went quiet", "waited in silence", "turned fear into calm", 2, 2, tags={"listen"}),
}

SETTINGS_ORDER = ["attic", "church", "museum"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    object: str
    action: str
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


GHOST_KNOWLEDGE = {
    "ghost": [("What is a ghost story?",
               "A ghost story is a tale that feels spooky, with shadows, whispers, or strange noises, but it can still end safely.")],
    "quartz": [("What is quartz?",
                "Quartz is a hard rock that can look shiny or pale. People sometimes keep it as a little treasure or decoration.")],
    "clean": [("Why do people clean dusty things?",
               "Cleaning dust off things can make them look brighter and help them feel cared for.")],
    "peace": [("What does reconciliation mean?",
               "Reconciliation means making peace again after a problem or a hurt feeling.")],
    "imp": [("What is an imp in a story?",
               "An imp is a tiny mischievous creature in old stories. It likes tricks, but it can still change and be kind.")],
}
GHOST_ORDER = ["ghost", "quartz", "imp", "clean", "peace"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that includes the words "{f["object"].label}", hygienist, and imp.',
        f'Tell a spooky-but-kind story where a hygienist helps an imp make peace with {f["object"].phrase}.',
        f'Write a reconciliation story in a ghostly setting where the quartz stops sounding eerie after someone cleans it gently.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hyg, imp, quartz = f["hygienist"], f["imp"], f["quartz"]
    setting = f["setting"]
    obj = f["object"]
    action = f["action"]
    pred = f.get("predicted", {})
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about a hygienist, an imp, and a piece of quartz in a spooky place. The hygienist brings calm, while the imp starts out playful and noisy."
        ),
        QAItem(
            question="What made the room feel spooky at first?",
            answer=f"{obj.phrase} made its {obj.sound}, and the setting had {setting.echo}. That mix of sound and place made the room feel like a ghost story before anyone fixed it."
        ),
        QAItem(
            question="What did the hygienist do to help?",
            answer=f"{hyg.id} used {action.approach}, wiped the quartz clean, and set it in the light. That careful work turned the uneasy feeling into something calmer."
        ),
    ]
    if pred:
        items.append(
            QAItem(
                question="Why did the hygienist think the room could settle down?",
                answer=f"The hygienist could see that cleaning and polishing would help the quartz stop acting haunted. Because the quartz could gleam again, the imp had a chance to feel sorry and make peace."
            )
        )
    if f.get("outcome") == "reconciled":
        items.append(
            QAItem(
                question="How did the story end?",
                answer="It ended in reconciliation. The imp apologized, the hygienist answered kindly, and the quartz looked bright instead of lonely."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["object"].tags) | {"peace"}
    items: list[QAItem] = []
    for tag in GHOST_ORDER:
        if tag in tags and tag in GHOST_KNOWLEDGE:
            q, a = GHOST_KNOWLEDGE[tag][0]
            items.append(QAItem(q, a))
    return items


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.spectral:
            bits.append("spectral=True")
        if e.haunted:
            bits.append("haunted=True")
        if e.gleams:
            bits.append("gleams=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "quartz", "cleanse"),
    StoryParams("church", "quartz", "dust"),
    StoryParams("museum", "mirror", "listen"),
]


def explain_rejection(obj: ObjectCfg, action: Action) -> str:
    return f"(No story: this setup does not feel ghostly enough for a reconciliation tale with {obj.label}.)"


def valid_story(params: StoryParams) -> bool:
    return params.object in OBJECTS and params.action in ACTIONS and params.setting in SETTINGS


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.gleams:
            lines.append(asp.fact("gleams", oid))
        if obj.haunted:
            lines.append(asp.fact("haunted", oid))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sense", aid, act.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(O, A) :- object(O), action(A), sense(A, S), sense_min(M), S >= M, (gleams(O); haunted(O)).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set((o, a) for o, a in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print(" only in python:", sorted(py - cl))
        print(" only in clingo:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        _ = format_qa(sample)
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghostly reconciliation storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
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
    if args.object and args.action:
        if not reasonableness_gate(OBJECTS[args.object], ACTIONS[args.action]):
            raise StoryError(explain_rejection(OBJECTS[args.object], ACTIONS[args.action]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, action = rng.choice(sorted(combos))
    return StoryParams(setting, obj, action)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.object], ACTIONS[params.action])
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid object/action combos:")
        for o, a in combos:
            print(f"  {o:8} {a}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
