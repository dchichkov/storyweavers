#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chicory_inner_monologue_kindness_reconciliation_folk_tale.py
===========================================================================================

A standalone storyworld about a small folk-tale moment: a child or villager
walks into a meadow, notices wild chicory, feels a hurt or misunderstanding,
keeps an inner monologue, answers with kindness, and ends in reconciliation.

The world is intentionally small and classical: a few typed entities, meters for
physical state, memes for emotional state, a short causal engine, a reasonableness
gate, and an inline ASP twin for parity checks.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class PersonCfg:
    id: str
    type: str
    role: str
    trait: str


@dataclass
class HerbCfg:
    id: str
    label: str
    is_chicory: bool = False
    edible: bool = True
    flower: str = "blue flowers"


@dataclass
class ConflictCfg:
    id: str
    cause: str
    hurt_word: str
    inner_monologue: str
    kindness_action: str
    reconciliation_line: str
    apology_line: str
    resolution_image: str


class World:
    def __init__(self) -> None:
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["kindness"] < THRESHOLD:
            continue
        sig = ("soften", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["warmth"] += 1
        out.append("")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("child")
    b = world.get("neighbor")
    if a.memes["kindness"] >= THRESHOLD and b.memes["kindness_received"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["peace"] += 1
            b.memes["peace"] += 1
    return out


CAUSAL_RULES = [Rule("soften", _r_soften), Rule("reconcile", _r_reconcile)]


SETTINGS = {
    "meadow": "the meadow beyond the hedge",
    "lane": "the narrow lane by the cottages",
    "garden": "the garden behind the mill",
}

PEOPLE = {
    "child": PersonCfg("child", "girl", "wanderer", "thoughtful"),
    "neighbor": PersonCfg("neighbor", "boy", "neighbor", "proud"),
    "mother": PersonCfg("mother", "woman", "parent", "kind"),
    "father": PersonCfg("father", "man", "parent", "kind"),
}

HERBS = {
    "chicory": HerbCfg("chicory", "wild chicory", True, True, "blue little flowers"),
    "daisy": HerbCfg("daisy", "white daisies", False, True, "small white stars"),
    "thistle": HerbCfg("thistle", "thistles", False, False, "spiky heads"),
}

CONFLICTS = {
    "glance": ConflictCfg(
        "glance",
        "a sharp glance over a basket of roots",
        "stung",
        "Why was the neighbor looking so cross? Had the child done wrong by picking the blue flowers? The child could almost hear the question fluttering inside.",
        "offered a handful of clean water and the best roots from the basket",
        "The neighbor's face softened, and the child felt the little knot in the chest loosen.",
        "I did not mean to wrong you; I only wanted to help.",
        "By dusk, they were laughing beside the hearth, the chicory laid gently in a bowl between them.",
    ),
    "teasing": ConflictCfg(
        "teasing",
        "a teasing word about muddy shoes",
        "burned",
        "Was the neighbor laughing at the child? Perhaps not. Yet the words still pricked like a briar.",
        "set the basket down and brushed the mud from the step",
        "The neighbor looked ashamed, and the child felt the hard place inside begin to melt.",
        "I spoke too sharply; I am sorry for my tongue.",
        "In the end, they shared bread and chicory tea, and the day ended sweetly.",
    ),
    "misunderstanding": ConflictCfg(
        "misunderstanding",
        "a misunderstood basket of chicory roots",
        "worried",
        "Maybe the neighbor thought the child had taken the roots without asking. The thought made the child breathe small and careful.",
        "held out the basket with both hands",
        "The neighbor nodded, and the air between them grew light again.",
        "I should have asked before I reached for it.",
        "Soon they were both smiling, and the chicory stood in a jar by the window.",
    ),
}


class StoryParams:
    def __init__(
        self,
        setting: str,
        person: str,
        herb: str,
        conflict: str,
        seed: Optional[int] = None,
    ) -> None:
        self.setting = setting
        self.person = person
        self.herb = herb
        self.conflict = conflict
        self.seed = seed


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld with chicory, kindness, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--person", choices=PEOPLE)
    ap.add_argument("--herb", choices=HERBS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for person in PEOPLE:
            for herb in HERBS:
                for conflict in CONFLICTS:
                    if herb == "chicory":
                        combos.append((setting, person, herb, conflict))
    return combos


def explain_rejection(herb: str) -> str:
    return "(No story: this tale needs chicory, so the herb must be chicory.)" if herb != "chicory" else "(No story: invalid combination.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.herb and args.herb != "chicory":
        raise StoryError(explain_rejection(args.herb))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.person is None or c[1] == args.person)
              and (args.herb is None or c[2] == args.herb)
              and (args.conflict is None or c[3] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, person, herb, conflict = rng.choice(sorted(combos))
    return StoryParams(setting, person, herb, conflict)


def tell(params: StoryParams) -> World:
    cfg_person = PEOPLE[params.person]
    cfg_herb = HERBS[params.herb]
    cfg_conflict = CONFLICTS[params.conflict]
    world = World()
    child = world.add(Entity("child", kind="character", type=cfg_person.type, role="wanderer", traits=[cfg_person.trait]))
    neighbor = world.add(Entity("neighbor", kind="character", type="boy", role="neighbor", traits=["proud"]))
    herb = world.add(Entity("herb", kind="thing", type="plant", label=cfg_herb.label, attrs={"flower": cfg_herb.flower}))
    child.memes["curiosity"] += 1
    world.say(f"Once, in {SETTINGS[params.setting]}, there lived a small {child.type} who walked where the grasses bowed.")
    world.say(f"The child noticed {cfg_herb.label}, its {cfg_herb.flower}, and thought the plant looked like a gift from the road itself.")
    world.para()
    world.say(f"At the neighbor's gate, a small trouble waited: {cfg_conflict.cause}.")
    world.say(f"The child stood still and listened to {child.pronoun('possessive')} own heart. {cfg_conflict.inner_monologue}")
    child.memes["hurt"] += 1
    neighbor.memes["pride"] += 1
    world.say(f"Then the child chose kindness and {cfg_conflict.kindness_action}.")
    child.memes["kindness"] += 1
    neighbor.memes["kindness_received"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(cfg_conflict.apology_line)
    child.memes["reconciliation"] += 1
    neighbor.memes["reconciliation"] += 1
    world.say(cfg_conflict.reconciliation_line)
    world.say(cfg_conflict.resolution_image)
    world.facts.update(setting=params.setting, person=params.person, herb=params.herb, conflict=params.conflict,
                       child=child, neighbor=neighbor, herb_ent=herb, conflict_cfg=cfg_conflict)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story that includes the word "{f["herb"]}" and ends with reconciliation.',
        f"Tell a small old-fashioned story where a wandering child notices {HERBS[f['herb']].label}, thinks quietly to {world.get('child').pronoun('object')}self, and responds with kindness.",
        "Write a gentle folk tale about a misunderstanding, a kind deed, and two people becoming friends again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    neighbor = f["neighbor"]
    cfg = f["conflict_cfg"]
    herb = HERBS[f["herb"]]
    qa = [
        QAItem(
            question="What did the child notice in the meadow?",
            answer=f"The child noticed {herb.label}. Its {herb.flower} made it look small and bright in the grass.",
        ),
        QAItem(
            question="What was the child thinking during the quiet moment?",
            answer=f"The child was worried about the trouble at the gate and wondered if {child.pronoun('possessive')} own actions had caused it. That inner monologue helped the child slow down instead of answering in anger.",
        ),
        QAItem(
            question="How did the child respond?",
            answer=f"The child chose kindness and {cfg.kindness_action}. Because of that, the neighbor softened too, and the two of them found their way back to peace.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended in reconciliation: the apology was spoken, the hurt was eased, and the day finished with {cfg.resolution_image.lower()}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    herb = HERBS[world.facts["herb"]]
    return [
        QAItem(
            question="What is chicory?",
            answer="Chicory is a wild plant with bright blue flowers. People can use its roots or leaves in simple country ways.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone chooses gentle, helpful actions even when the moment feels tense. It often helps other people feel safe again.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again. They may apologize, listen, and choose to be friendly once more.",
        ),
        QAItem(
            question=f"Why might {herb.label} be special in a folk tale?",
            answer="Wild plants often feel important in folk tales because they grow by roads and hedges, where ordinary people can find them. A simple plant can become part of a lesson or a shared meal.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, H, C) :- setting(S), person(P), herb(H), conflict(C), chicory(H).
kindness(H) :- herb(H), chicory(H).
reconcile(C) :- conflict(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in PEOPLE:
        lines.append(asp.fact("person", p))
    for h, cfg in HERBS.items():
        lines.append(asp.fact("herb", h))
        if cfg.is_chicory:
            lines.append(asp.fact("chicory", h))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


CURATED = [
    StoryParams("meadow", "child", "chicory", "misunderstanding"),
    StoryParams("lane", "neighbor", "chicory", "glance"),
    StoryParams("garden", "child", "chicory", "teasing"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.setting} | {p.person} | chicory | {p.conflict}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
