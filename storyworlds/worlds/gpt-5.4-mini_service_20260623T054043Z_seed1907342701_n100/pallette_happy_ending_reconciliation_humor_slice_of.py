#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/pallette_happy_ending_reconciliation_humor_slice_of.py
===============================================================================================================

A small slice-of-life storyworld about a shared art session, a harmless mess,
a small squabble, and a cheerful reconciliation.

The seed prompt asks for:
- the word "pallette"
- Happy Ending
- Reconciliation
- Humor
- Slice of Life

This world models a tiny home/art-table scene where a child, a friend, and a
grown-up try to finish a picture on a pallette. A little paint mishap creates
social tension, but the tension is resolved with a joke, a snack, and a shared
cleanup. The ending always proves the change with a clean table, a finished
picture, and warm feelings.

The file is self-contained and follows the Storyweavers contract:
- StoryParams, build_parser, resolve_params, generate, emit, main
- QAItem / StoryError / StorySample imported eagerly
- ASP helper imported lazily inside ASP helpers
- JSON / trace / QA / verify / show-ASP supported
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    helper: str = ""
    room: str = ""
    portable: bool = False
    messy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

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
class Setting:
    place: str
    surface: str
    cozy_detail: str


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    splash: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    cause: str
    joke_line: str
    fix_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["spill"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.id == "palette":
            world.get("table").meters["painted"] += 1
            world.get("friend").memes["annoyed"] += 1
            world.get("child").memes["embarrassed"] += 1
            out.append("The table got painted, and the friend looked annoyed.")
    return out


def _r_apology(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["apologized"] < THRESHOLD:
        return out
    sig = ("apology",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("friend").memes["softened"] += 1
    world.get("child").memes["hope"] += 1
    out.append("The room got a little less prickly.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spill, _r_apology):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting("the kitchen", "the table", "sunlight on the tiles"),
    "sunroom": Setting("the sunroom", "the craft table", "a window full of bright light"),
    "porch": Setting("the porch", "the bench", "a tiny breeze"),
    "playroom": Setting("the playroom", "the low table", "a shelf of crayons"),
}

ACTIVITIES = {
    "painting": Activity("painting", "paint a sign", "painting signs", "spill", "painty", "smudged", {"table"}),
    "fingerpaint": Activity("fingerpaint", "make fingerpaint art", "making fingerpaint art", "splash", "splotchy", "sticky", {"table"}),
    "gluecraft": Activity("gluecraft", "build a collage", "building a collage", "glue", "sticky", "clumpy", {"table"}),
    "watercolor": Activity("watercolor", "paint with watercolors", "painting with watercolors", "drip", "drippy", "wobbly", {"table"}),
}

PROBLEMS = {
    "dropped_cup": Problem("dropped_cup", "the water cup toppled", "a bump on the table", "It was a very sneaky cup.", "The friend helped wipe it up.", {"spill"}),
    "wrong_color": Problem("wrong_color", "the blue ran into the yellow", "too much water", "The paint had big feelings.", "They laughed and called it a happy accident.", {"spill"}),
    "sticky_hand": Problem("sticky_hand", "one hand got sticky", "too much glue", "The glue clearly wanted a hug.", "The grown-up found a wet cloth and the joke got everyone smiling.", {"spill"}),
    "tilted_palette": Problem("tilted_palette", "the pallette tipped", "an elbow nudged it", "The pallette did not enjoy the surprise dance.", "They set it flat again and kept going together.", {"spill"}),
}

TOOLS = {
    "cloth": Tool("cloth", "a damp cloth", "a damp cloth", "used a damp cloth to wipe the mess"),
    "paper_towel": Tool("paper_towel", "paper towels", "paper towels", "used paper towels to dry the table"),
    "tray": Tool("tray", "a tray", "a tray", "set the pallette on a tray so it would stay steady"),
    "smock": Tool("smock", "a paint smock", "a paint smock", "put on a paint smock to keep clothes clean"),
}

GIRL_NAMES = ["Maya", "Lena", "Ivy", "Nora", "Ella", "Zoe", "Ada"]
BOY_NAMES = ["Ben", "Theo", "Milo", "Finn", "Noah", "Eli", "Sam"]
TRAITS = ["careful", "curious", "patient", "cheerful", "silly", "gentle"]


@dataclass
class StoryParams:
    setting: str = "kitchen"
    activity: str = "painting"
    problem: str = "tilted_palette"
    tool: str = "cloth"
    child_name: str = "Maya"
    child_gender: str = "girl"
    friend_name: str = "Ben"
    friend_gender: str = "boy"
    grownup_name: str = "Mom"
    grownup_gender: str = "mother"
    trait: str = "cheerful"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for activity in ACTIVITIES:
            for problem in PROBLEMS:
                for tool in TOOLS:
                    if "spill" in PROBLEMS[problem].tags:
                        combos.append((setting, activity, problem, tool))
    return combos


KNOWLEDGE = {
    "palette": [("What is a pallette?", "A pallette is a flat board or tray where artists mix colors before they paint.")],
    "paint": [("Why can paint make a mess?", "Paint can drip, splash, and smudge onto tables and hands, so people often try to keep it on paper or on a pallette.")],
    "cloth": [("What does a damp cloth do?", "A damp cloth helps wipe sticky or painted spots off a table so the surface can look clean again.")],
    "tray": [("What is a tray for?", "A tray helps hold things steady and keeps them from sliding around.")],
    "smock": [("Why wear a smock for art?", "A smock helps keep clothes from getting paint on them.")],
    "spill": [("What should you do after a spill?", "It is best to stay calm, clean up what you can, and ask for help if you need it.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a child who works on a pallette at {f["setting"].place} and has a small art mishap.',
        f'Write a gentle, funny reconciliation story where {f["child"].id} and {f["friend"].id} solve a paint problem together.',
        f'Write a happy ending story about art, a little mess, and a grown-up who helps everybody smile again. Include the word "pallette".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    grownup: Entity = f["grownup"]
    setting: Setting = f["setting"]
    activity: Activity = f["activity"]
    problem: Problem = f["problem"]
    tool: Tool = f["tool"]
    qa = [
        QAItem(
            question=f"What were {child.id} and {friend.id} doing at {setting.place}?",
            answer=f"They were {activity.gerund} at {setting.place}. It started as a normal little art session, with colors, paper, and a pallette on the table.",
        ),
        QAItem(
            question=f"Why did the pallette cause trouble in the story?",
            answer=f"The {problem.label} because {problem.cause}. That made the table messy, so everyone had to pause and fix it together.",
        ),
        QAItem(
            question=f"How did {child.id} and {friend.id} make up after the mess?",
            answer=f"They smiled, made a joke about it, and worked together with {tool.phrase}. The joke helped the grumpy feeling soften, and then they finished the art side by side.",
        ),
        QAItem(
            question=f"What did {grownup.id} do to help the children?",
            answer=f"{grownup.id} stayed calm and helped by {tool.use_line}. That made the cleanup easy, and it gave the children a chance to laugh instead of feel embarrassed.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The table was clean again, the picture was finished, and {child.id} and {friend.id} were smiling together. The pallette sat neatly in place, so the ending felt warm and happy.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | set(world.facts["problem"].tags) | set(world.facts["tool"].tags)
    if "pallette" in world.facts:
        tags.add("palette")
    out: list[QAItem] = []
    for k, pairs in KNOWLEDGE.items():
        if k in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if mm:
            bits.append(f"memes={dict(mm)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, problem: Problem, tool: Tool,
         child_name: str, child_gender: str, friend_name: str, friend_gender: str,
         grownup_name: str, grownup_gender: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_gender, label=grownup_name, role="grownup"))
    palette = world.add(Entity(id="palette", type="thing", label="pallette", phrase="the pallette", portable=True, messy=True))
    table = world.add(Entity(id="table", type="thing", label=setting.surface))
    world.facts.update(
        child=child, friend=friend, grownup=grownup, setting=setting,
        activity=activity, problem=problem, tool=tool, palette=palette,
        resolved=False,
    )
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(f"{child.label} and {friend.label} were having a small art day at {setting.place}.")
    world.say(f"{setting.cozy_detail} sat nearby while the pallette waited on the table.")
    world.say(f"They were {activity.gerund}, and the room felt easy and ordinary, the kind of afternoon that likes crayons and quiet jokes.")
    world.para()
    child.memes["surprise"] += 1
    friend.memes["surprise"] += 1
    palette.meters["spill"] += 1
    propagate(world, narrate=True)
    world.say(f"Then {problem.label}, and {problem.joke_line}")
    child.memes["embarrassed"] += 1
    friend.memes["annoyed"] += 1
    world.say(f'{friend.label} made a face. "{problem.fix_line}"')
    world.para()
    child.memes["apologized"] += 1
    world.say(f'{child.label} laughed first. "{tool.use_line}, and maybe the pallette wanted to dance," {child.label} said.')
    propagate(world, narrate=True)
    world.say(f'{friend.label} snorted, because that was a ridiculous image and therefore exactly the right joke.')
    world.say(f"{grownup.label} came over with {tool.phrase} and helped them clean the table in a few quick swipes.")
    world.say(f"Before long, the mess was gone, the colors were back in order, and the three of them were smiling again.")
    world.para()
    world.facts["resolved"] = True
    world.say(f"The finished picture sat on the table, and the pallette rested beside it like nothing had ever gone wrong.")
    world.say(f"{child.label} and {friend.label} leaned over the art together, still giggling, with clean hands and a happy room around them.")
    return world


ASP_RULES = r"""
spill_needs_cleanup(P) :- pallette(P), spill(P).
softened(F) :- apology(C), friend(F), child(C).
happy_end :- resolved.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in a.tags:
            lines.append(asp.fact("act_tag", aid, t))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in p.tags:
            lines.append(asp.fact("prob_tag", pid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in t.tags:
            lines.append(asp.fact("tool_tag", tid, tag))
    lines.append(asp.fact("pallette", "pallette"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show spill_needs_cleanup/1."))
    return sorted(set(asp.atoms(model, "spill_needs_cleanup")))


def asp_verify() -> int:
    import io
    import contextlib
    from dataclasses import replace
    p = set(asp_valid_combos())
    q = set(valid_combos())
    rc = 0
    if len(q) >= 4:
        print(f"OK: valid_combos() has {len(q)} rows.")
    else:
        print(f"MISMATCH: valid_combos() too small ({len(q)}).")
        rc = 1
    if p == {("pallette",)}:
        print("OK: ASP program grounds the pallette fact.")
    else:
        print(f"MISMATCH: ASP facts unexpected: {sorted(p)}")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, activity=None, problem=None, tool=None, child_name=None, child_gender=None, friend_name=None, friend_gender=None, grownup_name=None, grownup_gender=None, trait=None), random.Random(777)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        if not sample.story or "pallette" not in sample.story:
            raise RuntimeError("smoke story failed")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a tiny art-table slice-of-life with a pallette, a joke, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup-name")
    ap.add_argument("--grownup-gender", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.activity:
        combos = [c for c in combos if c[1] == args.activity]
    if args.problem:
        combos = [c for c in combos if c[2] == args.problem]
    if args.tool:
        combos = [c for c in combos if c[3] == args.tool]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, problem, tool = rng.choice(sorted(combos))
    cgender = args.child_gender or rng.choice(["girl", "boy"])
    fgender = args.friend_gender or ("boy" if cgender == "girl" else "girl")
    return StoryParams(
        setting=setting,
        activity=activity,
        problem=problem,
        tool=tool,
        child_name=args.child_name or rng.choice(GIRL_NAMES if cgender == "girl" else BOY_NAMES),
        child_gender=cgender,
        friend_name=args.friend_name or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != (args.child_name or "")]),
        friend_gender=fgender,
        grownup_name=args.grownup_name or rng.choice(["Mom", "Dad"]),
        grownup_gender=args.grownup_gender or rng.choice(["mother", "father"]),
        trait=args.trait or rng.choice(TRAITS),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("unknown setting")
    if params.activity not in ACTIVITIES:
        raise StoryError("unknown activity")
    if params.problem not in PROBLEMS:
        raise StoryError("unknown problem")
    if params.tool not in TOOLS:
        raise StoryError("unknown tool")
    world = tell(
        SETTINGS[params.setting],
        ACTIVITIES[params.activity],
        PROBLEMS[params.problem],
        TOOLS[params.tool],
        params.child_name, params.child_gender, params.friend_name, params.friend_gender,
        params.grownup_name, params.grownup_gender, params.trait,
    )
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
    StoryParams(setting="kitchen", activity="painting", problem="tilted_palette", tool="cloth", child_name="Maya", child_gender="girl", friend_name="Ben", friend_gender="boy", grownup_name="Mom", grownup_gender="mother", trait="cheerful"),
    StoryParams(setting="sunroom", activity="watercolor", problem="wrong_color", tool="paper_towel", child_name="Theo", child_gender="boy", friend_name="Lena", friend_gender="girl", grownup_name="Dad", grownup_gender="father", trait="silly"),
    StoryParams(setting="playroom", activity="fingerpaint", problem="sticky_hand", tool="smock", child_name="Ivy", child_gender="girl", friend_name="Noah", friend_gender="boy", grownup_name="Mom", grownup_gender="mother", trait="gentle"),
    StoryParams(setting="porch", activity="gluecraft", problem="dropped_cup", tool="tray", child_name="Eli", child_gender="boy", friend_name="Zoe", friend_gender="girl", grownup_name="Dad", grownup_gender="father", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show spill_needs_cleanup/1.\n#show softened/1.\n#show happy_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show spill_needs_cleanup/1."))
        print(asp.atoms(model, "spill_needs_cleanup"))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
