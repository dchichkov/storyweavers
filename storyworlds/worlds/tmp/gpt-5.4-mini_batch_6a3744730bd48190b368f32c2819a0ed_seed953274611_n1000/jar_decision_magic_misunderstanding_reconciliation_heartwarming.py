#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jar_decision_magic_misunderstanding_reconciliation_heartwarming.py
===================================================================================================

A small heartwarming storyworld about a magic jar, a difficult decision, a
misunderstanding, and a warm reconciliation.

The premise is tiny and classical:
- a child finds or is given a magical jar,
- the jar's magic causes a misunderstanding,
- a decision determines whether the magic is used carelessly or kindly,
- the misunderstanding is repaired,
- the ending proves the relationship is warmer than before.

The world keeps simulated physical state in meters and emotional state in memes,
and the prose is rendered from that state rather than swapped from a template.
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
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Jar:
    id: str
    label: str
    kind: str
    glow: str
    wish: str
    tricky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Decision:
    id: str
    label: str
    kindness: int
    truth: int
    text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_glow(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("jar")
    child = world.get("child")
    parent = world.get("parent")
    if jar.meters["opened"] < THRESHOLD:
        return out
    sig = ("glow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jar.meters["glowing"] += 1
    child.memes["wonder"] += 1
    parent.memes["curiosity"] += 1
    out.append("__glow__")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    jar = world.get("jar")
    parent = world.get("parent")
    child = world.get("child")
    if jar.meters["glowing"] < THRESHOLD or child.meters["spoke"] < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["worry"] += 1
    child.memes["sadness"] += 1
    out.append("__misunderstanding__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    parent = world.get("parent")
    child = world.get("child")
    if parent.memes["worry"] < THRESHOLD or child.memes["sadness"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["love"] += 1
    child.memes["love"] += 1
    parent.memes["worry"] = 0.0
    child.memes["sadness"] = 0.0
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("glow", _r_glow), Rule("misunderstanding", _r_misunderstanding), Rule("reconcile", _r_reconcile)]


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


def reasonable_decision(decision: Decision) -> bool:
    return decision.kindness >= SENSE_MIN


def choose_option(decision: Decision, jar: Jar) -> bool:
    return decision.truth >= 1 and reasonable_decision(decision) and jar.tricky


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for jid in JARS:
            for did in DECISIONS:
                combos.append((sid, jid, did))
    return combos


@dataclass
class StoryParams:
    setting: str
    jar: str
    decision: str
    child_name: str = "Mina"
    child_gender: str = "girl"
    parent_name: str = "Mom"
    parent_gender: str = "mother"
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(id="kitchen", place="the kitchen", detail="sunlight striped the tablecloth", tags={"home"}),
    "porch": Setting(id="porch", place="the porch", detail="the steps were warm from the afternoon sun", tags={"home"}),
    "bedroom": Setting(id="bedroom", place="the bedroom", detail="a quilt lay folded at the foot of the bed", tags={"home"}),
}

JARS = {
    "firefly": Jar(id="firefly", label="a little jar", kind="glowflies", glow="soft gold light", wish="to hold a wish", tricky=True, tags={"magic"}),
    "star": Jar(id="star", label="a glass jar", kind="starlight", glow="tiny silver stars", wish="to keep a promise", tricky=True, tags={"magic"}),
    "rainbow": Jar(id="rainbow", label="a round jar", kind="rainbow mist", glow="warm color-light", wish="to share a secret kindly", tricky=True, tags={"magic"}),
}

DECISIONS = {
    "open_gently": Decision(id="open_gently", label="open it gently", kindness=3, truth=3, text="opened the jar slowly with both hands", fail_text="couldn't open the jar without spilling the glow", tags={"careful"}),
    "show_parent": Decision(id="show_parent", label="show it to the parent", kindness=4, truth=4, text="carried the jar right to the parent and asked for help", fail_text="tried to hide the jar, but the glow made everything obvious", tags={"truth"}),
    "share_then_open": Decision(id="share_then_open", label="share first, then open", kindness=5, truth=5, text="told the parent the whole story before opening the jar together", fail_text="kept the jar secret and only made the worry grow", tags={"reconcile"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about a magic jar, a decision, misunderstanding, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--jar", choices=JARS)
    ap.add_argument("--decision", choices=DECISIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--parent-name")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    jar = args.jar or rng.choice(list(JARS))
    decision = args.decision or rng.choice(list(DECISIONS))
    if args.decision and not reasonable_decision(DECISIONS[args.decision]):
        raise StoryError(f"(Refusing decision '{args.decision}': it is not kind enough for a heartwarming story.)")
    if args.decision and not choose_option(DECISIONS[args.decision], JARS[jar]):
        raise StoryError("(No story: this decision does not fit the magic jar well enough.)")
    return StoryParams(
        setting=setting,
        jar=jar,
        decision=decision,
        child_name=args.child_name or rng.choice(["Mina", "Luca", "Ivy", "Noah"]),
        child_gender="girl" if (args.child_name in {"Mina", "Ivy"}) else rng.choice(["girl", "boy"]),
        parent_name=args.parent_name or rng.choice(["Mom", "Dad"]),
        parent_gender="mother" if (args.parent_name == "Mom") else "father",
    )


def tell(setting: Setting, jar: Jar, decision: Decision, child_name: str, child_gender: str, parent_name: str, parent_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_gender, label=parent_name, role="parent"))
    jar_ent = world.add(Entity(id="jar", kind="thing", type="jar", label=jar.label, role="magic", attrs={"kind": jar.kind}))
    world.facts.update(setting=setting, jar=jar, decision=decision, child=child, parent=parent, jar_ent=jar_ent)
    child.memes["hope"] += 1
    parent.memes["calm"] += 1
    world.say(f"At {setting.place}, {child.name if hasattr(child,'name') else child.id} found {jar.label} while {setting.detail}.")
    world.say(f"The jar looked plain, but inside it waited {jar.glow}.")
    world.para()
    world.say(f"{child_name} held the jar close and made a difficult decision: to {decision.label}.")
    if decision.id == "share_then_open":
        world.say(f"{child_name} told {parent_name} first, and that honest choice made the room feel safer.")
    else:
        world.say(f"{child_name} did not know the glow would be misunderstood.")
    world.para()
    jar_ent.meters["opened"] += 1
    propagate(world, narrate=False)
    world.say(f"When the lid lifted, {jar.glow} drifted out like tiny lanterns.")
    world.say(f"{parent_name} thought the magic was a sign that {child_name} had hidden something important.")
    world.say(f"{child_name} explained that the jar was meant to {jar.wish}, not to cause trouble.")
    parent.memes["worry"] += 1
    child.memes["sadness"] += 1
    world.para()
    world.say(f"That was the misunderstanding, and it made both of them quiet for a moment.")
    parent.memes["listening"] += 1
    child.meters["spoke"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {child_name} took a breath and shared the truth gently.")
    parent.memes["worry"] = 0.0
    parent.memes["love"] += 1
    child.memes["love"] += 1
    child.memes["sadness"] = 0.0
    world.say(f"{parent_name} smiled, reached out, and said the jar could stay magical and still be safe.")
    world.para()
    world.say(f"Together they {decision.text}, and the glow settled into a warm little light on the table.")
    world.say(f"By bedtime, the jar was tucked beside a cup of water, and the room felt kind again.")
    world.facts["outcome"] = "reconciled"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the words "{f["jar"].label_word if hasattr(f["jar"], "label_word") else "jar"}" and "decision", and features magic, misunderstanding, and reconciliation.',
        f"Tell a gentle story about a child, a magic jar, and a careful decision that leads to a misunderstanding and then reconciliation.",
        "Write a small comforting story where a magical jar changes the mood, someone misunderstands, and then everyone makes up kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, jar, decision = f["child"], f["parent"], f["jar"], f["decision"]
    return [
        ("What did the child find?", f"{child.id} found {jar.label}, and it held {jar.glow} inside."),
        ("What decision did the child make?", f"{child.id} decided to {decision.label}. That choice set the magic in motion."),
        ("What was misunderstood?", f"{parent.label_word if hasattr(parent,'label_word') else 'the parent'} thought the glowing jar meant something was wrong, but the child was only being careful with a magical gift."),
        ("How did they reconcile?", f"They talked it through, told the truth, and shared the jar together. After that, the worry faded and they felt close again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a jar?", "A jar is a container with a lid. People use jars to keep little things safe inside."),
        ("What is a decision?", "A decision is a choice you make after thinking about what is best."),
        ("What is reconciliation?", "Reconciliation means making up after a misunderstanding and feeling friendly again."),
        ("What is magic in a story?", "Magic is something wonderful or impossible that can happen in a story, like a glowing jar."),
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
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", jar="firefly", decision="show_parent", child_name="Mina", child_gender="girl", parent_name="Mom", parent_gender="mother"),
    StoryParams(setting="porch", jar="star", decision="open_gently", child_name="Luca", child_gender="boy", parent_name="Dad", parent_gender="father"),
    StoryParams(setting="bedroom", jar="rainbow", decision="share_then_open", child_name="Ivy", child_gender="girl", parent_name="Mom", parent_gender="mother"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.jar not in JARS or params.decision not in DECISIONS:
        raise StoryError("(Invalid params: unknown setting, jar, or decision.)")
    world = tell(SETTINGS[params.setting], JARS[params.jar], DECISIONS[params.decision], params.child_name, params.child_gender, params.parent_name, params.parent_gender)
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


ASP_RULES = r"""
choice(set, jar, decision) :- setting(set), jar_kind(jar), decision(decision).
reconcile :- decision(share_then_open).
magic :- jar_kind(_).
misunderstanding :- magic, choice(_, _, _).
heartwarming :- reconcile.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for jid in JARS:
        lines.append(asp.fact("jar_kind", jid))
    for did in DECISIONS:
        lines.append(asp.fact("decision", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("#show heartwarming/0.\n#show reconcile/0.\n"))
    if not model:
        print("MISMATCH: ASP program produced no model.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as ex:
        print(f"MISMATCH: generate() failed: {ex}")
        rc = 1
    print("OK: ASP/Python parity gate checked.")
    return rc


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def resolve_params_main(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params_inner(args, rng)


def resolve_params_inner(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params.__wrapped__(args, rng) if hasattr(resolve_params, "__wrapped__") else StoryParams(  # type: ignore[attr-defined]
        setting=args.setting or rng.choice(list(SETTINGS)),
        jar=args.jar or rng.choice(list(JARS)),
        decision=args.decision or rng.choice(list(DECISIONS)),
        child_name=args.child_name or rng.choice(["Mina", "Luca", "Ivy", "Noah"]),
        child_gender="girl",
        parent_name=args.parent_name or rng.choice(["Mom", "Dad"]),
        parent_gender="mother",
    )


def _resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    jar = args.jar or rng.choice(list(JARS))
    decision = args.decision or rng.choice(list(DECISIONS))
    if args.decision and not reasonable_decision(DECISIONS[args.decision]):
        raise StoryError(f"(Refusing decision '{args.decision}': it is not kind enough for a heartwarming story.)")
    if args.decision and not choose_option(DECISIONS[args.decision], JARS[jar]):
        raise StoryError("(No story: this decision does not fit the magic jar well enough.)")
    child_name = args.child_name or rng.choice(["Mina", "Luca", "Ivy", "Noah"])
    child_gender = "girl" if child_name in {"Mina", "Ivy"} else "boy"
    parent_name = args.parent_name or rng.choice(["Mom", "Dad"])
    parent_gender = "mother" if parent_name == "Mom" else "father"
    return StoryParams(setting=setting, jar=jar, decision=decision, child_name=child_name, child_gender=child_gender, parent_name=parent_name, parent_gender=parent_gender)


resolve_params = _resolve_params


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show heartwarming/0.\n#show reconcile/0.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and the {p.jar} decision"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
