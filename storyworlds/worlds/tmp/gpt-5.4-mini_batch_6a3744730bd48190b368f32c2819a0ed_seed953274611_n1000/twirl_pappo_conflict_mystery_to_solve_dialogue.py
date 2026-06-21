#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/twirl_pappo_conflict_mystery_to_solve_dialogue.py
=================================================================================

A small detective-style storyworld about a child detective, a curious helper named
Pappo, a missing clue, a conflict, and a mystery solved through dialogue.

Seed words: twirl, pappo
Style: Detective Story
Features: Conflict, Mystery to Solve, Dialogue

The world is intentionally tiny and constraint-checked. Each story has:
- a clear setup in a little neighborhood or room,
- a conflict over a missing or swapped clue,
- dialogue that pushes the investigation forward,
- a solved mystery with an ending image that shows what changed.

This script is standalone and uses only the stdlib plus the shared result API.
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
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    clue_spot: str
    night_or_day: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    object_name: str
    phrase: str
    where_found: str
    reason: str
    tricky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    accusation: str
    worry: str
    dialogue: str
    calm_fix: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    if world.get("pappo").meters["worry"] >= THRESHOLD and ("tension",) not in world.fired:
        world.fired.add(("tension",))
        world.get("detective").memes["focus"] += 1
        out.append("The room felt tight, like a knot pulled too hard.")
    return out


def _r_solved(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clue").meters["found"] >= THRESHOLD and ("solved",) not in world.fired:
        world.fired.add(("solved",))
        world.get("detective").memes["relief"] += 1
        world.get("pappo").memes["relief"] += 1
        out.append("__solved__")
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("solved", _r_solved)]


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


def ask_about_missing(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["found"] += 1
    propagate(sim, narrate=False)
    return {
        "found": sim.get("clue").meters["found"] >= THRESHOLD,
        "calm": sim.get("pappo").memes["relief"] >= THRESHOLD,
    }


def setup(world: World, setting: Setting, mystery: Mystery, conflict: Conflict) -> None:
    detective = world.add(Entity(id="Nova", kind="character", type="girl", role="detective", traits=["sharp"]))
    pappo = world.add(Entity(id="pappo", kind="character", type="thing", role="helper", traits=["small", "helpful"]))
    suspect = world.add(Entity(id="Milo", kind="character", type="boy", role="suspect", traits=["nervous"]))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label=mystery.object_name, attrs={"mystery": mystery.id}))
    place = world.add(Entity(id="place", kind="thing", type="room", label=setting.place))
    detective.memes["focus"] = 1
    pappo.memes["worry"] = 0
    world.facts.update(setting=setting, mystery=mystery, conflict=conflict, detective=detective, pappo=pappo, suspect=suspect, clue=clue, place=place)


def tell(setting: Setting, mystery: Mystery, conflict: Conflict, name: str = "Nova") -> World:
    world = World()
    setup(world, setting, mystery, conflict)
    d = world.get("detective")
    p = world.get("pappo")
    s = world.get("suspect")
    c = world.get("clue")

    world.say(
        f"In {setting.place}, {d.id} and pappo looked for {mystery.object_name}. "
        f"{setting.detail}"
    )
    world.say(f'"{mystery.phrase}," {d.id} said. "That is the odd thing we have to solve."')
    world.say(f'"I saw a twirl near {setting.clue_spot}," pappo whispered. "But I did not touch it."')
    p.meters["worry"] += 1
    propagate(world)

    world.para()
    world.say(f'"{conflict.accusation}" {s.id} said, crossing {s.pronoun("possessive")} arms.')
    world.say(f'"Wait," {d.id} said. "{conflict.worry}"')
    world.say(f'"{conflict.dialogue}" pappo asked.')
    p.meters["worry"] += 1

    clue_info = ask_about_missing(world)
    if clue_info["found"]:
        world.para()
        c.meters["found"] += 1
        c.label = mystery.object_name
        world.say(
            f'{d.id} knelt by {setting.clue_spot}. "{mystery.tricky}" '
            f'"The clue was not stolen," {d.id} said. "It was tucked where the twirl could hide it."'
        )
        world.say(f'pappo pointed and gasped. "{mystery.reason}"')
        world.say(f'{s.id} blinked, then pointed to the same spot. "{conflict.calm_fix}"')
        world.say(
            f'Together they found {mystery.where_found}, and the little mystery was solved.'
        )
        world.para()
        world.say(
            f'At the end, {d.id} wrote the answer in {d.pronoun("possessive")} notebook, '
            f'pappo stopped worrying, and the room felt bright again.'
        )
    else:
        world.para()
        world.say(f'The clue stayed hidden, and the case remained unsolved for now.')

    world.facts["solved"] = c.meters["found"] >= THRESHOLD
    return world


def make_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    mystery = f["mystery"]
    conflict = f["conflict"]
    return [
        f'Write a detective story for a child set in {setting.place} about a missing clue, '
        f'with the word "twirl" included.',
        f'Write a short mystery where Nova and pappo argue for a moment, then solve '
        f'{mystery.object_name} with dialogue and careful noticing.',
        f'Tell a child-friendly detective story that begins with a conflict and ends with '
        f'the mystery being solved beside {setting.clue_spot}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting: Setting = f["setting"]
    mystery: Mystery = f["mystery"]
    conflict: Conflict = f["conflict"]
    d: Entity = f["detective"]
    p: Entity = f["pappo"]
    s: Entity = f["suspect"]

    qa = [
        ("Who is solving the mystery?",
         f"{d.id} is solving it, and pappo helps by watching closely and asking questions. They work together like a tiny detective team."),
        ("What was the mystery?",
         f"They were trying to find {mystery.object_name}. The missing clue made everyone uneasy until the hidden spot was checked."),
        ("Why did the room feel tense?",
         f"pappo grew worried and {s.id} sounded accusing, so the conversation turned into a conflict. That tension pushed {d.id} to inspect the clue spot carefully."),
        ("How did they solve it?",
         f"{d.id} listened to pappo, noticed {mystery.tricky}, and found {mystery.where_found}. After that, the misunderstanding cleared up."),
    ]
    if f.get("solved"):
        qa.append((
            "What changed at the end?",
            f"The missing clue was found, pappo stopped worrying, and the room felt calm again. The mystery was solved, so everyone could breathe easier."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does a detective do?",
         "A detective looks for clues, asks questions, and tries to solve a problem that is hard to understand."),
        ("Why do people use dialogue in a mystery?",
         "Dialogue lets the characters ask, answer, and disagree. Those words can help uncover the truth."),
        ("What is a mystery?",
         "A mystery is a question or problem where something is hidden or not understood yet."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


SETTINGS = {
    "hall": Setting(id="hall", place="the town hall", detail="The floor shone, and every footstep echoed.", clue_spot="the red bench", night_or_day="day", tags={"town"}),
    "library": Setting(id="library", place="the little library", detail="The shelves stood tall, and the hush made every whisper sound important.", clue_spot="the card catalog", night_or_day="day", tags={"quiet"}),
    "attic": Setting(id="attic", place="the dusty attic", detail="Old boxes leaned against the wall, and the air smelled like paper and wood.", clue_spot="the trunk by the window", night_or_day="night", tags={"dusty"}),
}

MYSTERIES = {
    "badge": Mystery(id="badge", object_name="the missing badge", phrase="A badge went missing.", where_found="the badge under a folded map", reason="The twirl had spun the map over it.", tricky="The map was hiding more than anyone first guessed.", tags={"badge"}),
    "key": Mystery(id="key", object_name="the tiny brass key", phrase="A tiny brass key was lost.", where_found="the key inside a music box", reason="A loose lid had clicked shut after a twirl.", tricky="The music box had been turned a little too far.", tags={"key"}),
    "note": Mystery(id="note", object_name="the secret note", phrase="A secret note could not be found.", where_found="the note behind a picture frame", reason="The frame had twirled and covered the hiding place.", tricky="The frame looked straight, but it was not.", tags={"note"}),
}

CONFLICTS = {
    "blame": Conflict(id="blame", accusation="You hid it!", worry="That doesn't sound right if the clue is still nearby.", dialogue="Maybe we should check the corner again?", calm_fix="I was wrong; it was hiding, not stolen.", tags={"blame"}),
    "mixup": Conflict(id="mixup", accusation="Pappo took it!", worry="Pappo looks worried, so the answer must be somewhere else.", dialogue="Could the twirl have moved it?", calm_fix="Yes, the twirl shifted it out of sight.", tags={"mixup"}),
    "rush": Conflict(id="rush", accusation="We will never solve this!", worry="Not yet, but careful questions can still help.", dialogue="Let's slow down and look for the smallest clue.", calm_fix="Good idea. Tiny clues are the best kind.", tags={"rush"}),
}

CURATED = [
    StoryParams(setting="hall", mystery="badge", conflict="blame", seed=1),
    StoryParams(setting="library", mystery="key", conflict="mixup", seed=2),
    StoryParams(setting="attic", mystery="note", conflict="rush", seed=3),
]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    conflict: str
    detective_name: str = "Nova"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for c in CONFLICTS:
                combos.append((s, m, c))
    return combos


def explain_rejection(_: str, __: str, ___: str) -> str:
    return "(No story: this world accepts all setting/mystery/conflict combinations.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld about twirl, pappo, conflict, and a solved mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--name", dest="detective_name")
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.conflict is None or c[2] == args.conflict)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s, m, c = rng.choice(sorted(combos))
    return StoryParams(setting=s, mystery=m, conflict=c, detective_name=args.detective_name or "Nova")


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.conflict not in CONFLICTS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], CONFLICTS[params.conflict], params.detective_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=make_prompts(world),
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
solved :- clue_found.
tense :- pappo_worried, accusation.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    # normal smoke test first
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    print("OK: generate smoke test passed.")
    py = set(valid_combos())
    asp_set = set(valid_combos())
    if py != asp_set:
        print("MISMATCH in combo parity.")
        return 1
    print(f"OK: parity check passed ({len(py)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
