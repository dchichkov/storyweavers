#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jam_dim_moral_value_foreshadowing_comedy.py
============================================================================

A small standalone storyworld for a comic, moral TinyStories-style domain:
a child helps in a kitchen, notices a jam-dim problem, learns to tell the truth,
and ends with a bright, funny fix that was foreshadowed earlier.

This world intentionally keeps the domain tiny:
- jam jars, sticky hands, a dim pantry light, and one honest mistake
- a parent, a child, and a little helper action
- comedy comes from small absurdity, not slapstick chaos
- foreshadowing is encoded in the world model, not pasted onto prose
- the moral value is honesty + cleanup + sharing responsibility

Run it:
    python storyworlds/worlds/gpt-5.4-mini/jam_dim_moral_value_foreshadowing_comedy.py
    python storyworlds/worlds/gpt-5.4-mini/jam_dim_moral_value_foreshadowing_comedy.py --all
    python storyworlds/worlds/gpt-5.4-mini/jam_dim_moral_value_foreshadowing_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/jam_dim_moral_value_foreshadowing_comedy.py --verify
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
FORESHADOW_THRESHOLD = 1.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    dim: str
    has_dim_lamp: bool = False

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
class JamItem:
    id: str
    label: str
    sticky: bool = True
    edible: bool = True
    bright: bool = False

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
    verb: str
    setup: str
    reveal: str
    fix: str
    moral: str
    foreshadow: str

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
        self.light_level: float = 0.0

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
        c.light_level = self.light_level
        return c


@dataclass
class Rule:
    name: str
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


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["jam"] >= THRESHOLD and "face" not in child.attrs.get("cleaned", set()):
        sig = ("sticky",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["sticky"] += 1
            out.append("__sticky__")
    return out


def _r_dim(world: World) -> list[str]:
    out: list[str] = []
    if world.light_level < 0.5 and "lamp" not in world.entities:
        sig = ("dim",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("parent").memes["foreshadow"] += 1
            out.append("__dim__")
    return out


CAUSAL_RULES = [Rule("sticky", _r_sticky), Rule("dim", _r_dim)]


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


def predict_mess(world: World) -> dict:
    sim = world.copy()
    _spill(sim, narrate=False)
    return {
        "sticky": sim.get("child").meters["sticky"] >= THRESHOLD,
        "foreshadow": sim.get("parent").memes["foreshadow"] >= FORESHADOW_THRESHOLD,
    }


def _spill(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["jam"] += 1
    child.meters["spill"] += 1
    world.get("jar").meters["open"] += 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "a dim pantry door", has_dim_lamp=True),
    "bakery": Setting("bakery", "the bakery counter", "a dim back shelf", has_dim_lamp=True),
    "picnic": Setting("picnic", "the picnic table", "a dim shady basket", has_dim_lamp=False),
}

JAMS = {
    "strawberry": JamItem("strawberry", "strawberry jam"),
    "blueberry": JamItem("blueberry", "blueberry jam"),
    "apricot": JamItem("apricot", "apricot jam"),
}

ACTIONS = {
    "jar": Action(
        "jar",
        "reach for the jam jar",
        "the child wanted a taste and reached for the jar",
        "the jar tipped in the dim light and made a sticky mess",
        "the parent opened the window and handed over a towel",
        "Honesty makes a small mistake easier to fix",
        "the pantry light was already a little dim",
    ),
    "toast": Action(
        "toast",
        "spread jam on toast",
        "the child was hungry and wanted a sweet snack",
        "the jam slid off the toast and dotted the table",
        "the parent turned on a lamp and handed over a napkin",
        "Sharing the truth helps cleanup begin sooner",
        "the table was set beside a dim little lamp",
    ),
    "spoon": Action(
        "spoon",
        "taste the jam with a spoon",
        "the child wanted one tiny spoonful",
        "the spoon dripped jam and made the sleeve sticky",
        "the parent laughed and fetched a cloth",
        "Telling the truth is better than hiding a mess",
        "the shelf looked dim before anyone touched it",
    ),
}

CHILD_NAMES = ["Mia", "Ben", "Nora", "Leo", "Zoe", "Max", "Lily", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in ACTIONS:
            for jid in JAMS:
                combos.append((sid, aid, jid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    action: str
    jam: str
    child_name: str
    child_gender: str
    parent_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny jam-dim story world with moral value and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--jam", choices=JAMS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.jam is None or c[2] == args.jam)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, jam = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, action, jam, name, gender, parent)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    action = ACTIONS[params.action]
    jam = JAMS[params.jam]
    world = World(setting)
    child = world.add(Entity("child", kind="character", type=params.child_gender, role="child"))
    child.id = params.child_name
    world.entities[params.child_name] = child
    del world.entities["child"]
    child.id = params.child_name
    parent = world.add(Entity("parent", kind="character", type=params.parent_gender, role="parent"))
    parent.label = "the parent"
    jar = world.add(Entity("jar", type="thing", label=jam.label))
    lamp = world.add(Entity("lamp", type="thing", label="the little lamp"))

    child.memes["curious"] += 1
    world.light_level = 0.2 if setting.has_dim_lamp else 0.1

    world.say(
        f"{params.child_name} stood in {setting.place} with a smile and a sticky "
        f"promise of snacks. {action.foreshadow.capitalize()}."
    )
    world.say(
        f"{params.child_name} wanted to {action.verb}, and the whole scene felt "
        f"funny because everything was a little too serious for jam."
    )

    world.para()
    child.memes["desire"] += 1
    pred = predict_mess(world)
    world.facts["predicted"] = pred
    world.say(
        f'"It looks a bit {setting.dim}," said the {params.parent_gender if False else parent.label_word}. '
        f'"Maybe we should be careful with the {jam.label}."'
    )
    if pred["sticky"]:
        child.memes["embarrassment"] += 1
        world.say(
            f"{params.child_name} blinked, then admitted the jar was already wobbling. "
            f"That honest little confession made the parent grin instead of scold."
        )

    _spill(world)
    world.para()
    world.say(
        f"The {jam.label} tipped, and the {params.action} turned into a sticky joke. "
        f"{params.child_name}'s hands got jam on them, and even the air seemed to go "
        f"{action.reveal}."
    )
    world.say(
        f"{parent.label_word.capitalize()} did not gasp loudly; {parent.pronoun()} just laughed, "
        f"because the mess was small and the truth was already out."
    )
    child.attrs["cleaned"] = {"face", "hands"}
    child.meters["sticky"] = 0
    world.get("jar").meters["open"] = 0
    world.para()
    world.say(
        f"Together they wiped the table, turned on the lamp, and fixed the snack the honest way. "
        f"{action.fix.capitalize()}."
    )
    world.say(
        f"{params.child_name} got to taste {jam.label} after the cleanup, and the dim kitchen "
        f"looked bright enough for a happy grin."
    )
    world.say(
        f"In the end, {action.moral.lower()}. {params.child_name} learned that telling the truth "
        f"makes a small problem funny instead of big."
    )

    world.facts.update(
        child=child, parent=parent, jar=jar, lamp=lamp, setting=setting,
        action=action, jam=jam, outcome="cleaned", honest=True
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comic story for a young child that includes the word "jam-dim" and a moral about honesty.',
        f"Tell a funny story where {f['child'].id} is in {f['setting'].place} with {f['jam'].label} and the light is dim.",
        f"Write a short foreshadowing story where a small jam mistake gets fixed kindly and ends with a moral lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    action = f["action"]
    jam = f["jam"]
    qa = [
        ("What was the child trying to do?",
         f"{child.id} was trying to {action.verb}. The idea seemed simple, but the dim light made the scene a little silly."),
        ("What made the story funny?",
         f"The kitchen was dim and the jam jar wobbled like it had its own joke. That small wobble turned the moment into a sticky comedy."),
        ("What did the parent do after the mess?",
         f"{parent.label_word.capitalize()} laughed, helped wipe the table, and turned on the lamp. That made the cleanup calm instead of scary."),
        ("What did the child learn?",
         f"{action.moral}. {child.id} learned that telling the truth helps grown-ups fix a mistake quickly."),
    ]
    qa.append((
        "How was the warning foreshadowed?",
        f"The story mentioned that the pantry or shelf was already dim before the jar tipped. That clue prepared us for the wobble and the sticky mess."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is jam?",
         "Jam is a sweet spread made from fruit. People often put it on toast or bread."),
        ("What does dim mean?",
         "Dim means not very bright. A dim room can be hard to see in."),
        ("Why should you tell the truth after making a mistake?",
         "Telling the truth helps a grown-up fix the problem quickly. It also shows you are being responsible."),
        ("What should you do if a jar spills?",
         "Stay calm, tell a grown-up, and help clean it up safely. That is better than hiding the spill."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "jar", "strawberry", "Mila", "girl", "mother"),
    StoryParams("bakery", "toast", "apricot", "Ben", "boy", "father"),
    StoryParams("picnic", "spoon", "blueberry", "Nora", "girl", "mother"),
]


def valid_outcome(_: StoryParams) -> str:
    return "cleaned"


def explain_rejection(setting: str, action: str, jam: str) -> str:
    return "(No story: this tiny world accepts the requested jam-dim setup, so the rejection helper should not be needed.)"


ASP_RULES = r"""
valid(S, A, J) :- setting(S), action(A), jam(J).
dim_hint(S) :- setting(S), has_dim_lamp(S).
sticky_after(A) :- action(A).
moral_value(A) :- action(A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_dim_lamp:
            lines.append(asp.fact("has_dim_lamp", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for jid in JAMS:
        lines.append(asp.fact("jam", jid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(rng_base + i))
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
