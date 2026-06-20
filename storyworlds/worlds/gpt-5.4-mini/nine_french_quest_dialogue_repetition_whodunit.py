#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nine_french_quest_dialogue_repetition_whodunit.py
=================================================================================

A standalone story world for a tiny whodunit with a quest shape, repeated
dialogue clues, and a child-facing mystery about missing French treats.

The seed words are honored directly in the premise:
- nine
- french

The narrative instruments are:
- Quest: the detective searches room by room
- Dialogue: the clue is spoken in short exchanges
- Repetition: a repeated phrase betrays the culprit
- Whodunit: the ending reveals who took the treats and why

This is a small, constraint-checked simulation. The story changes because world
state changes: suspicion rises, clues are found, the culprit's nerves wobble,
and the ending resolves the mystery.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    rooms: list[str]
    mood: str


@dataclass
class Quest:
    id: str
    start_room: str
    search_order: list[str]
    clue_phrase: str
    final_place: str
    ending_image: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    speech_style: str
    has_reason: bool = True


@dataclass
class MissingThing:
    id: str
    label: str
    count: int
    adjective: str
    container: str
    scent: str


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


SETTINGS = {
    "kitchen": Setting("kitchen", "the bright kitchen", ["kitchen", "pantry", "hall", "garden"], "busy"),
    "bakery": Setting("bakery", "the little bakery", ["counter", "shelf", "back room", "alley"], "warm"),
    "library": Setting("library", "the quiet library", ["desk", "stacks", "hall", "reading nook"], "soft"),
}

QUESTS = {
    "missing_treats": Quest(
        "missing_treats",
        "kitchen",
        ["kitchen", "pantry", "hall", "garden"],
        "nine french treats",
        "garden",
        "In the end, the nine treats were back in the basket, and the basket sat safe on the table again.",
    ),
    "missing_cards": Quest(
        "missing_cards",
        "library",
        ["desk", "stacks", "hall", "reading nook"],
        "nine french picture cards",
        "reading nook",
        "In the end, the nine cards were stacked neatly, and the clue book was shut with a tiny snap.",
    ),
    "missing_roses": Quest(
        "missing_roses",
        "bakery",
        ["counter", "shelf", "back room", "alley"],
        "nine french sugar roses",
        "back room",
        "In the end, the nine roses were found in a tray, and the tray was carried home with care.",
    ),
}

SUSPECTS = {
    "cat": Suspect("cat", "the cat", "cat", "wanted a snack", "mewled"),
    "brother": Suspect("brother", "the brother", "boy", "wanted to hide the treats for a joke", "said"),
    "aunt": Suspect("auntie", "the aunt", "aunt", "was making tea and forgot to tell anyone", "said"),
}

MISSING = {
    "treats": MissingThing("treats", "treats", 9, "french", "basket", "sweet"),
    "cards": MissingThing("cards", "cards", 9, "french", "box", "paper"),
    "roses": MissingThing("roses", "roses", 9, "french", "tray", "sugar"),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Max", "Noah", "Theo", "Finn", "Sam"]


def story_gate(quest: Quest, missing: MissingThing, suspect: Suspect) -> bool:
    return quest.id in QUESTS and missing.id in MISSING and suspect.id in SUSPECTS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for q in QUESTS:
        for m in MISSING:
            for s in SUSPECTS:
                if story_gate(QUESTS[q], MISSING[m], SUSPECTS[s]):
                    combos.append((q, m, s))
    return combos


@dataclass
class StoryParams:
    quest: str
    missing: str
    suspect: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    setting: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit story world with a quest, dialogue, and repetition.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--setting", choices=SETTINGS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.quest is None or c[0] == args.quest)
              and (args.missing is None or c[1] == args.missing)
              and (args.suspect is None or c[2] == args.suspect)
              and (args.setting is None or c[0] == "missing_treats" or c[0] == "missing_cards" or c[0] == "missing_roses")]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    quest, missing, suspect = rng.choice(sorted(combos))
    dg = rng.choice(["girl", "boy"])
    hg = "boy" if dg == "girl" else "girl"
    detective = args.detective or _pick_name(rng, dg)
    helper = args.helper or _pick_name(rng, hg, avoid=detective)
    setting = args.setting or {"missing_treats": "kitchen", "missing_cards": "library", "missing_roses": "bakery"}[quest]
    return StoryParams(quest, missing, suspect, detective, dg, helper, hg, setting)


def _repeated_quote(suspect: Suspect) -> str:
    return {
        "cat": '“No snack, no snack,” the cat said.',
        "brother": '“Not me, not me,” the brother said.',
        "aunt": '“I only went for tea, tea, tea,” the aunt said.',
    }[suspect.id]


def tell(params: StoryParams) -> World:
    world = World()
    quest = QUESTS[params.quest]
    missing = MISSING[params.missing]
    suspect = SUSPECTS[params.suspect]
    detective = world.add(Entity(params.detective, kind="character", type=params.detective_gender, role="detective"))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper_gender, role="helper"))
    culprit = world.add(Entity("Suspect", kind="character", type=suspect.type, role="suspect", label=suspect.label, attrs={"motive": suspect.motive}))
    clue = world.add(Entity("clue", type="thing", label=quest.clue_phrase))
    basket = world.add(Entity("basket", type="thing", label=missing.container))
    detective.memes["curiosity"] = 1
    helper.memes["trust"] = 1
    world.facts["quest"] = quest
    world.facts["missing"] = missing
    world.facts["suspect"] = suspect
    world.facts["setting"] = SETTINGS[params.setting]

    world.say(f"At {SETTINGS[params.setting].place}, {detective.id} had a little whodunit on {detector_day(params.setting)}.")
    world.say(f"Nine {missing.adjective} French {missing.label} had vanished from the {missing.container}, and everyone wanted to know where they had gone.")
    world.say(f'"We need to look," said {detective.id}. "We need to look, look, look."')
    world.say(f'"I will help," said {helper.id}. "I will help, help, help."')
    world.para()

    for room in quest.search_order:
        detective.memes["curiosity"] += 1
        world.say(f"They searched the {room}.")
        if room == quest.final_place:
            culprit.memes["nervous"] += 1
            world.say(f"There, {helper.id} found {clue.label} tucked beside the trail.")
            world.say(f'"Why here?" asked {detective.id}. "Why here, why here?"')
            world.say(_repeated_quote(suspect))
            world.say(f'"Say that again," said {detective.id}. "Say it again."')
            world.say(_repeated_quote(suspect))
            culprit.memes["suspicion"] += 1
            culprit.meters["caught"] += 1
            break
    world.para()
    if suspect.id == "cat":
        world.say(f"The cat had climbed onto a chair and knocked the basket behind the door, then chased the sweet smell and curled up beside it.")
    elif suspect.id == "brother":
        world.say(f"The brother had hidden the nine French treats as a joke, but he forgot the plan when the game went too far.")
    else:
        world.say(f"The aunt had carried the tray to make tea, then set it down in the wrong room while she answered the kettle.")

    world.say(f'{detective.id} pointed to the trail and said, "The clue is here, the clue is here."')
    world.say(f'"And the missing things are there," said {helper.id}. "There they are."')
    world.say(f'At last, the truth came out: {suspect.label} had taken the {missing.count} {missing.adjective} French {missing.label} because {suspect.motive}.')
    world.say(f'{detective.id} smiled and said, "We found it, we found it."')
    world.say(f'Together they put the {missing.label} back in the {missing.container}, and {quest.ending_image}')

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        clue=clue,
        basket=basket,
        outcome="solved",
    )
    return world


def detector_day(setting: str) -> str:
    return {
        "kitchen": "a sunny afternoon",
        "bakery": "a busy morning",
        "library": "a quiet evening",
    }[setting]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q = f["quest"]
    s = f["suspect"]
    return [
        f'Write a child-friendly whodunit story with a quest that includes the words "nine" and "French".',
        f"Tell a mystery where {f['detective'].id} searches room by room to find the missing nine French treats and keeps asking the same question again and again.",
        f"Write a dialogue-heavy quest story where the clue is revealed by repetition, and {s.label} turns out to be the one who moved the missing things.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = f["quest"]
    m = f["missing"]
    s = f["suspect"]
    d = f["detective"]
    h = f["helper"]
    return [
        QAItem(
            question="What was missing?",
            answer=f"Nine {m.adjective} French {m.label} were missing from the {m.container}. The story follows the search for them."
        ),
        QAItem(
            question="Who helped with the search?",
            answer=f"{h.id} helped {d.id} search room by room. The helper noticed the clue when the hunt reached the last place."
        ),
        QAItem(
            question="Who did the ending blame?",
            answer=f"The ending showed that {s.label} had taken the missing things. The repeated talking gave away the answer."
        ),
        QAItem(
            question=f"Why did {s.label} get caught?",
            answer=f"{s.label} kept repeating the same line, and that made the clue stand out. The repetition matched the hiding place and turned the search into a solved whodunit."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where people ask questions and try to find out who did something."
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out the truth."
        ),
        QAItem(
            question="Why do repeated words matter in a mystery?",
            answer="Repeated words can be a clue because they may show nervousness or point to the same place again and again."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Quest, Missing, Suspect) :- quest(Quest), missing(Missing), suspect(Suspect).
solved :- valid(Q, M, S), quest(Q), missing(M), suspect(S).
#show valid/3.
#show solved/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for m in MISSING:
        lines.append(asp.fact("missing", m))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    # smoke test
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def _pick_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combo = resolve_params(args, rng)
    return combo


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("missing_treats", "treats", "cat", "Mia", "girl", "Leo", "boy", "kitchen"),
    StoryParams("missing_cards", "cards", "brother", "Theo", "boy", "Ava", "girl", "library"),
    StoryParams("missing_roses", "roses", "aunt", "Nora", "girl", "Max", "boy", "bakery"),
]


def resolve_args(args: argparse.Namespace) -> StoryParams:
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    if args.quest and args.quest not in QUESTS:
        raise StoryError("(Unknown quest.)")
    if args.missing and args.missing not in MISSING:
        raise StoryError("(Unknown missing item.)")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("(Unknown suspect.)")
    combos = [c for c in valid_combos()
              if (args.quest is None or c[0] == args.quest)
              and (args.missing is None or c[1] == args.missing)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    q, m, s = rng.choice(sorted(combos))
    dg = rng.choice(["girl", "boy"])
    hg = "boy" if dg == "girl" else "girl"
    detective = args.detective or _pick_name(rng, dg)
    helper = args.helper or _pick_name(rng, hg, avoid=detective)
    setting = args.setting or {"missing_treats": "kitchen", "missing_cards": "library", "missing_roses": "bakery"}[q]
    return StoryParams(q, m, s, detective, dg, helper, hg, setting)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print("  ", combo)
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_args(argparse.Namespace(
                quest=args.quest, missing=args.missing, suspect=args.suspect,
                setting=args.setting, detective=args.detective, helper=args.helper,
                seed=base_seed + i
            ))
            params.seed = base_seed + i
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
