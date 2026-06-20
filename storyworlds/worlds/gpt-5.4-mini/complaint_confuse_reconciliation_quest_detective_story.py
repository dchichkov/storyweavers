#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/complaint_confuse_reconciliation_quest_detective_story.py
==========================================================================================

A standalone story world for a small detective-style domain: a child detective,
a confusing clue trail, a complaint about a missing object, a quest to recover
it, and a reconciliation at the end when everyone understands what happened.

The story engine keeps the world model small and classical:
- typed entities with physical meters and emotional memes
- causal state changes that drive the prose
- a reasonableness gate for valid story combinations
- an inline ASP twin for parity checks

This world is designed to include the seed words "complaint" and "confuse",
while keeping the style close to a gentle detective story with a quest and a
reconciliation beat.
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
CONFUSION_MAX = 3.5


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
class Scene:
    setting: str
    detail: str
    clue_place: str
    quest_goal: str
    style_word: str
    ending_image: str


@dataclass
class Complaint:
    id: str
    about: str
    complaint_line: str
    confusion_line: str
    complaint_meter: str = "complaint"
    confuse_meter: str = "confuse"


@dataclass
class Clue:
    id: str
    label: str
    hiding_place: str
    kind: str
    reveal_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestTool:
    id: str
    label: str
    phrase: str
    use_line: str
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


def _r_confuse(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["confuse"] < THRESHOLD:
            continue
        sig = ("confuse", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "detective" in world.entities:
            world.get("detective").memes["focus"] += 1
        out.append("__confuse__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    if "child" not in world.entities or "friend" not in world.entities:
        return out
    child = world.get("child")
    friend = world.get("friend")
    if child.memes["understanding"] < THRESHOLD or friend.memes["sorry"] < THRESHOLD:
        return out
    sig = ("reconcile", child.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] += 1
    friend.memes["relief"] += 1
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("confuse", "mental", _r_confuse),
    Rule("reconcile", "social", _r_reconcile),
]


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


@dataclass
class StoryParams:
    scene: str
    complaint: str
    clue: str
    tool: str
    detective: str
    detective_gender: str
    complainant: str
    complainant_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None


SCENES = {
    "library": Scene("the library", "The library was quiet, full of tall shelves and soft footsteps.", "the reading corner", "find the missing book", "detective", "The case ended with the book back on the shelf, neatly waiting."),
    "garden": Scene("the garden", "The garden had hedges, stepping stones, and a little shed at the end.", "the shed door", "find the missing key", "detective", "The case ended with the key in a hand, glinting in the sun."),
    "kitchen": Scene("the kitchen", "The kitchen smelled like toast, with drawers, chairs, and a bright table.", "the tablecloth corner", "find the missing spoon", "detective", "The case ended with the spoon beside the bowl, ready for tea."),
}

COMPLAINTS = {
    "book": Complaint("book", "book", "A complaint about a missing book came first.", "At first the shelves only made the case confuse."),
    "key": Complaint("key", "key", "A complaint about a missing key came first.", "The little clue trail made everyone confuse."),
    "spoon": Complaint("spoon", "spoon", "A complaint about a missing spoon came first.", "The strange little trail was enough to confuse even the careful eyes."),
}

CLUES = {
    "bookmark": Clue("bookmark", "bookmark", "under a chair", "paper", "The detective found a bright bookmark under a chair.", {"paper"}),
    "mudprint": Clue("mudprint", "muddy print", "by the back door", "print", "A muddy print pointed toward the back door.", {"print"}),
    "ribbon": Clue("ribbon", "ribbon", "tied to a drawer handle", "cloth", "A ribbon tied to a drawer handle gave the next clue.", {"cloth"}),
}

TOOLS = {
    "magnifier": QuestTool("magnifier", "magnifying glass", "a magnifying glass", "The detective used a magnifying glass to study the clue.", {"detective"}),
    "notebook": QuestTool("notebook", "notebook", "a little notebook", "The detective wrote the clue down in a little notebook.", {"detective"}),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Max", "Finn", "Eli"]
TRAITS = ["careful", "curious", "patient", "gentle", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for comp in COMPLAINTS:
            for clue in CLUES:
                if scene == "library" and clue != "bookmark":
                    continue
                if scene == "garden" and clue != "mudprint":
                    continue
                if scene == "kitchen" and clue != "ribbon":
                    continue
                combos.append((scene, comp, clue))
    return combos


def complaint_reasonable(complaint: Complaint, clue: Clue) -> bool:
    return complaint.about in clue.label or complaint.about in {"book", "key", "spoon"}


def world_can_reconcile(world: World) -> bool:
    return world.get("child").memes["understanding"] >= THRESHOLD and world.get("friend").memes["sorry"] >= THRESHOLD


def tell(scene: Scene, complaint: Complaint, clue: Clue, tool: QuestTool,
         detective: Entity, complainant: Entity, friend: Entity) -> World:
    world = World()
    detective = world.add(detective)
    complainant = world.add(complainant)
    friend = world.add(friend)
    world.add(Entity("room", type="room", label=scene.setting))
    world.add(Entity("clue", type="clue", label=clue.label))
    detective.role = "detective"
    complainant.role = "complainant"
    friend.role = "friend"

    detective.memes["focus"] = 1
    complainant.meters["complaint"] += 1
    complainant.meters["confuse"] += 1

    world.say(f"{detective.id} was a little detective who loved solving puzzles in {scene.setting}.")
    world.say(scene.detail)
    world.say(f"{complainant.id} had a complaint: something important was missing.")
    world.say(complaint.complaint_line)

    world.para()
    world.say(f"{friend.id} looked around, and the first clues only made the case more confusing.")
    world.say(complaint.confusion_line)
    world.say(f"{detective.id} took on the quest to {scene.quest_goal}.")

    world.para()
    world.say(f"{tool.use_line}")
    world.say(clue.reveal_line)
    complainant.memes["hope"] += 1
    complainant.meters["confuse"] += 1

    world.para()
    detective.memes["understanding"] += 1
    if complaint.about == clue.label:
        friend.memes["sorry"] += 1
        world.say(f"{friend.id} noticed the answer and smiled with relief.")
        world.say(f"{friend.id} admitted the mistake, and {complainant.id} stopped feeling upset.")
        world.say(f"The three of them talked kindly until the mix-up finally made sense.")
        world.say(f"That was the reconciliation: no one stayed blamed, and everyone could breathe again.")
    else:
        world.say(f"{detective.id} still had to think hard, but the clue trail pointed the way.")
        friend.memes["sorry"] += 1
        world.say(f"At last, {friend.id} explained the mix-up, and the upset feeling softened into reconciliation.")
    world.say(scene.ending_image)

    world.facts.update(
        scene=scene,
        complaint=complaint,
        clue=clue,
        tool=tool,
        detective=detective,
        complainant=complainant,
        friend=friend,
        resolved=world_can_reconcile(world),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the words "complaint" and "confuse".',
        f"Tell a quest story where {f['detective'].id} follows clues, fixes a complaint, and ends with reconciliation.",
        f"Write a child-friendly mystery in the style of a detective story where a small mix-up becomes clear at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    complainant = f["complainant"]
    friend = f["friend"]
    complaint = f["complaint"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {detective.id}, a little detective, and the two friends around the missing {complaint.about}. {detective.id} helps untangle the mix-up with a calm quest.",
        ),
        QAItem(
            question="Why did the case feel confusing at first?",
            answer=f"The complaint came first, but the clues did not make sense right away. That confusion made the detective slow down and look more carefully before the answer appeared.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation. {friend.id} understood the mistake, {complainant.id} felt heard, and the missing thing was found or explained so everyone could be calm again.",
        ),
    ]
    if f["resolved"]:
        qa.append(
            QAItem(
                question=f"What did {friend.id} do after the clue was found?",
                answer=f"{friend.id} apologized and explained the mix-up. That helped {complainant.id} relax, and the three of them could smile together at the end.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    tags.update(world.facts["clue"].tags)
    tags.add("detective")
    if world.facts["resolved"]:
        tags.add("reconciliation")
        tags.add("quest")
    out = []
    if "detective" in tags:
        out.append(QAItem("What does a detective do?", "A detective looks for clues and asks careful questions to solve a mystery."))
    if "quest" in tags:
        out.append(QAItem("What is a quest?", "A quest is a journey or task to find something, solve something, or help someone."))
    if "reconciliation" in tags:
        out.append(QAItem("What is reconciliation?", "Reconciliation is when people stop being upset and make peace again after a mistake or a misunderstanding."))
    if "print" in tags:
        out.append(QAItem("What can a muddy print help with?", "A muddy print can show where someone walked, so it can point a detective to the next clue."))
    if "paper" in tags:
        out.append(QAItem("What is a bookmark for?", "A bookmark helps you save your place in a book."))
    if "cloth" in tags:
        out.append(QAItem("What can a ribbon do?", "A ribbon can tie things together or mark an object so it stands out."))
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("library", "book", "bookmark", "magnifier", "Noa", "girl", "Milo", "boy", "Iris", "girl"),
    StoryParams("garden", "key", "mudprint", "notebook", "Ben", "boy", "Pia", "girl", "Theo", "boy"),
    StoryParams("kitchen", "spoon", "ribbon", "magnifier", "Lily", "girl", "Jude", "boy", "Nora", "girl"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid in COMPLAINTS:
        lines.append(asp.fact("complaint", cid))
    for kid in CLUES:
        lines.append(asp.fact("clue", kid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, K) :- scene(S), complaint(C), clue(K), compatible(S, C, K).
resolved(C, K) :- complaint(C), clue(K), complaint_about(C, A), clue_label(K, A).
"""


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
        rc = 1
        print("MISMATCH in gate:")
        print(" only in python:", sorted(py - cl))
        print(" only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, complaint=None, clue=None, tool=None, detective=None, detective_gender=None, complainant=None, complainant_gender=None, friend=None, friend_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style quest story with complaint, confuse, and reconciliation.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--complaint", choices=COMPLAINTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (args.scene is None or c[0] == args.scene)
              and (args.complaint is None or c[1] == args.complaint)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, complaint, clue = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    detective_gender = args.gender or rng.choice(["girl", "boy"])
    complainant_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    detective = args.name or rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)
    complainant = rng.choice([n for n in (GIRL_NAMES if complainant_gender == "girl" else BOY_NAMES) if n != detective])
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_gender == "girl" else BOY_NAMES) if n not in {detective, complainant}])
    return StoryParams(scene, complaint, clue, tool, detective, detective_gender, complainant, complainant_gender, friend, friend_gender)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, k) for s, c, k in (
        (s, c, k) for s in SCENES for c in COMPLAINTS for k in CLUES
    ) if complaint_reasonable(COMPLAINTS[c], CLUES[k]) and (
        (s == "library" and k == "bookmark") or (s == "garden" and k == "mudprint") or (s == "kitchen" and k == "ribbon")
    )]


def generate(params: StoryParams) -> StorySample:
    scene = SCENES[params.scene]
    complaint = COMPLAINTS[params.complaint]
    clue = CLUES[params.clue]
    tool = TOOLS[params.tool]
    world = tell(
        scene,
        complaint,
        clue,
        tool,
        Entity(params.detective, kind="character", type=params.detective_gender, role="detective"),
        Entity(params.complainant, kind="character", type=params.complainant_gender, role="complainant"),
        Entity(params.friend, kind="character", type=params.friend_gender, role="friend"),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible detective-story combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
