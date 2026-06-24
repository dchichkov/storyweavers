#!/usr/bin/env python3
"""
A small detective-story world about an odd sound, a little magic, and clues
spoken with an accent. The story stays grounded in simulated state: the case
begins with a strange effect, suspicion grows from evidence, and a final
resolution explains what really happened.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective"}
        male = {"boy", "man", "father", "detective"}
        if self.type in female and self.type not in {"boy", "man", "father"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Suspect:
    id: str
    accent: str
    tells_truth: bool
    magical: bool
    clue: str
    phrase: str


@dataclass
class Case:
    place: str
    incident: str
    sound_effect: str
    magic_effect: str
    accent: str
    approximate: str
    culprit: str
    witness: str
    evidence: str


@dataclass
class World:
    case: Case
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.case)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "library": "the old library",
    "museum": "the quiet museum",
    "bakery": "the corner bakery",
    "station": "the little train station",
}

INCIDENTS = {
    "vanish": "a silver key vanished from the table",
    "echo": "a strange echo came from the hallway",
    "glow": "a bright glow appeared in the dark room",
    "knock": "three soft knocks came from the locked door",
}

SOUND_EFFECTS = {
    "tap": "tap-tap",
    "clink": "clink!",
    "whoosh": "whoosh",
    "plink": "plink-plink",
}

MAGIC_EFFECTS = {
    "sparkle": "a tiny sparkle trail",
    "mist": "a curl of silver mist",
    "blink": "a blink of blue light",
    "twirl": "a twirling ribbon of light",
}

ACCENTS = {
    "soft": "with a soft accent",
    "bright": "with a bright accent",
    "round": "with a round accent",
    "careful": "with a careful accent",
}

APPROXIMATE_WORDS = {
    "almost": "almost",
    "nearly": "nearly",
    "about": "about",
    "roughly": "roughly",
}

SUSPECTS = {
    "baker": Suspect("baker", "careful", True, False, "flour", "The baker said the tray was empty."),
    "magician": Suspect("magician", "bright", False, True, "wand", "The magician said the trick was nearly done."),
    "porter": Suspect("porter", "round", True, False, "wheel", "The porter said he only moved boxes."),
    "child": Suspect("child", "soft", True, True, "button", "The child said he only heard the sound."),
}

DETECTIVE_NAMES = ["Mina", "Jules", "Nora", "Pip", "Ada", "Theo"]


@dataclass
class StoryParams:
    place: str
    incident: str
    sound_effect: str
    magic_effect: str
    accent: str
    approximate: str
    culprit: str
    witness: str
    detective: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, incident: str, culprit: str, witness: str) -> bool:
    if culprit == witness:
        return False
    if place not in PLACES or incident not in INCIDENTS:
        return False
    if culprit not in SUSPECTS or witness not in SUSPECTS:
        return False
    # A magical suspect is required for a magic story beat.
    if not SUSPECTS[culprit].magical:
        return False
    # The witness should be truthful enough to support detective dialogue.
    if not SUSPECTS[witness].tells_truth:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for incident in INCIDENTS:
            for culprit in SUSPECTS:
                for witness in SUSPECTS:
                    if valid_combo(place, incident, culprit, witness):
                        out.append((place, incident, culprit, witness))
    return out


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------
def intro(world: World, detective: Entity, witness: Entity) -> None:
    world.say(
        f"{detective.name_or_label()} was the town detective, and {detective.pronoun()} "
        f"always listened closely when someone spoke {witness.memes.get('accent_text', 'with a careful accent')}."
    )
    world.say(
        f"On a {world.case.place}, {world.case.incident}, and the room still hummed "
        f"with {world.case.sound_effect} and {world.case.magic_effect}."
    )


def investigate(world: World, detective: Entity, witness: Entity, culprit: Entity) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(
        f"{detective.name_or_label()} bent low and whispered, \"What did you hear?\""
    )
    world.say(
        f"{witness.name_or_label()} answered, \"I heard {world.case.sound_effect}, "
        f"then {world.case.magic_effect}.\""
    )
    witness.meters["heard"] = witness.meters.get("heard", 0) + 1
    world.facts["witness_statement"] = f"{world.case.sound_effect} and {world.case.magic_effect}"
    culprit.memes["uneasy"] = culprit.memes.get("uneasy", 0) + 1


def reason_about_clue(world: World, detective: Entity, culprit: Entity) -> None:
    world.say(
        f"{detective.name_or_label()} looked at the clue and said, "
        f"\"That is only an {world.case.approximate} match, not the whole answer.\""
    )
    world.say(
        f"By the table, {culprit.name_or_label()} kept glancing at the floor."
    )
    detective.meters["clues"] = detective.meters.get("clues", 0) + 1


def reveal(world: World, detective: Entity, culprit: Entity, witness: Entity) -> None:
    if culprit.memes.get("uneasy", 0) < 1:
        raise StoryError("the culprit never became uneasy enough for a believable reveal")
    world.say(
        f"{detective.name_or_label()} said, \"The sound was {world.case.sound_effect}, "
        f"and the magic was {world.case.magic_effect}. But the real clue was your clue, "
        f"{culprit.name_or_label()}: {culprit.facts['clue']}.\""
    )
    world.say(
        f"{culprit.name_or_label()} blinked. \"All right,\" {culprit.pronoun()} said, "
        f"\"I used the spell to hide the missing thing, but it only made an {world.case.approximate} trick.\""
    )
    world.say(
        f"{witness.name_or_label()} nodded. \"I knew the voice sounded right, but not exact.\""
    )
    world.facts["resolved"] = True


def ending(world: World, detective: Entity, culprit: Entity) -> None:
    world.say(
        f"In the end, the missing thing was found behind a loose panel, and the room grew quiet again."
    )
    world.say(
        f"{detective.name_or_label()} put the clue in a small envelope, and {culprit.name_or_label()} "
        f"walked away with a sheepish look instead of a mystery."
    )


def build_world(params: StoryParams) -> World:
    case = Case(
        place=PLACES[params.place],
        incident=INCIDENTS[params.incident],
        sound_effect=SOUND_EFFECTS[params.sound_effect],
        magic_effect=MAGIC_EFFECTS[params.magic_effect],
        accent=ACCENTS[params.accent],
        approximate=APPROXIMATE_WORDS[params.approximate],
        culprit=params.culprit,
        witness=params.witness,
        evidence=SUSPECTS[params.culprit].clue,
    )
    world = World(case)
    detective = world.add(Entity(id="detective", kind="character", type="detective", label=params.detective))
    witness = world.add(Entity(id="witness", kind="character", type="person", label=params.witness.title()))
    culprit = world.add(Entity(id="culprit", kind="character", type="person", label=params.culprit.title()))
    witness.memes["accent_text"] = case.accent
    culprit.facts = {"clue": case.evidence}
    world.facts.update(detective=detective, witness=witness, culprit=culprit, case=case)
    intro(world, detective, witness)
    world.para()
    investigate(world, detective, witness, culprit)
    reason_about_clue(world, detective, culprit)
    world.para()
    reveal(world, detective, culprit, witness)
    ending(world, detective, culprit)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    c = world.case
    return [
        f'Write a short detective story for a child that includes "{c.sound_effect}" and "{c.magic_effect}".',
        f"Tell a mystery where someone speaks {c.accent} and the detective notices an {c.approximate} clue.",
        f'Write a simple story about {c.incident} in {c.place} with dialogue, sound effects, and a little magic.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.case
    d = world.facts["detective"]
    w = world.facts["witness"]
    u = world.facts["culprit"]
    return [
        QAItem(
            question=f"Who solved the mystery in {c.place}?",
            answer=f"{d.name_or_label()} solved it by listening carefully and following the clues."
        ),
        QAItem(
            question=f"What sound effect was heard during the case?",
            answer=f"The story heard {c.sound_effect}, which helped make the clue feel real."
        ),
        QAItem(
            question=f"What magic effect appeared in the mystery?",
            answer=f"The story included {c.magic_effect}, so the mystery had a little magic in it."
        ),
        QAItem(
            question=f"Who spoke with an accent in the story?",
            answer=f"{w.name_or_label()} spoke {c.accent}, which helped the detective notice the voice."
        ),
        QAItem(
            question=f"Why did the detective say the clue was only {c.approximate}?",
            answer=f"The clue looked close to the answer, but it was not exact, so {d.name_or_label()} treated it as only an {c.approximate} match."
        ),
        QAItem(
            question=f"What did the culprit admit at the end?",
            answer=f"{u.name_or_label()} admitted that the magic trick only hid the missing thing for a little while."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks questions, and tries to find out what really happened."
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small bit of information that helps solve a mystery."
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a word or phrase that helps readers imagine a sound, like tap-tap or whoosh."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful or unusual that can happen in the story world."
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
incident(I) :- case_incident(I).
suspect(S) :- suspect_id(S).

valid_case(P,I,C,W) :- place(P), incident(I), culprit(C), witness(W),
                       magical(C), truthful(W), C != W.

story_hint(P,I,C,W) :- valid_case(P,I,C,W), solves(C, W, P, I).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for iid in INCIDENTS:
        lines.append(asp.fact("case_incident", iid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect_id", sid))
        if s.magical:
            lines.append(asp.fact("magical", sid))
        if s.tells_truth:
            lines.append(asp.fact("truthful", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_case/4."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - ap:
        print("  only in python:", sorted(py - ap))
    if ap - py:
        print("  only in clingo:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with sound effects, magic, dialogue, accents, and approximate clues.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--incident", choices=INCIDENTS)
    ap.add_argument("--sound-effect", dest="sound_effect", choices=SOUND_EFFECTS)
    ap.add_argument("--magic-effect", dest="magic_effect", choices=MAGIC_EFFECTS)
    ap.add_argument("--accent", choices=ACCENTS)
    ap.add_argument("--approximate", choices=APPROXIMATE_WORDS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--witness", choices=SUSPECTS)
    ap.add_argument("--detective")
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.incident is None or c[1] == args.incident)
        and (args.culprit is None or c[2] == args.culprit)
        and (args.witness is None or c[3] == args.witness)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, incident, culprit, witness = rng.choice(sorted(filtered))
    sound_effect = args.sound_effect or rng.choice(list(SOUND_EFFECTS))
    magic_effect = args.magic_effect or rng.choice(list(MAGIC_EFFECTS))
    accent = args.accent or SUSPECTS[witness].accent
    approximate = args.approximate or rng.choice(list(APPROXIMATE_WORDS))
    detective = args.detective or rng.choice(DETECTIVE_NAMES)
    return StoryParams(
        place=place,
        incident=incident,
        sound_effect=sound_effect,
        magic_effect=magic_effect,
        accent=accent,
        approximate=approximate,
        culprit=culprit,
        witness=witness,
        detective=detective,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
    StoryParams("library", "vanish", "magician", "witness", "soft", "almost", "magician", "baker", "Mina"),
    StoryParams("museum", "glow", "magician", "child", "bright", "nearly", "magician", "porter", "Nora"),
    StoryParams("station", "knock", "magician", "baker", "careful", "roughly", "magician", "child", "Jules"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_case/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible cases:")
        for t in combos:
            print(" ", t)
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
