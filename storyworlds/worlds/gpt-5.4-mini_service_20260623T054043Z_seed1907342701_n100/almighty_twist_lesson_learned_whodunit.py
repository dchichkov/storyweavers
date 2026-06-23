#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/almighty_twist_lesson_learned_whodunit.py
=============================================================================================================

A standalone story world for a small whodunit-style mystery with a twist and a
lesson learned. The setting is child-facing, concrete, and state-driven: a tiny
problem appears, clues are gathered, the likely culprit is ruled out, a twist
reveals what really happened, and the ending image shows what changed.

The story always includes the word "almighty" and keeps a whodunit tone without
becoming dark or scary.
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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue: str
    twist: str
    lesson: str
    evidence: str
    sound: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    excuse: str
    tell: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dirty(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["spilled"] < THRESHOLD:
            continue
        sig = ("dirty", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["mess"] += 1
        out.append(f"A little mess showed up near the clue.")
    return out


CAUSAL_RULES = [Rule("dirty", "physical", _r_dirty)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_mystery(setting: Setting, mystery: Mystery, suspect: Suspect, tool: Tool) -> bool:
    return mystery.id in setting.affords and mystery.id in suspect.tags and mystery.id in tool.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for sus_id, suspect in SUSPECTS.items():
                for tool_id, tool in TOOLS.items():
                    if valid_mystery(setting, mystery, suspect, tool):
                        combos.append((sid, mid, sus_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    mystery: str
    suspect: str
    tool: str
    detective: str = "Nina"
    detective_type: str = "girl"
    helper: str = "Milo"
    helper_type: str = "boy"
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", mood="bright", affords={"spilled_jam", "missing_key"}),
    "garden": Setting(place="the garden", mood="windy", affords={"missing_ball", "spilled_jam"}),
    "classroom": Setting(place="the classroom", mood="quiet", affords={"missing_chalk", "spilled_jam"}),
    "workshop": Setting(place="the workshop", mood="busy", affords={"missing_key", "missing_bell"}),
}

MYSTERIES = {
    "spilled_jam": Mystery(
        id="spilled_jam", label="the jam jar", phrase="a jar of jam",
        clue="sticky red tracks", twist="the tracks led to a spoon, not a thief",
        lesson="ask before borrowing", evidence="sticky", sound="plip",
        risk="the floor could get slippery", tags={"spilled_jam"},
    ),
    "missing_key": Mystery(
        id="missing_key", label="the silver key", phrase="a silver key",
        clue="a shiny glint", twist="the key was tucked under a note",
        lesson="look twice before worrying", evidence="shiny", sound="clink",
        risk="someone needed the key soon", tags={"missing_key"},
    ),
    "missing_ball": Mystery(
        id="missing_ball", label="the red ball", phrase="a red ball",
        clue="a round shadow", twist="the ball rolled behind a bucket",
        lesson="slow down and follow clues", evidence="round", sound="thump",
        risk="a game had paused", tags={"missing_ball"},
    ),
    "missing_chalk": Mystery(
        id="missing_chalk", label="the chalk box", phrase="a box of chalk",
        clue="white dust on a sleeve", twist="the chalk was moved for art time",
        lesson="check the art shelf first", evidence="dusty", sound="scrape",
        risk="the board could not be used yet", tags={"missing_chalk"},
    ),
    "missing_bell": Mystery(
        id="missing_bell", label="the little bell", phrase="a little bell",
        clue="a soft ring from a drawer", twist="the bell was wrapped in cloth",
        lesson="listen carefully for small sounds", evidence="ringing", sound="ting",
        risk="the helper needed it for a game", tags={"missing_bell"},
    ),
}

SUSPECTS = {
    "cat": Suspect(id="cat", label="the cat", type="cat", excuse="was napping",
                   tell="had jam on its whiskers", tags={"spilled_jam", "missing_key", "missing_ball"}),
    "dog": Suspect(id="dog", label="the dog", type="dog", excuse="was chasing a leaf",
                   tell="had a muddy pawprint", tags={"missing_ball", "spilled_jam"}),
    "brother": Suspect(id="brother", label="the brother", type="boy", excuse="was building a fort",
                       tell="had chalk on his sleeve", tags={"missing_chalk", "missing_bell", "missing_key"}),
    "grandma": Suspect(id="grandma", label="grandma", type="woman", excuse="was reading",
                       tell="had a note in her apron pocket", tags={"missing_key", "missing_chalk", "missing_bell"}),
}

TOOLS = {
    "magnifier": Tool(id="magnifier", label="magnifying glass", phrase="a magnifying glass",
                      helps="made tiny clues easier to see", tags={"spilled_jam", "missing_key", "missing_ball", "missing_chalk", "missing_bell"}),
    "lamp": Tool(id="lamp", label="desk lamp", phrase="a desk lamp",
                 helps="showed shiny things and tiny dust", tags={"missing_key", "missing_chalk", "missing_bell"}),
    "napkin": Tool(id="napkin", label="clean napkin", phrase="a clean napkin",
                   helps="wiped sticky clues carefully", tags={"spilled_jam"}),
    "shoe": Tool(id="shoe", label="small shoe", phrase="a small shoe",
                 helps="measured footprints and little tracks", tags={"missing_ball", "missing_key"}),
}

GIRL_NAMES = ["Nina", "Maya", "Luna", "Ivy", "Ada", "Mina"]
BOY_NAMES = ["Milo", "Theo", "Owen", "Leo", "Ezra", "Finn"]


def aspiration_text(mystery: Mystery) -> str:
    return f"the mighty little word almighty felt like a clue all by itself"


def tell(setting: Setting, mystery: Mystery, suspect: Suspect, tool: Tool,
         detective_name: str, detective_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, label=detective_name, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name, role="helper"))
    culprit = world.add(Entity(id="suspect", kind="character", type=suspect.type, label=suspect.label, role="suspect", attrs={"excuse": suspect.excuse, "tell": suspect.tell}))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.label, phrase=mystery.phrase))
    world.add(Entity(id="tool", type="thing", label=tool.label, phrase=tool.phrase))
    world.facts.update(detective=detective, helper=helper, culprit=culprit, mystery=mystery, suspect=suspect, tool=tool, setting=setting)

    detective.memes["curiosity"] += 1
    helper.memes["help"] += 1
    world.say(f"{detective.id} and {helper.id} were in {setting.place}, where {mystery.label_word if hasattr(mystery, 'label_word') else mystery.label} looked wrong.")
    world.say(f"{detective.id} whispered that the case felt {aspiration_text(mystery)}.")
    world.para()
    world.say(f"Something was off near {mystery.label}. The first clue was {mystery.clue}.")
    clue.meters["spilled"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{helper.id} pointed at {mystery.evidence} marks, while {detective.id} checked every corner.")
    if "jam" in mystery.id:
        world.say(f"The trail seemed to blame {suspect.label}, but the shiny trail ended at a spoon.")
    elif "missing" in mystery.id:
        world.say(f"The trail seemed to blame {suspect.label}, but the real clue was hidden nearby.")
    world.para()
    world.say(f"Then came the twist: {mystery.twist}.")
    world.say(f"{suspect.label.capitalize()} had only {suspect.excuse}, and {suspect.tell}.")
    world.para()
    world.say(f"In the end, {detective.id} fixed the problem and learned that {mystery.lesson}.")
    world.say(f"The final picture was simple: {mystery.label} was back where it belonged, and the room looked calm again.")
    world.facts.update(solved=True, twist=True, ending="restored")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    suspect: Suspect = f["suspect"]
    return [
        f'Write a whodunit for a small child in {setting.place} about {mystery.phrase}. Include the word "almighty".',
        f"Tell a gentle mystery story with a twist where {suspect.label} seems suspicious, but the real answer is simpler.",
        f"Write a short detective story for kids that ends with a lesson learned and a clue revealing who handled {mystery.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    helper: Entity = f["helper"]
    suspect: Suspect = f["suspect"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who solved the mystery in {setting.place}?",
            answer=f"{detective.id} solved it with help from {helper.id}. They followed the clues instead of guessing too fast.",
        ),
        QAItem(
            question=f"What seemed suspicious about {suspect.label} at first?",
            answer=f"{suspect.label} looked like the likely answer because of {suspect.tell}. That made the first guess feel convincing.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {mystery.twist}. The clue turned the guess around and showed the first idea was not right.",
        ),
        QAItem(
            question=f"What lesson did the detective learn?",
            answer=f"{mystery.lesson.capitalize()}. The ending proves it because the mystery was solved calmly and the place was put right again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    out = [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps you figure out what happened.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks at clues, asks careful questions, and tries to solve a mystery.",
        ),
    ]
    if "jam" in mystery.id:
        out.append(QAItem(
            question="Why can jam be messy?",
            answer="Jam is sticky, so it can smear on the floor or hands and make a mess very quickly.",
        ))
    if "missing" in mystery.id:
        out.append(QAItem(
            question="What should you do when something is missing?",
            answer="Look carefully, check the nearby places, and follow the clues before you worry.",
        ))
    return out


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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, C, T) :- setting(S), mystery(M), suspect(C), tool(T),
                     setting_affords(S, M), suspect_tag(C, M), tool_tag(T, M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("setting_affords", sid, m))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
    for cid, c in SUSPECTS.items():
        lines.append(asp.fact("suspect", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("suspect_tag", cid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tool_tag", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    print("OK: ASP and Python match.")
    # smoke test
    sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, suspect=None, tool=None, detective=None, helper=None, seed=None), random.Random(7)))
    if not sample.story.strip():
        print("MISMATCH: generated story was empty.")
        return 1
    print("OK: story generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit story world with a twist and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
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
              and (args.suspect is None or c[2] == args.suspect)
              and (args.tool is None or c[3] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, suspect, tool = rng.choice(sorted(combos))
    det = args.detective or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != det])
    return StoryParams(setting=setting, mystery=mystery, suspect=suspect, tool=tool, detective=det, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    mystery = MYSTERIES.get(params.mystery)
    suspect = SUSPECTS.get(params.suspect)
    tool = TOOLS.get(params.tool)
    if not all([setting, mystery, suspect, tool]):
        raise StoryError("Invalid params.")
    if not valid_mystery(setting, mystery, suspect, tool):
        raise StoryError("This combination does not make a reasonable mystery.")
    world = tell(setting, mystery, suspect, tool, params.detective, "girl" if params.detective in GIRL_NAMES else "boy", params.helper, "girl" if params.helper in GIRL_NAMES else "boy")
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
    StoryParams(setting="kitchen", mystery="spilled_jam", suspect="cat", tool="napkin", detective="Nina", helper="Milo"),
    StoryParams(setting="workshop", mystery="missing_key", suspect="grandma", tool="lamp", detective="Ada", helper="Finn"),
    StoryParams(setting="garden", mystery="missing_ball", suspect="dog", tool="shoe", detective="Maya", helper="Leo"),
    StoryParams(setting="classroom", mystery="missing_chalk", suspect="brother", tool="magnifier", detective="Ivy", helper="Owen"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
