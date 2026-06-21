#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/compress_misunderstanding_dialogue_whodunit.py
===============================================================================

A small whodunit story world about a missing object, a mistaken assumption, and
a careful conversation that clears things up. The seed word "compress" appears
both as a literal cold compress and as part of the mystery's confusion: one
character thinks the missing item is evidence, while another is trying to keep
someone's bruise calm and cool.

The world is built for child-facing, TinyStories-style mystery prose:
- typed entities with physical meters and emotional memes
- state-driven beats, not frozen text swapping
- a reasonableness gate for valid mystery setups
- a Python gate mirrored by inline ASP rules
- prompts, story-grounded QA, and world-knowledge QA
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "woman"}
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
    label: str
    place: str
    has_clues: bool = True
    has_bright_light: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    likely_place: str
    category: str
    can_be_misread: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    mistaken_for: str
    clue_word: str
    reason: str
    clears_with: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DialogueBeat:
    id: str
    opener: str
    clarifier: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    item: str
    misunderstanding: str
    dialogue: str
    detective: str
    witness: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
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


def _r_worry(world: World) -> list[str]:
    out = []
    if world.facts.get("missing_seen") and not world.facts.get("resolved"):
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    if world.facts.get("resolved") and ("relief", "once") not in world.fired:
        world.fired.add(("relief", "once"))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("relief", "social", _r_relief)]


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


def reasonableness_check(setting: Setting, item: MissingItem, m: Misunderstanding) -> bool:
    return setting.has_clues and item.can_be_misread and item.category == m.mistaken_for


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for mid, m in MISUNDERSTANDINGS.items():
                if reasonableness_check(setting, item, m):
                    combos.append((sid, iid, mid))
    return combos


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    opts = [n for n in pool if n != avoid]
    return rng.choice(opts)


def explain_rejection(setting: Setting, item: MissingItem, m: Misunderstanding) -> str:
    return (
        f"(No story: this setup does not fit a small mystery. "
        f"The setting must have clues, the item must be something a child could "
        f"misread, and the misunderstanding must match that item. "
        f"Try a different item or mystery.)"
    )


def _do_find(world: World, item_ent: Entity) -> None:
    item_ent.meters["found"] = 1
    world.facts["missing_seen"] = True
    propagate(world, narrate=False)


def predict_confusion(world: World, item_id: str) -> dict:
    sim = world.copy()
    _do_find(sim, sim.get(item_id))
    return {
        "confusion": sim.get("Detective").memes["worry"],
        "resolved": sim.get(item_id).meters["found"] >= THRESHOLD,
    }


def intro(world: World, detective: Entity, witness: Entity, helper: Entity, setting: Setting) -> None:
    detective.memes["curiosity"] += 1
    witness.memes["unease"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At {setting.place}, {detective.id} noticed something odd before the others did. "
        f"{witness.id} was frowning, and {helper.id} was already looking under the little table."
    )


def missing_notice(world: World, detective: Entity, item: MissingItem) -> None:
    world.say(
        f'"{item.label_word if hasattr(item, "label_word") else item.label} is gone," '
        f"{detective.id} said. "
        f'The missing thing was {item.phrase}, and that made the room feel very quiet.'
    )


def raise_misunderstanding(world: World, witness: Entity, item: MissingItem, m: Misunderstanding) -> None:
    witness.memes["alarm"] += 1
    world.say(
        f'"Wait," {witness.id} said. "Did you mean {m.mistaken_for}? '
        f"I heard {m.clue_word}, and I thought that was the clue."
    )
    world.say(
        f"{witness.id} pointed at the {item.likely_place}, because the word sounded like trouble."
    )


def answer_question(world: World, helper: Entity, detective: Entity, item: MissingItem, m: Misunderstanding) -> None:
    helper.memes["calm"] += 1
    world.say(
        f'"No," {helper.id} said gently. "{m.reason} '
        f"That's why {m.clue_word} can sound scary when it really is not."
    )
    world.say(
        f'{helper.id} took a careful breath and showed the truth: {m.clears_with}.'
    )


def find_item(world: World, detective: Entity, item_ent: Entity) -> None:
    _do_find(world, item_ent)
    world.say(
        f"{detective.id} opened the right drawer at last. There sat the missing {item_ent.label}, "
        f"right where it had been left."
    )


def reveal(world: World, detective: Entity, witness: Entity, helper: Entity, item: MissingItem, m: Misunderstanding) -> None:
    world.facts["resolved"] = True
    detective.memes["relief"] += 1
    witness.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'"Oh!" {witness.id} said. "I thought you meant the other thing." '
        f'"That was the misunderstanding," {helper.id} answered, smiling.'
    )
    world.say(
        f'Then {detective.id} nodded. "{m.clears_with}," {detective.pronoun()} said, '
        f"and everyone laughed at how one small word could send the room in circles."
    )


def ending(world: World, detective: Entity, item: MissingItem, setting: Setting) -> None:
    world.say(
        f"By the end, the missing {item.label} was back in its place, and the room at {setting.place} felt calm again."
    )


SETTINGS = {
    "kitchen": Setting(id="kitchen", label="the kitchen", place="the kitchen", has_clues=True, tags={"room"}),
    "library": Setting(id="library", label="the library", place="the library", has_clues=True, tags={"room"}),
    "workshop": Setting(id="workshop", label="the workshop", place="the workshop", has_clues=True, tags={"room"}),
}

ITEMS = {
    "compress": MissingItem(
        id="compress",
        label="compress",
        phrase="a cool cloth compress for a bump on the knee",
        likely_place="first-aid basket",
        category="compress",
        can_be_misread=True,
        tags={"compress", "first_aid"},
    ),
    "magnifier": MissingItem(
        id="magnifier",
        label="magnifying glass",
        phrase="a small magnifying glass with a round handle",
        likely_place="reading desk",
        category="magnifier",
        can_be_misread=True,
        tags={"glass", "clue"},
    ),
    "key": MissingItem(
        id="key",
        label="tiny key",
        phrase="a tiny brass key with a ribbon on it",
        likely_place="jar shelf",
        category="key",
        can_be_misread=True,
        tags={"key", "clue"},
    ),
}

MISUNDERSTANDINGS = {
    "compress": Misunderstanding(
        id="compress",
        mistaken_for="a clue packet",
        clue_word="compress",
        reason="A compress is not a secret note. It is something cool and soft you press on a bruise.",
        clears_with="the cold cloth was for a bump, not for a mystery",
        tags={"compress", "misunderstanding"},
    ),
    "magnifier": Misunderstanding(
        id="magnifier",
        mistaken_for="the missing key",
        clue_word="magnifier",
        reason="A magnifying glass helps you look closely. It is not the same as a key.",
        clears_with="the glass only helped them search, not open the drawer",
        tags={"magnifier", "misunderstanding"},
    ),
    "key": Misunderstanding(
        id="key",
        mistaken_for="the clue envelope",
        clue_word="key",
        reason="A key opens a lock, but it is not itself a note.",
        clears_with="the key belonged by the lock, while the envelope was elsewhere",
        tags={"key", "misunderstanding"},
    ),
}

DIALOGUES = {
    "gentle": DialogueBeat(
        id="gentle",
        opener="I think something is missing",
        clarifier="Wait, that word sounded wrong to me",
        reveal="Oh, now I see what you meant",
        tags={"dialogue"},
    ),
    "hushed": DialogueBeat(
        id="hushed",
        opener="Look at this strange spot",
        clarifier="Say that again, slowly",
        reveal="That makes much more sense",
        tags={"dialogue"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Mia", "Ada"]
BOY_NAMES = ["Eli", "Owen", "Finn", "Theo", "Noah", "Jude"]
TRAITS = ["careful", "curious", "quiet", "smart"]


def choose_combo(rng: random.Random) -> tuple[str, str, str]:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid mystery combinations exist.")
    return rng.choice(sorted(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.misunderstanding:
        s, i, m = SETTINGS[args.setting], ITEMS[args.item], MISUNDERSTANDINGS[args.misunderstanding]
        if not reasonableness_check(s, i, m):
            raise StoryError(explain_rejection(s, i, m))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.item is None or c[1] == args.item)
        and (args.misunderstanding is None or c[2] == args.misunderstanding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, misunderstanding = rng.choice(sorted(combos))
    dialogue = args.dialogue or rng.choice(sorted(DIALOGUES))
    gender = rng.choice(["girl", "boy"])
    detective = args.detective or pick_name(rng, gender)
    witness = args.witness or pick_name(rng, "girl" if gender == "boy" else "boy", avoid=detective)
    helper = args.helper or rng.choice(["Aunt", "Uncle", "Nurse"])
    return StoryParams(setting=setting, item=item, misunderstanding=misunderstanding, dialogue=dialogue, detective=detective, witness=witness, helper=helper)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    item_cfg = ITEMS[params.item]
    mis = MISUNDERSTANDINGS[params.misunderstanding]
    dia = DIALOGUES[params.dialogue]
    world = World(setting)

    det = world.add(Entity(id=params.detective, kind="character", type="girl" if params.detective in GIRL_NAMES else "boy", role="detective"))
    wit = world.add(Entity(id=params.witness, kind="character", type="girl" if params.witness in GIRL_NAMES else "boy", role="witness"))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman", role="helper", label=params.helper))
    item = world.add(Entity(id="Clue", kind="thing", type="thing", label=item_cfg.label, attrs={"category": item_cfg.category}))

    intro(world, det, wit, helper, setting)
    world.para()
    world.say(f'"{dia.opener}," {det.id} said.')
    missing_notice(world, det, item_cfg)
    raise_misunderstanding(world, wit, item_cfg, mis)
    answer_question(world, helper, det, item_cfg, mis)
    find_item(world, det, item)
    reveal(world, det, wit, helper, item_cfg, mis)
    world.para()
    ending(world, det, item_cfg, setting)

    world.facts.update(
        detective=det, witness=wit, helper=helper, item_cfg=item_cfg, item=item,
        misunderstanding=mis, dialogue=dia, setting=setting, resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    mis = f["misunderstanding"]
    return [
        f'Write a child-friendly whodunit that includes the word "{item.id}" and a misunderstanding about it.',
        f"Tell a small mystery where one character thinks {mis.mistaken_for}, but another explains that {item.phrase} is not a clue.",
        f'Write a short dialogue-heavy mystery with a mistaken word and a calm reveal at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, wit, helper = f["detective"], f["witness"], f["helper"]
    item, mis, setting = f["item_cfg"], f["misunderstanding"], f["setting"]
    return [
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about a missing {item.label} and a misunderstanding about what that word meant. The characters had to talk carefully before they could solve it.",
        ),
        QAItem(
            question=f"What did {wit.id} misunderstand?",
            answer=f"{wit.id} thought {mis.mistaken_for}, because the word {mis.clue_word} sounded like a clue. That was not right, so the helper explained the difference.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{det.id} found the missing item, and {helper.id} explained that {mis.clears_with}. Once everyone understood, the room became calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a compress?",
            answer="A compress is a soft, cool cloth or pad used on a bruise or bump. It helps make the sore spot feel better.",
        ),
        QAItem(
            question="Why do people ask questions in a mystery?",
            answer="People ask questions so they can find out what really happened. Careful questions help clear up confusion and point to the truth.",
        ),
        QAItem(
            question="What does it mean to misunderstand something?",
            answer="To misunderstand means to get the meaning wrong. You may think one thing is happening when it is really something else.",
        ),
    ]


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
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,I,M) :- setting(S), item(I), misunderstanding(M), item_can_be_misread(I), item_category(I,C), mistaken_for(M,C), has_clues(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.has_clues:
            lines.append(asp.fact("has_clues", sid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.can_be_misread:
            lines.append(asp.fact("item_can_be_misread", iid))
        lines.append(asp.fact("item_category", iid, i.category))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("mistaken_for", mid, m.mistaken_for))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between clingo and Python valid_combos().")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print(f"OK: ASP matches Python and generation smoke test passed ({len(valid_combos())} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit world built around a misunderstanding and a careful dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--dialogue", choices=DIALOGUES)
    ap.add_argument("--detective")
    ap.add_argument("--witness")
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.item not in ITEMS:
        raise StoryError("Unknown item.")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if not reasonableness_check(SETTINGS[params.setting], ITEMS[params.item], MISUNDERSTANDINGS[params.misunderstanding]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], ITEMS[params.item], MISUNDERSTANDINGS[params.misunderstanding]))
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
    StoryParams(setting="kitchen", item="compress", misunderstanding="compress", dialogue="gentle", detective="Mina", witness="Eli", helper="Aunt"),
    StoryParams(setting="library", item="magnifier", misunderstanding="magnifier", dialogue="hushed", detective="Nora", witness="Finn", helper="Uncle"),
    StoryParams(setting="workshop", item="key", misunderstanding="key", dialogue="gentle", detective="Ivy", witness="Theo", helper="Nurse"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible mystery setups:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 30):
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
