#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/perceptive_pull_banter_lesson_learned_happy_ending.py
======================================================================================

A tiny bedtime-story world about a child, a stuck ribbon, a perceptive friend,
a careful pull, a little banter, and a lesson learned with a happy ending.

The premise is classical and small:
- one child wants a thing that is stuck or tangled,
- another child notices the real problem first,
- they try a gentle, sensible pull instead of a rough tug,
- they banter a little while they work,
- they learn a calm lesson,
- the story ends with a bright, cozy image.

This file is standalone and stdlib-only.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Thing:
    id: str
    label: str
    stuck_kind: str
    fix_kind: str
    place: str
    near: str
    safe_image: str
    danger_image: str
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
class Reaction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class Theme:
    id: str
    setting: str
    bedtime_opening: str
    game: str
    cozy_end: str

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

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["relief"] >= THRESHOLD:
            sig = ("relief", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["joy"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief)]


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


def sensible_reactions() -> list[Reaction]:
    return [r for r in REACTIONS.values() if r.sense >= SENSE_MIN]


def valid_combo(theme: Theme, thing: Thing, reaction: Reaction) -> bool:
    return thing.fix_kind in reaction.tags and reaction.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid, theme in THEMES.items():
        for xid, thing in THINGS.items():
            for rid, reaction in REACTIONS.items():
                if valid_combo(theme, thing, reaction):
                    combos.append((tid, xid, rid))
    return combos


def should_learn(thing: Thing, reaction: Reaction) -> bool:
    return reaction.power >= 1 and thing.fix_kind in reaction.tags


def _careful_pull(world: World, child: Entity, thing: Thing, reaction: Reaction) -> None:
    child.memes["perceptive"] += 1
    child.memes["banter"] += 1
    child.meters["care"] += 1
    world.say(
        f'{child.id} was perceptive and noticed that {thing.label} was stuck {thing.place}, '
        f'not broken. "{thing.label.capitalize()} needs a gentle pull," {child.id} said.'
    )
    world.say(
        f'"A gentle pull?" the other child asked, with a sleepy grin. '
        f'"That sounds better than a grumpy yank."'
    )
    world.say(
        f'Together they gave it a careful pull, and {reaction.text}.'
    )
    child.memes["relief"] += 1


def _lesson(world: World, child: Entity, thing: Thing, reaction: Reaction) -> None:
    world.say(
        f'For a moment they paused and learned the lesson: if you stop and look first, '
        f'you can solve a small problem without making it bigger.'
    )
    world.say(
        f'Then {child.id} smiled at the neat little rescue and tucked {thing.label} into '
        f'{thing.safe_image}.'
    )


def _oops(world: World, child: Entity, thing: Thing, reaction: Reaction) -> None:
    child.memes["worry"] += 1
    world.say(
        f"They tried a rough pull, but {reaction.fail}. The ribbon only tightened, and "
        f"the moment turned wobbly and sad."
    )


def tell(theme: Theme, thing: Thing, reaction: Reaction,
         child_a: str = "Mina", child_b: str = "Theo",
         child_a_type: str = "girl", child_b_type: str = "boy",
         parent: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=child_a, kind="character", type=child_a_type, role="perceptive"))
    b = world.add(Entity(id=child_b, kind="character", type=child_b_type, role="banter"))
    mom = world.add(Entity(id=parent, kind="character", type=parent, label=f"the {parent}"))

    a.memes["perceptive"] = 2.0
    b.memes["banter"] = 1.0
    mom.memes["warm"] = 1.0

    world.say(theme.bedtime_opening)
    world.say(
        f"That night, {a.id} and {b.id} were playing {theme.game} in {theme.setting}. "
        f"Then {thing.label} got stuck {thing.place}, just where the moonlight could not reach."
    )
    world.say(
        f'{b.id} reached first and wanted to pull hard, but {a.id} was perceptive enough to '
        f'look closely.'
    )
    world.para()
    if should_learn(thing, reaction):
        _careful_pull(world, a, thing, reaction)
        world.para()
        _lesson(world, a, thing, reaction)
        a.memes["lesson_learned"] += 1
        b.memes["lesson_learned"] += 1
        a.memes["happy"] += 1
        b.memes["happy"] += 1
        world.say(
            f'{thing.safe_image.capitalize()} glowed softly under the blanket, and the children '
            f'fell asleep with a happy ending and a quiet little smile.'
        )
    else:
        _oops(world, a, thing, reaction)

    world.facts.update(
        theme=theme,
        thing=thing,
        reaction=reaction,
        child_a=a,
        child_b=b,
        parent=mom,
        happy=True,
        learned=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    thing = f["thing"]
    return [
        f'Write a bedtime story for a young child that uses the words "perceptive", '
        f'"pull", and "banter", and ends happily.',
        f"Tell a cozy story where {f['child_a'].id} notices that {thing.label} is only "
        f"stuck, not broken, and the children solve it with a gentle pull.",
        f"Write a small happy-ending tale about two children who banter a little, learn a "
        f"lesson, and fix {thing.label} the calm way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    thing = f["thing"]
    a = f["child_a"]
    b = f["child_b"]
    return [
        ("Who was perceptive in the story?",
         f"{a.id} was perceptive. {a.id} looked closely and noticed the thing was stuck, "
         f"not ruined, which changed what they did next."),
        ("What did the children do instead of a rough yank?",
         f"They gave {thing.label} a gentle pull. That careful move was enough to free it "
         f"without making the tangle worse."),
        ("How did the banter help?",
         f"The banter kept the moment light and calm. It turned the problem into a shared "
         f"little job instead of a scary one."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does perceptive mean?",
         "Perceptive means noticing small things quickly and understanding what is really going on."),
        ("Why can a hard pull be a bad idea?",
         "A hard pull can make a knot tighter or break something. A gentle pull is often safer when you are not sure what is wrong."),
        ("What is banter?",
         "Banter is light, playful talking between people. It can make a busy moment feel friendlier."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


THEMES = {
    "bedroom": Theme("bedroom", "a cozy bedroom", "The lamp glowed low and the blanket was soft.", "story", "a warm bed"),
    "nursery": Theme("nursery", "a sleepy nursery", "The rocking chair waited by the window, and the room was hushed.", "playtime", "a warm pillow"),
    "attic": Theme("attic", "a quiet attic", "The little room was full of old treasures and a sleepy hush.", "make-believe", "a tucked-away basket"),
}

THINGS = {
    "kite_string": Thing("kite_string", "kite string", "stuck on a chair leg", "ribbon", "the playroom",
                         "a little basket", "the basket under the blanket", "a twisted knot", tags={"ribbon"}),
    "ribbon": Thing("ribbon", "blue ribbon", "caught on a doorknob", "ribbon", "the hall",
                    "a drawer", "the ribbon box", "a messy snag", tags={"ribbon"}),
    "thread": Thing("thread", "gold thread", "wrapped around a toy box", "thread", "the corner",
                    "a sewing tin", "the sewing tin", "a little snarl", tags={"thread"}),
}

REACTIONS = {
    "gentle_pull": Reaction("gentle_pull", 3, 3,
                            "the ribbon slipped free with a soft little swish",
                            "the tug only made the knot tighter",
                            "pulled it free with a soft little swish",
                            tags={"ribbon", "thread"}),
    "easy_pull": Reaction("easy_pull", 2, 2,
                          "it came loose in one bright, easy slide",
                          "the pull only tightened the twist",
                          "came loose in one bright, easy slide",
                          tags={"ribbon", "thread"}),
}

CURATED = [
    dataclass(type("P", (), {}))
]

# Replace the placeholder with actual curated params below.
@dataclass
class StoryParams:
    theme: str
    thing: str
    reaction: str
    child_a: str
    child_a_type: str
    child_b: str
    child_b_type: str
    parent: str
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


CURATED = [
    StoryParams("bedroom", "kite_string", "gentle_pull", "Mina", "girl", "Theo", "boy", "mother"),
    StoryParams("nursery", "ribbon", "easy_pull", "Lila", "girl", "Noah", "boy", "father"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("fix_kind", tid, t.fix_kind))
    for rid, r in REACTIONS.items():
        lines.append(asp.fact("reaction", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
        for tg in sorted(r.tags):
            lines.append(asp.fact("supports", rid, tg))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, X, R) :- theme(T), thing(X), reaction(R), fix_kind(X, K), supports(R, K), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        ok = False
        print("MISMATCH in valid combos.")
        print("python:", sorted(valid_combos()))
        print("asp:", sorted(asp_valid_combos()))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: perceptive pull banter lesson learned happy ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
              if (args.theme is None or c[0] == args.theme)
              and (args.thing is None or c[1] == args.thing)
              and (args.reaction is None or c[2] == args.reaction)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, thing, reaction = rng.choice(sorted(combos))
    a = args.name_a or rng.choice(["Mina", "Lila", "Pia", "Nora", "Ivy"])
    b = args.name_b or rng.choice([n for n in ["Theo", "Noah", "Eli", "Finn", "Jude"] if n != a])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(theme, thing, reaction, a, "girl", b, "boy", parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], THINGS[params.thing], REACTIONS[params.reaction],
                 params.child_a, params.child_a_type, params.child_b, params.child_b_type, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (theme, thing, reaction) combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
