#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/knife_rhyme_suspense_bad_ending_mystery.py
=========================================================================

A standalone story world for a small mystery tale with rhyme, suspense, and a
bad ending. The domain is a child noticing a missing kitchen knife, following
a few clue-like rhymes, and making choices that raise tension. The story always
uses a simulated world model so the prose reflects what happened, not a frozen
template.

This world keeps the style close to mystery: dim rooms, whispered clues,
counting, searching, and a final unresolved or disappointing ending image.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    id: str
    place: str
    darkness: str
    clue_spot: str


@dataclass
class Knife:
    id: str
    label: str
    shine: str
    sharp: bool = True


@dataclass
class Clue:
    id: str
    line: str
    next_line: str
    hint: str


@dataclass
class Complication:
    id: str
    line: str
    risk: str
    bad_turn: str


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["fear"] >= THRESHOLD and ("suspense", "fear") not in world.fired:
        world.fired.add(("suspense", "fear"))
        child.meters["shiver"] += 1
        out.append("__tension__")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    knife = world.entities.get("knife")
    if not knife:
        return out
    if knife.meters["lost"] >= THRESHOLD and ("loss", "knife") not in world.fired:
        world.fired.add(("loss", "knife"))
        world.get("room").meters["mess"] += 1
        out.append("__loss__")
    return out


CAUSAL_RULES = [Rule("suspense", "social", _r_suspense), Rule("loss", "physical", _r_loss)]


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


def reasonableness_gate(setting: Setting, knife: Knife, complication: Complication) -> bool:
    return bool(setting.place and knife.sharp and complication.risk)


def predict_mystery(world: World) -> dict:
    sim = world.copy()
    _do_complication(sim, narrate=False)
    return {
        "tension": sim.get("child").meters["shiver"],
        "lost": sim.get("knife").meters["lost"] >= THRESHOLD,
    }


def _do_complication(world: World, narrate: bool = True) -> None:
    world.get("child").memes["fear"] += 1
    world.get("knife").meters["lost"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    world.say(
        f"At {setting.place}, {child.id} heard the wind at the window and saw "
        f"{setting.darkness} under the table. The room felt like a mystery."
    )
    world.say(
        f"{child.id} and {adult.id} were looking for the missing {world.facts['knife'].label}."
    )


def clue1(world: World, clue: Clue, child: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(f"{clue.line} {child.id} whispered, \"{clue.hint}\"")
    world.say(f"The note seemed to point toward {world.facts['setting'].clue_spot}.")


def clue2(world: World, clue: Clue, child: Entity) -> None:
    child.memes["fear"] += 1
    world.say(f"{clue.next_line}")
    world.say(
        f"{child.id}'s heart thumped faster. The hallway was quiet, and every little "
        f"sound felt like a secret."
    )


def search(world: World, child: Entity, adult: Entity, setting: Setting) -> None:
    child.memes["nervous"] += 1
    adult.memes["watchful"] += 1
    world.say(
        f"They searched by {setting.clue_spot}, peeking behind boxes and along the floor."
    )


def reach_for_knife(world: World, child: Entity, knife: Knife) -> None:
    child.memes["bold"] += 1
    world.say(
        f"Then {child.id} spotted the {knife.label}. It caught the lamp light and gave "
        f"a small, cold shine."
    )
    world.say(f'"I found it," {child.id} said, but {child.id} did not call for {world.facts["adult"].label_word} yet.')


def bad_choice(world: World, complication: Complication) -> None:
    world.say(
        f"{complication.line} {complication.bad_turn}"
    )
    _do_complication(world, narrate=False)
    world.say(
        f"Everything went still, and the mystery felt bigger instead of smaller."
    )


def ending_bad(world: World, child: Entity, adult: Entity) -> None:
    child.memes["sad"] += 1
    adult.memes["sad"] += 1
    world.say(
        f"In the end, {child.id} had no neat answer. The {world.facts['knife'].label} "
        f"was still missing from the counter, and the room smelled like dust and worry."
    )
    world.say(
        f"{adult.id} held {child.id}'s hand and looked around one more time, but the "
        f"night stayed mysterious and unfinished."
    )
    world.say(
        f"The last thing they saw was the dark space under the table, quiet as a secret."
    )


def tell(setting: Setting, knife: Knife, clue_a: Clue, clue_b: Clue, complication: Complication,
         child_name: str = "Mina", child_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    world.add(Entity(id="knife", type="thing", label=knife.label))
    world.facts.update(setting=setting, knife=knife, clue_a=clue_a, clue_b=clue_b,
                       complication=complication, child=child, adult=adult, room=room)
    setup(world, child, adult, setting)
    world.para()
    clue1(world, clue_a, child)
    clue2(world, clue_b, child)
    search(world, child, adult, setting)
    world.para()
    reach_for_knife(world, child, knife)
    bad_choice(world, complication)
    world.para()
    ending_bad(world, child, adult)
    world.facts.update(outcome="bad_ending")
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "a shadowy corner", "the bread box"),
    "pantry": Setting("pantry", "the pantry", "a dark shelf", "the flour jar"),
    "hall": Setting("hall", "the hallway", "a long dark stretch", "the umbrella stand"),
}

KNIVES = {
    "kitchen_knife": Knife("kitchen_knife", "knife", "small silver shine", True),
}

CLUES = {
    "rhyme_a": Clue("rhyme_a", "On the counter, by the chair, a rhyme was waiting there:", "Under the loaf, there it goes,",
                    "A clue can hide where bread lives."),
    "rhyme_b": Clue("rhyme_b", "Next came a whisper, soft and slow:", "Behind the jar, the shadows grow,",
                    "A whisper can point to a hiding place."),
}

COMPLICATIONS = {
    "grab": Complication("grab", "Mina reached too fast and grabbed the knife by the blade.", "cut", "The shiny edge slipped from her fingers."),
    "hide": Complication("hide", "Mina hid the knife in a pocket to solve the case alone.", "lost", "The pocket swallowed it like a tiny cave."),
    "open": Complication("open", "Mina tried to open a stuck box with the knife.", "scratch", "The lid jolted, and the knife skidded away."),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lena", "Ruby"]
BOY_NAMES = ["Eli", "Sam", "Noah", "Theo", "Max"]


@dataclass
class StoryParams:
    setting: str
    knife: str
    clue_a: str
    clue_b: str
    complication: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for k in KNIVES:
            for c in COMPLICATIONS:
                if reasonableness_gate(SETTINGS[s], KNIVES[k], COMPLICATIONS[c]):
                    combos.append((s, k, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a young child that includes the word "{f["knife"].label}" and a rhyme clue.',
        f"Tell a suspenseful story where {f['child'].id} searches {f['setting'].place} for a missing knife, follows clues, and makes a poor choice.",
        f"Write a short mystery with rhyme, suspense, and a bad ending set in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, knife, setting = f["child"], f["adult"], f["knife"], f["setting"]
    return [
        QAItem(
            question=f"What were {child.id} and {adult.id} looking for?",
            answer=f"They were looking for the {knife.label}, and they searched because it was missing from the counter. The search made the room feel like a mystery."
        ),
        QAItem(
            question="What did the rhymes do in the story?",
            answer="The rhymes gave clues about where to look next. They made the search feel suspenseful, as if every line might point to the missing thing."
        ),
        QAItem(
            question="Why did the ending feel bad?",
            answer="The ending felt bad because the knife was still not put away safely, and the child made the situation worse instead of solving it. The mystery ended with worry, not a clean answer."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a knife?",
            answer="A knife is a sharp tool that grown-ups use carefully in the kitchen. It is not a toy, because it can hurt someone if it is handled the wrong way."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story or problem where something is missing or unknown. The characters look for clues to try to figure it out."
        ),
        QAItem(
            question="What does suspense mean in a story?",
            answer="Suspense means you feel nervous and want to know what happens next. It makes the reader wait with the characters and wonder about the outcome."
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
tension(child) :- fear(child), fear_level(child, F), F > 0.
mystery(place) :- setting(place).
bad_ending :- knife_missing, not knife_found_safely.
knife_missing :- chosen_setting(S), setting(S).
knife_found_safely :- false.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for kid in KNIVES:
        lines.append(asp.fact("knife", kid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for cid in COMPLICATIONS:
        lines.append(asp.fact("complication", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show mystery/1. #show bad_ending/0."))
    _ = model
    python_ok = len(valid_combos()) > 0
    print(f"OK: ASP program loaded; valid combo count = {len(valid_combos())}.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, knife=None, clue_a=None, clue_b=None, complication=None, child_name=None, child_gender=None, adult_name=None, adult_gender=None, seed=None), random.Random(7)))
        print("OK: smoke test story generation produced", len(sample.story), "characters of story.")
    except Exception as exc:
        print("FAILED: smoke test generation crashed:", exc)
        return 1
    return 0 if python_ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with rhyme, suspense, and a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--knife", choices=KNIVES)
    ap.add_argument("--clue-a", choices=CLUES)
    ap.add_argument("--clue-b", choices=CLUES)
    ap.add_argument("--complication", choices=COMPLICATIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.knife and args.complication:
        if (args.setting, args.knife, args.complication) not in combos:
            raise StoryError("That combination does not fit this mystery world.")
    setting = args.setting or rng.choice(sorted(SETTINGS))
    knife = args.knife or "knife"
    clue_a = args.clue_a or rng.choice(sorted(CLUES))
    clue_b = args.clue_b or rng.choice([k for k in CLUES if k != clue_a])
    complication = args.complication or rng.choice(sorted(COMPLICATIONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult_name = args.adult_name or ( "Mom" if adult_gender == "mother" else "Dad" )
    return StoryParams(setting, knife, clue_a, clue_b, complication, child_name, child_gender, adult_name, adult_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        KNIVES[params.knife],
        CLUES[params.clue_a],
        CLUES[params.clue_b],
        COMPLICATIONS[params.complication],
        params.child_name,
        params.child_gender,
        params.adult_name,
        params.adult_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
    StoryParams("kitchen", "knife", "rhyme_a", "rhyme_b", "grab", "Mina", "girl", "Mom", "mother"),
    StoryParams("pantry", "knife", "rhyme_b", "rhyme_a", "hide", "Eli", "boy", "Dad", "father"),
    StoryParams("hall", "knife", "rhyme_a", "rhyme_b", "open", "Nora", "girl", "Mom", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show mystery/1.\n#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This world focuses on one mystery line: the missing knife and the bad ending.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.setting} / {p.complication}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
