#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fellow_alcoholic_identity_conflict_whodunit.py
===============================================================================

A standalone storyworld for a small whodunit-style mystery set in a sleepy inn.

Seed premise:
- Include the words fellow, alcoholic, identity
- Use Conflict
- Style: Whodunit

Core shape:
- A strange spill, a confused identity, a few suspicious clues, a tense conflict,
  and a reveal that turns out to be harmless but surprising.
- The world model tracks physical meters and emotional memes.
- A calm detective, a worried host, and a mysterious fellow all interact.
- The ending proves what changed by resolving the conflict and exposing the true
  identity through clues, not through template prose.

This script is stdlib-only and can be run directly.
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
SAFE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hostess"}
        male = {"boy", "father", "dad", "man", "detective"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    mood: str
    clue_spot: str
    rumor: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Suspect:
    id: str
    label: str
    likely_role: str
    detail: str
    true_role: str
    clue: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class ConflictMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["suspicion"] < THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("inn").memes["unease"] += 1
        out.append("__tension__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.get("inn").memes["unease"] >= THRESHOLD and world.get("host").memes["worry"] >= THRESHOLD:
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("host").memes["conflict"] += 1
            world.get("detective").memes["conflict"] += 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("tension", _r_tension), Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_moves() -> list[ConflictMove]:
    return [m for m in MOVES.values() if m.sense >= SAFE_MIN]


def chosen_move() -> ConflictMove:
    return max(MOVES.values(), key=lambda m: m.sense)


def honest_clue(suspect: Suspect) -> bool:
    return bool(suspect.clue)


def likely_conflict(setting: Setting, suspect: Suspect) -> bool:
    return setting.rumor in suspect.tags and honest_clue(suspect)


def _spill(world: World, suspect: Entity) -> None:
    suspect.meters["spilled"] += 1
    suspect.memes["nervous"] += 1
    propagate(world, narrate=False)


def introduce(world: World, detective: Entity, host: Entity, setting: Setting) -> None:
    world.say(
        f"On a damp evening at {setting.place}, the room felt unusually quiet. "
        f"{detective.id} had come to solve a small whodunit, and {host.id} had "
        f"already noticed a strange rumor about the fellow in the corner."
    )


def clue_one(world: World, setting: Setting, suspect: Suspect) -> None:
    world.say(
        f"Near {setting.clue_spot}, there was a thin smell of bitter juice and a "
        f"torn paper label. The label mattered, because it pointed to the fellow "
        f"who had been seen with {suspect.detail}."
    )


def tension_beat(world: World, host: Entity, detective: Entity, suspect: Entity) -> None:
    host.memes["worry"] += 1
    detective.memes["suspicion"] += 1
    world.say(
        f'{host.id} narrowed {host.pronoun("possessive")} eyes. '
        f'"That fellow changed {suspect.pronoun("possessive")} story twice," '
        f"{host.id} whispered. {detective.id} kept the note in one hand and the "
        f"clue in the other."
    )


def conflict_beat(world: World, host: Entity, detective: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{host.id} stepped between the table and the stranger. "
        f'"If you are not who you say you are, tell us now," {host.id} said, '
        f"and the whole inn seemed to hold its breath."
    )
    if host.memes["conflict"] >= THRESHOLD:
        world.say(
            f"{detective.id} lifted a calm hand. It was a conflict, but a quiet one: "
            f"nobody wanted a fight, only the truth."
        )


def reveal(world: World, suspect: Entity, setting: Setting, move: ConflictMove) -> None:
    suspect.meters["unmasked"] += 1
    suspect.memes["relief"] += 1
    world.say(
        f"Then {move.text}. The missing piece clicked into place at last: the "
        f"fellow was not a thief at all, but {suspect.attrs['true_identity']}, "
        f"who had come in from the rain and mistaken by everyone for someone else."
    )
    world.say(
        f"The torn label matched {suspect.pronoun('possessive')} coat pocket, and "
        f"the bitter smell came from a medicine bottle, not a crime."
    )
    world.say(
        f"At {setting.place}, the rumor faded, and the room felt lighter than it had "
        f"all night."
    )


def resolution(world: World, host: Entity, detective: Entity, suspect: Entity) -> None:
    host.memes["conflict"] = 0
    detective.memes["suspicion"] = 0
    world.say(
        f"{host.id} let out a breath and apologized. {detective.id} smiled and "
        f"put the notes away. The strange fellow looked embarrassed, but safe."
    )
    world.say(
        f'“Next time,” {host.id} said, “just tell us your identity right away.”'
    )


def tell(setting: Setting, suspect_cfg: Suspect, move: ConflictMove,
         detective_name: str = "Mara", detective_type: str = "girl",
         host_name: str = "June", host_type: str = "girl") -> World:
    world = World()
    detective = world.add(Entity(detective_name, kind="character", type=detective_type, role="detective", label="the detective"))
    host = world.add(Entity(host_name, kind="character", type=host_type, role="host", label="the host"))
    suspect = world.add(Entity(suspect_cfg.id, kind="character", type="man", role="suspect", label=suspect_cfg.label,
                               attrs={"true_identity": suspect_cfg.true_role, "detail": suspect_cfg.detail}))
    world.add(Entity("inn", type="place", label=setting.place))
    detective.memes["suspicion"] = 1
    host.memes["worry"] = 1
    suspect.memes["suspicion"] = 1

    introduce(world, detective, host, setting)
    world.para()
    clue_one(world, setting, suspect_cfg)
    tension_beat(world, host, detective, suspect)
    world.para()
    conflict_beat(world, host, detective)
    reveal(world, suspect, setting, move)
    world.para()
    resolution(world, host, detective, suspect)

    world.facts.update(
        setting=setting,
        suspect=suspect,
        suspect_cfg=suspect_cfg,
        detective=detective,
        host=host,
        move=move,
        outcome="resolved",
    )
    return world


SETTINGS = {
    "inn": Setting("inn", "the sleepy inn", "muffled", "the front desk", "alcoholic"),
    "station": Setting("station", "the old station house", "echoing", "the waiting bench", "identity"),
    "library": Setting("library", "the small library", "hushed", "the reading lamp", "fellow"),
}

SUSPECTS = {
    "bottle": Suspect("bottle", "the fellow with the bottle", "drinker", "a dark bottle", "innkeeper", "a torn paper label", {"alcoholic"}),
    "coat": Suspect("coat", "the fellow in the coat", "stranger", "a soaked coat", "postman", "a monogrammed button", {"identity"}),
    "ledger": Suspect("ledger", "the fellow with the ledger", "clerk", "a ledger book", "cashier", "a signed receipt", {"fellow"}),
}

MOVES = {
    "calm": ConflictMove("calm", 3, 3, "the detective asked one careful question after another, and the truth arrived on its own", "the detective guessed too soon and only made things murkier"),
    "show_note": ConflictMove("show_note", 3, 2, "the host showed the hidden note, and everyone saw the name written in the corner", "the note was too smudged to help"),
    "compare_clue": ConflictMove("compare_clue", 2, 2, "the detective compared the clues and finally saw which detail belonged to which fellow", "the clues did not fit together"),
}

NAMES = ["Mara", "June", "Nina", "Iris", "Theo", "Ben", "Clara", "Eli"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    suspect: str
    move: str
    detective_name: str
    detective_type: str
    host_name: str
    host_type: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for spid, suspect in SUSPECTS.items():
            if likely_conflict(setting, suspect):
                for mid in MOVES:
                    combos.append((sid, spid, mid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with conflict, clues, and identity confusion.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--detective-name")
    ap.add_argument("--host-name")
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
    if args.setting and args.suspect:
        if not likely_conflict(SETTINGS[args.setting], SUSPECTS[args.suspect]):
            raise StoryError("No story: that setting and suspect do not create a believable conflict or clue trail.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.suspect is None or c[1] == args.suspect)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, suspect, move = rng.choice(sorted(combos))
    det_name = args.detective_name or rng.choice(NAMES)
    host_name = args.host_name or rng.choice([n for n in NAMES if n != det_name])
    det_type = rng.choice(["girl", "boy"])
    host_type = rng.choice(["girl", "boy"])
    return StoryParams(setting, suspect, move, det_name, det_type, host_name, host_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit story for a young child that includes the words fellow, alcoholic, and identity.',
        f"Tell a small mystery where {f['host'].id} and {f['detective'].id} question a fellow after a strange clue at {f['setting'].place}.",
        f"Write a story with conflict and a gentle reveal where the wrong identity causes trouble, then the real identity is shown by clues.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    suspect = f["suspect_cfg"]
    host = f["host"]
    detective = f["detective"]
    setting = f["setting"]
    return [
        QAItem(
            question="What kind of story is this?",
            answer="It is a little whodunit mystery. A strange clue creates conflict, and the ending explains the mistaken identity.",
        ),
        QAItem(
            question=f"Why did {host.id} get upset?",
            answer=f"{host.id} got upset because the clues made one fellow seem suspicious. The tension grew until everyone had to stop and compare the details carefully.",
        ),
        QAItem(
            question="What solved the problem?",
            answer=f"The clues solved it. Once the torn label and the note were matched together, the true identity became clear and the conflict ended.",
        ),
        QAItem(
            question=f"Who was the fellow really?",
            answer=f"The fellow was really {suspect.true_role}. He had looked suspicious at first, but the story showed that the identity was only mistaken.",
        ),
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened at {setting.place}. That was the place where the clue appeared and where the truth was uncovered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where people try to find out who did something or who someone really is.",
        ),
        QAItem(
            question="What does identity mean?",
            answer="Identity means who a person really is. Sometimes people get confused at first, and clues help show the truth.",
        ),
        QAItem(
            question="Why can conflict happen in a mystery?",
            answer="Conflict can happen when people disagree about what the clues mean or who can be trusted. The truth usually calms things down.",
        ),
    ]


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("inn", "bottle", "calm", "Mara", "girl", "June", "girl"),
    StoryParams("station", "coat", "compare_clue", "Eli", "boy", "Nina", "girl"),
    StoryParams("library", "ledger", "show_note", "Clara", "girl", "Theo", "boy"),
]


def outcome_of(params: StoryParams) -> str:
    return "resolved"


def explain_rejection(setting: Setting, suspect: Suspect) -> str:
    return f"(No story: that pair does not create a strong enough clue-based conflict at {setting.place}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", sid, t))
    for mid in MOVES:
        lines.append(asp.fact("move", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, U, M) :- setting(S), suspect(U), move(M), tag(U, T), setting_tag(S, T).
"""


def asp_program(extra: str, show: str) -> str:
    facts = asp_facts()
    return f"{facts}\n{show}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combo gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as ex:
        rc = 1
        print(f"SMOKE TEST FAILED: {ex}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SUSPECTS[params.suspect], MOVES[params.move],
                 params.detective_name, params.detective_type, params.host_name, params.host_type)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.asp:
        print(f"{len(valid_combos())} compatible combos")
        for c in valid_combos():
            print(c)
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
        hdr = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
