#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/magnetic_pace_quest_bad_ending_friendship_folk.py
==================================================================================

A standalone story world for a small folk-tale domain about a friendship quest,
a magnetic charm, and a pace that matters too much.  The model creates
constraint-checked stories where two friends set out on a quest, one of them
hurries too fast, a magnetic token causes trouble, and the ending can be bad
when the wrong pace and the wrong choice ruin the journey.

This script follows the shared Storyweavers contract:
- stdlib only
- eager import of storyworlds/results.py containers
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

The tale style is intentionally folk-like: a path, a want, a warning, a turn,
and an ending image proving what changed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
PACE_MIN = 2
PACE_MAX = 8


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Friend:
    id: str
    label: str
    patience: int
    pace: int
    brave: bool = False

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
class Quest:
    id: str
    path: str
    goal: str
    want: str
    token: str
    turn: str
    ending: str
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
class Charm:
    id: str
    label: str
    phrase: str
    magnetic: bool = True
    pulls: bool = True
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

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


def pace_ok(friend: Friend, quest: Quest) -> bool:
    return friend.pace >= PACE_MIN and friend.pace <= PACE_MAX and quest.id in QUESTS


def magnetic_trouble(charm: Charm, quest: Quest) -> bool:
    return charm.magnetic and "iron" in quest.tags


def quest_risk(friend: Friend, quest: Quest, charm: Charm) -> bool:
    return magnetic_trouble(charm, quest) and friend.pace >= 6


def pace_pressure(friend: Friend, quest: Quest) -> int:
    return friend.pace + (2 if "crowd" in quest.tags else 0)


def outcome_of_params(params: "StoryParams") -> str:
    if params.friend_pace <= 3 and params.patience >= 5:
        return "bad"
    if magnetic_trouble(CHARMS[params.charm], QUESTS[params.quest]):
        return "bad" if pace_pressure(Friend(params.friend_name, "", params.patience, params.friend_pace), QUESTS[params.quest]) >= 8 else "bad"
    return "bad"


@dataclass
@dataclass
class StoryParams:
    quest: str
    charm: str
    friend_name: str
    friend_gender: str
    companion_name: str
    companion_gender: str
    patience: int
    friend_pace: int
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


GIRL_NAMES = ["Mira", "Luna", "Nora", "Sana", "Tilda", "Rosa", "Elin"]
BOY_NAMES = ["Robin", "Perrin", "Alden", "Milo", "Bram", "Tomas", "Ivo"]


QUESTS = {
    "well": Quest("well", "the mossy lane", "the old wishing well", "fetch the silver bucket", "the magnetic key", "the pace of the walk", "the village went quiet again", {"iron", "crowd"}),
    "hill": Quest("hill", "the winding hill path", "the stone shrine", "carry the lantern", "the magnetic clasp", "the hush of dusk", "the hill kept its secret", {"iron"}),
    "ford": Quest("ford", "the river bend", "the far bank", "bring home the map box", "the magnetic nail", "the pace of the river", "the path was lost to mud", {"iron", "water"}),
}

CHARMS = {
    "key": Charm("key", "an old magnetic key", "an old magnetic key that clung to nails and needles", True, True, {"magnetic", "key"}),
    "clasp": Charm("clasp", "a magnetic clasp", "a magnetic clasp that snapped to every bit of iron", True, True, {"magnetic", "clasp"}),
    "stone": Charm("stone", "a magnetic stone", "a magnetic stone that pulled at coins and pins", True, True, {"magnetic", "stone"}),
}


def valid_combos() -> list[tuple[str, str]]:
    return [(q, c) for q in QUESTS for c in CHARMS if magnetic_trouble(CHARMS[c], QUESTS[q])]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_pull(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["pulled"] < THRESHOLD:
            continue
        sig = ("pull", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["frustration"] += 1
        out.append("__pull__")
    return out


def _r_bad(world: World) -> list[str]:
    out = []
    hero = world.entities.get("hero")
    if hero and hero.memes["frustration"] >= THRESHOLD and hero.meters["lost"] >= THRESHOLD:
        sig = ("bad",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__bad__")
    return out


CAUSAL_RULES = [Rule("pull", _r_pull), Rule("bad", _r_bad)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World, quest: Quest, charm: Charm) -> dict:
    sim = world.copy()
    sim.get("hero").meters["pulled"] += 1
    sim.get("hero").meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "frustration": sim.get("hero").memes["frustration"],
        "lost": sim.get("hero").meters["lost"],
    }


def tell(quest: Quest, charm: Charm, friend: Friend, companion: Friend, patience: int) -> World:
    w = World()
    hero = w.add(Entity("hero", "character", friend.label, role="friend", traits=["restless"]))
    pal = w.add(Entity("pal", "character", companion.label, role="companion", traits=["steady"]))
    hill = w.add(Entity("path", "place", quest.path, label=quest.path))
    token = w.add(Entity("token", "thing", charm.label, label=charm.label))
    hero.memes["pace"] = float(friend.pace)
    pal.memes["patience"] = float(patience)
    w.facts["quest"] = quest
    w.facts["charm"] = charm
    w.facts["friend"] = friend
    w.facts["companion"] = companion
    w.facts["path"] = hill
    w.facts["token"] = token

    w.say(
        f"Once in a small folk village, {friend.label} and {companion.label} went upon a quest "
        f"along {quest.path}. They meant to reach {quest.goal}, and the day felt stitched with old song."
    )
    w.say(
        f"{friend.label} carried {charm.phrase}; it was magnetic, and that made the little thing restless in {friend.pronoun('possessive')} pocket."
    )
    w.para()

    pred = predict(w, quest, charm)
    w.facts["predicted"] = pred
    w.say(
        f"{companion.label} walked at a careful pace and said, \"We should keep our pace slow. "
        f"This charm tugs at iron, and a hurrying step can make a quest go wrong.\""
    )
    w.say(
        f"But {friend.label} wanted the story to hurry on. {friend.label} laughed, quickened {friend.pronoun('possessive')} pace, and went straight for the brightest bend in the path."
    )
    hero.meters["pulled"] += 1
    hero.meters["lost"] += 1
    hero.memes["defiance"] += 1
    propagate(w, narrate=False)

    w.para()
    w.say(
        f"At the bend, the magnetic charm snagged on old nails in the gate. The key yanked hard, the strap twisted, and the two friends stumbled apart."
    )
    w.say(
        f"{companion.label} called out, but {friend.label} would not slow down. The path grew twisted, the bucket was dropped, and the quest lost its way."
    )

    w.para()
    w.say(
        f"By dusk, the village lamp was lit, yet the quest had gone bad. {friend.label} and {companion.label} sat on the step, dusty and sad, while the magnetic charm lay lonely on the ground."
    )
    w.say(
        f"They were still friends, but they had learned a hard folk lesson: a quest needs a steady pace, and not every bright-looking shortcut is wise."
    )

    w.facts["outcome"] = "bad"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q = f["quest"]
    c = f["charm"]
    return [
        f'Write a folk-tale quest story for a young child that includes the words "magnetic" and "pace".',
        f"Tell a friendship story where {f['friend'].label} and {f['companion'].label} go on a quest, but a magnetic charm and the wrong pace make the ending bad.",
        f"Write a short folk tale about a quest, friendship, and a magnetic object that causes trouble when the pace gets too fast.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    friend = f["friend"]
    companion = f["companion"]
    quest = f["quest"]
    charm = f["charm"]
    pred = f["predicted"]
    return [
        QAItem(
            question="Who went on the quest?",
            answer=f"{friend.label} and {companion.label} went together on a small folk quest. They were friends who hoped to reach {quest.goal}."
        ),
        QAItem(
            question="Why did the quest go bad?",
            answer=f"It went bad because {charm.label} was magnetic and kept tugging at iron on the path. {friend.label} also hurried and did not keep a steady pace, so the friends lost their way."
        ),
        QAItem(
            question="What did the steady friend warn about?",
            answer=f"{companion.label} warned that they should keep their pace slow. {companion.label} knew the charm could snag on iron and make the journey go wrong."
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"The friends sat down tired and sad, and the quest ended badly. The magnetic charm was left on the ground, and the village lamp came on after the trouble was over."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does magnetic mean?",
            answer="Magnetic means it can pull certain metal things toward it, like pins, nails, or little keys."
        ),
        QAItem(
            question="What is pace?",
            answer="Pace is how fast or slow someone moves. A steady pace can help on a long walk."
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey where someone goes looking for something important."
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about one another, listen, and try to help each other."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x for x, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("well", "key", "Mira", "girl", "Robin", "boy", 5, 7),
    StoryParams("hill", "clasp", "Bram", "boy", "Nora", "girl", 6, 6),
    StoryParams("ford", "stone", "Luna", "girl", "Alden", "boy", 4, 8),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale quest story world with magnetic trouble and pace.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--friend")
    ap.add_argument("--companion")
    ap.add_argument("--pace", type=int, choices=list(range(1, 9)))
    ap.add_argument("--patience", type=int, choices=list(range(1, 9)))
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
    combos = valid_combos()
    if args.quest and args.charm and (args.quest, args.charm) not in combos:
        raise StoryError("That quest and charm do not make a magnetic problem worth telling.")
    if args.pace is not None and not (PACE_MIN <= args.pace <= PACE_MAX):
        raise StoryError("Pace must be between 2 and 8 for this story world.")
    quest, charm = rng.choice(sorted(combos))
    gender = "girl" if rng.random() < 0.5 else "boy"
    cgender = "boy" if gender == "girl" else "girl"
    friend = args.friend or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(BOY_NAMES if cgender == "boy" else GIRL_NAMES)
    pace = args.pace if args.pace is not None else rng.randint(4, 8)
    patience = args.patience if args.patience is not None else rng.randint(3, 8)
    return StoryParams(quest, charm, friend, gender, companion, cgender, patience, pace)


def generate(params: StoryParams) -> StorySample:
    quest = QUESTS[params.quest]
    charm = CHARMS[params.charm]
    friend = Friend(params.friend_name, params.friend_name, params.patience, params.friend_pace)
    companion = Friend(params.companion_name, params.companion_name, max(1, params.patience - 1), max(1, params.friend_pace - 2), brave=False)
    world = tell(quest, charm, friend, companion, params.patience)
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


ASP_RULES = r"""
magnetic_problem(Q, C) :- quest(Q), charm(C), quest_iron(Q), magnetic(C).
bad_ending(Q, C) :- magnetic_problem(Q, C).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, t))
        if "iron" in q.tags:
            lines.append(asp.fact("quest_iron", qid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.magnetic:
            lines.append(asp.fact("magnetic", cid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_bad_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show bad_ending/2."))
    return sorted(set(asp.atoms(model, "bad_ending")))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_bad_pairs()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP/combo parity.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show bad_ending/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible quest/charm pairs:")
        for q, c in valid_combos():
            print(f"  {q:6} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.friend_name} & {p.companion_name}: {p.quest}, {p.charm}, pace={p.friend_pace}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
