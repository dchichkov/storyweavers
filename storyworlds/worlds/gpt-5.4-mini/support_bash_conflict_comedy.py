#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/support_bash_conflict_comedy.py
===============================================================

A tiny storyworld built from the seed words "support" and "bash" with a
comedic conflict shape.

Premise
-------
Two children are trying to build a silly homemade stage prop for a pretend show.
One child wants the "support" to hold steady; the other wants to give it a
dramatic "bash" for a joke. The conflict is about whether to keep the prop
standing or to whack it for laughs.

The world is intentionally small:
- typed entities with physical meters and emotional memes
- state-driven causal changes
- a clear conflict beat
- a funny but safe ending image

This script follows the Storyweavers storyworld contract and can be run
directly.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Prop:
    id: str
    label: str
    support_kind: str
    bash_kind: str
    wobble: int
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sound: str
    force: int
    sense: int
    fail_phrase: str
    success_phrase: str
    tags: set[str] = field(default_factory=set)


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    if prop.meters["hit"] < THRESHOLD:
        return out
    sig = ("wobble", prop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.meters["wobble"] += 1
    world.get("room").memes["chaos"] += 1
    for eid in ("kid1", "kid2"):
        world.get(eid).memes["alarm"] += 1
    out.append("__wobble__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("wobble", "physical", _r_wobble)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str
    prop: str
    tool: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "backstage": "behind a tiny school stage",
    "garage": "in a cluttered garage",
    "playroom": "in a bright playroom",
}

PROPS = {
    "cardboard_tower": Prop("cardboard_tower", "cardboard tower", "support", "bash", 2,
                            "toppled into a soft pile", {"cardboard", "tower"}),
    "cushion_stack": Prop("cushion_stack", "cushion stack", "support", "bash", 3,
                          "collapsed into a giggling heap", {"cushion"}),
    "book_bridge": Prop("book_bridge", "book bridge", "support", "bash", 1,
                        "slid apart with a funny thump", {"book"}),
}

TOOLS = {
    "hammer_puppet": Tool("hammer_puppet", "a toy hammer", "the toy hammer", "Bam!", 3, 3,
                          "gave the toy hammer a bash, but it barely nudged the prop",
                          "gave the toy hammer a bash, and the prop clattered down",
                          {"toy", "bash"}),
    "elbow": Tool("elbow", "an elbow", "an elbow", "Boing!", 2, 4,
                  "bumped it with an elbow, but that only made everyone wobble",
                  "bumped it with an elbow, and the prop tipped over",
                  {"body", "bash"}),
    "soft_ball": Tool("soft_ball", "a soft ball", "a soft ball", "Poff!", 1, 2,
                      "tossed a soft ball at it, but the prop wobbled and held",
                      "tossed a soft ball, and the prop finally gave way",
                      {"ball", "bash"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Max", "Ben", "Eli", "Theo", "Sam"]
TRAITS = ["cheerful", "curious", "sensible", "playful", "sly"]


def reasonableness_ok(prop: Prop, tool: Tool) -> bool:
    return tool.sense >= SENSE_MIN and prop.bash_kind == "bash"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROPS:
            for t in TOOLS:
                if reasonableness_ok(PROPS[p], TOOLS[t]):
                    combos.append((s, p, t))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _build_world(params: StoryParams) -> World:
    world = World()
    kid1 = world.add(Entity(id=params.child1, kind="character", type=params.child1_gender,
                            role="supporter", traits=["careful"]))
    kid2 = world.add(Entity(id=params.child2, kind="character", type=params.child2_gender,
                            role="basher", traits=["silly"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent",
                              label="the parent"))
    room = world.add(Entity(id="room", type="room", label=SETTINGS[params.setting]))
    prop = world.add(Entity(id="prop", type="prop", label=PROPS[params.prop].label))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS[params.tool].label))
    world.facts.update(kid1=kid1, kid2=kid2, parent=parent, room=room, prop=prop,
                       tool=tool, setting=params.setting, prop_cfg=PROPS[params.prop],
                       tool_cfg=TOOLS[params.tool])
    return world


def tell(params: StoryParams) -> World:
    world = _build_world(params)
    kid1 = world.get("kid1")
    kid2 = world.get("kid2")
    parent = world.get("Parent")
    prop = world.get("prop")
    tool = world.get("tool")
    prop_cfg = PROPS[params.prop]
    tool_cfg = TOOLS[params.tool]

    kid1.memes["pride"] += 1
    kid2.memes["mischief"] += 1

    world.say(
        f"At {SETTINGS[params.setting]}, {kid1.id} and {kid2.id} were building a silly act. "
        f"They wanted {prop_cfg.label} to give the joke some support."
    )
    world.say(
        f"{kid1.id} patted the prop and said, 'Easy does it.' "
        f"{kid2.id} grinned and said, 'Or we could give it a bash.'"
    )

    world.para()
    kid1.memes["worry"] += 1
    world.say(
        f"{kid1.id} frowned. 'If you bash it now, the whole thing will fall over,' "
        f"{kid1.pronoun()} said."
    )
    world.say(
        f"{kid2.id} held up {tool_cfg.phrase} and made a tiny joke sound: {tool_cfg.sound}"
    )

    if tool_cfg.sense < SENSE_MIN:
        raise StoryError("The chosen bash tool is too silly to make a sensible story.")

    world.para()
    kid2.memes["defiance"] += 1
    prop.meters["hit"] += 1
    world.say(
        f"'{tool_cfg.sound} Nice bash!' {kid2.id} said, and {tool_cfg.success_phrase}."
    )
    propagate(world, narrate=False)

    if prop.meters["wobble"] >= THRESHOLD:
        world.say(
            f"The {prop_cfg.label} wobbled once, twice, and then {prop_cfg.mess}."
        )
        parent.memes["alert"] += 1
        world.say(
            f"{parent.label_word.capitalize()} came over fast and said, 'No more bashes. "
            f"Let's keep the support, not the smash.'"
        )
        kid2.memes["surprise"] += 1
        kid1.memes["relief"] += 1
        kid2.memes["relief"] += 1
        world.para()
        world.say(
            f"{kid1.id} straightened the pieces while {kid2.id} held them steady. "
            f"Then they laughed at the crooked shape and rebuilt it with better support."
        )
        world.say(
            f"This time the prop stood tall, and {kid2.id} promised to save the bash for pretend drums."
        )
        outcome = "wobbled"
    else:
        world.say(
            f"Nothing broke, but the prop shivered so much that everyone had to lean in and hold it."
        )
        world.say(
            f"They called that the funniest kind of support: two kids and one stubborn prop."
        )
        outcome = "steady"

    world.facts["outcome"] = outcome
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy for a 3-to-5-year-old that includes the words "support" and "bash".',
        f"Tell a funny story where {f['kid1'].id} wants to keep a prop in {f['setting']}, "
        f"but {f['kid2'].id} wants to bash it for a joke.",
        f"Write a child-friendly conflict story where a silly bash causes trouble, then the kids fix it with teamwork.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid1 = f["kid1"]
    kid2 = f["kid2"]
    prop_cfg = f["prop_cfg"]
    tool_cfg = f["tool_cfg"]
    qa = [
        ("Who was trying to support the prop?",
         f"{kid1.id} was trying to keep {prop_cfg.label} steady and give the joke some support."),
        ("Who wanted to bash it?",
         f"{kid2.id} wanted to give it a bash, mostly because it sounded funny to {kid2.id}."),
        ("What happened after the bash?",
         f"The prop wobbled and made a silly mess. That happened because a strong bash can shake a small prop loose."),
    ]
    if f["outcome"] == "wobbled":
        qa.append((
            "How did they fix the problem?",
            f"They rebuilt the prop with better support and held it still together. That way {tool_cfg.label} stayed part of the joke, but it did not knock anything down again."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with laughter, a steadier prop, and a safer plan for the next joke. The bash became something to save for pretend drums."
        ))
    else:
        qa.append((
            "How did they feel at the end?",
            f"They felt amused and a little proud that they kept the prop up. The funny part was that everyone had to help the support."
        ))
    return qa


KNOWLEDGE = {
    "support": [
        ("What is support?",
         "Support is help that holds something up so it does not fall down."),
    ],
    "bash": [
        ("What does it mean to bash something?",
         "To bash something means to hit it hard. That can make it wobble, break, or fall over."),
    ],
    "conflict": [
        ("What is a conflict in a story?",
         "A conflict is a problem or disagreement that the characters need to handle."),
    ],
    "comedy": [
        ("What is comedy?",
         "Comedy is a funny story or show that is meant to make people laugh."),
    ],
}
KNOWLEDGE_ORDER = ["support", "bash", "conflict", "comedy"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"support", "bash", "conflict", "comedy"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("backstage", "cardboard_tower", "hammer_puppet", "Mia", "girl", "Max", "boy", "mother"),
    StoryParams("garage", "book_bridge", "elbow", "Theo", "boy", "Nora", "girl", "father"),
    StoryParams("playroom", "cushion_stack", "soft_ball", "Lily", "girl", "Sam", "boy", "mother"),
]


def explain_rejection() -> str:
    return "(No story: that bash idea is too silly or too weak for this small comedy world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy storyworld about support, bash, and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
              and (args.prop is None or c[1] == args.prop)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prop, tool = rng.choice(sorted(combos))
    c1_gender = rng.choice(["girl", "boy"])
    c2_gender = "boy" if c1_gender == "girl" else "girl"
    c1 = args.name1 or choose_name(rng, c1_gender)
    c2 = args.name2 or choose_name(rng, c2_gender)
    if c1 == c2:
        c2 = choose_name(rng, c2_gender)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, prop, tool, c1, c1_gender, c2, c2_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
support_story(S, P, T) :- setting(S), prop(P), tool(T).
sensible(T) :- tool(T), sense(T, N), sense_min(M), N >= M.
conflict(P) :- prop(P).
outcome(wobble) :- hit_prop, wobble_prop.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p, cfg in PROPS.items():
        lines.append(asp.fact("prop", p))
        lines.append(asp.fact("wobble", p, cfg.wobble))
    for t, cfg in TOOLS.items():
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("sense", t, cfg.sense))
        lines.append(asp.fact("force", t, cfg.force))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show support_story/3."))
    return sorted(set(asp.atoms(model, "support_story")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import sys
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    sample = generate(CURATED[0])
    if not sample.story:
        rc = 1
        print("MISMATCH: generate() produced empty story.")
    else:
        print("OK: generate() smoke test passed.")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, t) for s in SETTINGS for p in PROPS for t in TOOLS if reasonableness_ok(PROPS[p], TOOLS[t])]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show support_story/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible())}\n")
        for s, p, t in asp_valid_combos():
            print(f"{s:10} {p:16} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child1} and {p.child2}: support vs bash ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
