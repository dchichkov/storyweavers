#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/beak_juggle_utensil_magic_mystery_to_solve.py
===============================================================================

A small fable-like story world about a curious bird-child, a shiny utensil,
a little piece of magic, a mystery to solve, and a friendship that grows when
the friends choose patience over pride.

The seed words are woven into the world model:
- beak
- juggle
- utensil

The core story pattern is:
1. a magical household mystery appears,
2. a friend wants to juggle the shiny utensil for fun,
3. that choice causes trouble,
4. the pair solve the mystery together,
5. friendship is strengthened by the fix.

The world is deliberately small and classical: a few typed entities, physical
meters and emotional memes, a forward causal simulation, and a prose renderer
that narrates the state change rather than a frozen summary.
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        c.facts = copy.deepcopy(self.facts)
        return c

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


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    mood: str


@dataclass(frozen=True)
class Bird:
    id: str
    kind: str
    beak: str
    gift: str
    curiosity: str


@dataclass(frozen=True)
class Mystery:
    id: str
    sign: str
    source: str
    lesson: str


@dataclass(frozen=True)
class Utensil:
    id: str
    label: str
    shine: str
    can_juggle: bool = True


@dataclass(frozen=True)
class Magic:
    id: str
    spark: str
    effect: str
    helps: str
    risky: bool = False


@dataclass(frozen=True)
class OutcomePlan:
    id: str
    sense: int
    text: str
    answer: str


SETTINGS = {
    "orchard": Setting("orchard", "the moonlit orchard", "quiet"),
    "garden": Setting("garden", "the old garden", "still"),
    "riverbank": Setting("riverbank", "the riverbank path", "murmuring"),
}

BIRDS = {
    "pip": Bird("Pip", "bird", "beak", "a small song", "kind"),
    "lark": Bird("Lark", "bird", "beak", "a bright note", "gentle"),
    "rook": Bird("Rook", "bird", "beak", "a clever tune", "watchful"),
}

MYSTERIES = {
    "silver_sound": Mystery("silver_sound", "a silver sound in the leaves", "a dropped spoon", "someone's magic charm"),
    "missing_key": Mystery("missing_key", "a missing key by the roots", "a nest tucked under moss", "patience and looking closely"),
    "glow_crumbs": Mystery("glow_crumbs", "glow crumbs on the path", "a pocket of moon magic", "sharing the find"),
}

UTENSILS = {
    "spoon": Utensil("spoon", "a spoon", "silver shine"),
    "ladle": Utensil("ladle", "a ladle", "bright shine"),
    "fork": Utensil("fork", "a fork", "small shine"),
}

MAGIC = {
    "moon": Magic("moon", "moon-glow", "soft light", "makes hidden things easier to see"),
    "friendship": Magic("friendship", "warm magic", "steady courage", "helps friends listen and share"),
}

ACTIONS = {
    "juggle": "juggle",
    "polish": "polish",
    "search": "search",
}

RESPONSES = {
    "gentle_fix": OutcomePlan("gentle_fix", 3, "lifted the spoon carefully, and the glow settled into a path they could follow", "lifted the utensil carefully"),
    "share_purpose": OutcomePlan("share_purpose", 2, "used the utensil to scoop dew from a leaf and reveal the hidden clue", "used the utensil to reveal the clue"),
}

NAMES = ["Pip", "Lark", "Rook", "Mina", "Nilo", "Tavi", "Juno", "Mara"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for b in BIRDS:
            for m in MYSTERIES:
                for u in UTENSILS:
                    out.append((s, b, m, u))
    return out


@dataclass
@dataclass
class StoryParams:
    setting: str
    bird: str
    mystery: str
    utensil: str
    magic: str
    friend: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about a magical mystery and a friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--utensil", choices=UTENSILS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--friend")
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
              and (args.bird is None or c[1] == args.bird)
              and (args.mystery is None or c[2] == args.mystery)
              and (args.utensil is None or c[3] == args.utensil)]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    s, b, m, u = rng.choice(combos)
    return StoryParams(s, b, m, u, args.magic or rng.choice(sorted(MAGIC)), args.friend or rng.choice(NAMES))


def _r_mysterious_glow(world: World) -> list[str]:
    out = []
    mystery = world.facts["mystery"]
    for e in list(world.entities.values()):
        sig = ("glow", mystery.id)
        if e.role == "mystery" and e.meters["mystery"] >= THRESHOLD and sig not in world.fired:
            world.fired.add(sig)
            world.get("setting").meters["mystery"] += 1
            out.append("__mystery__")
    return out


def _r_tension(world: World) -> list[str]:
    out = []
    b = world.get("bird")
    f = world.get("friend")
    if b.memes["worry"] >= THRESHOLD and f.memes["pride"] >= THRESHOLD:
        sig = ("tension",)
        if sig not in world.fired:
            world.fired.add(sig)
            f.memes["stuck"] += 1
            out.append("__tension__")
    return out


CAUSAL_RULES = [Rule("mystery_glow", _r_mysterious_glow), Rule("tension", _r_tension)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("utensil").meters["juggled"] += 1
    sim.get("friend").memes["pride"] += 1
    propagate(sim, narrate=False)
    return {"confused": sim.get("friend").memes["worry"] >= THRESHOLD,
            "revealed": sim.get("setting").meters["mystery"] >= THRESHOLD}


def tell(setting: Setting, bird: Bird, mystery: Mystery, utensil: Utensil, magic: Magic, friend_name: str) -> World:
    w = World()
    hero = w.add(Entity("bird", kind="character", type="bird", label=bird.id, role="seeker", traits=["gentle"], attrs={"beak": bird.beak}))
    friend = w.add(Entity("friend", kind="character", type="child", label=friend_name, role="friend", traits=["loyal"]))
    setup = w.add(Entity("setting", type="setting", label=setting.place))
    clue = w.add(Entity("mystery", type="mystery", label=mystery.sign, role="mystery"))
    tool = w.add(Entity("utensil", type="utensil", label=utensil.label))
    spark = w.add(Entity("magic", type="magic", label=magic.spark))
    w.facts.update(setting=setting, bird=hero, friend=friend, mystery=mystery, utensil=utensil, magic=magic, tool=tool)

    hero.memes["care"] += 1
    friend.memes["joy"] += 1
    clue.meters["mystery"] += 1
    spark.meters["magic"] += 1

    w.say(f"In {setting.place}, {bird.id} the little bird listened with a sharp beak and kind eyes.")
    w.say(f"Beside {bird.id} was {friend_name}, who liked to share every small wonder and every song.")
    w.say(f"One dusk they found {mystery.sign}, and {magic.spark} flickered where the leaves ought to have been quiet.")
    w.para()
    w.say(f"{friend_name} saw {utensil.label} and said it would be funny to juggle the utensil just to make the mystery dance.")
    w.say(f"But {bird.id} warned that a shiny utensil can slip, and magic should be handled with care.")

    friend.memes["pride"] += 1
    w.get("mystery").meters["mystery"] += 1
    predict_info = predict(w)
    w.facts["predict"] = predict_info
    if predict_info["confused"]:
        friend.memes["worry"] += 1
    propagate(w, narrate=False)

    w.para()
    if predict_info["revealed"]:
        w.say(f"At last, {bird.id} used the {bird.beak} to nudge a leaf aside, and the mystery became clear.")
        w.say(f"The hidden clue was simple: {mystery.lesson}.")
        w.say(f"{friend_name} set the utensil down, and together the friends chose to search rather than show off.")
        w.say(f"Then the magic changed from puzzling to gentle, and their friendship grew warmer than the moonlight.")
    else:
        w.say(f"They paused, listened, and then found that even a small mystery can be solved by looking again.")
        w.say(f"The friends shared the work, and {friend_name} put the utensil down so the magic could settle.")
        w.say(f"By dawn they understood the clue, and their friendship had become steadier and brighter.")

    w.facts["outcome"] = "solved"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story for a young child that includes the words "{f["bird"].attrs["beak"]}", "juggle", and "{f["utensil"].label}".',
        f"Tell a gentle mystery story where {f['bird'].label} and {f['friend'].label} solve a magical clue together and learn about friendship.",
        f"Write a small fable about a bird with a beak, a shiny utensil, and a mystery that is solved without boasting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bird = f["bird"]
    friend = f["friend"]
    mystery = f["mystery"]
    utensil = f["utensil"]
    magic = f["magic"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {bird.label} and {friend.label}. They are friends who face a small mystery together."
        ),
        QAItem(
            question=f"What did {friend.label} want to do with the {utensil.label}?",
            answer=f"{friend.label} wanted to juggle the utensil because it looked shiny and fun. But that choice could have made the mystery harder to solve."
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"They slowed down, looked carefully, and let {bird.label} use a beak and patient eyes to notice the clue. Then the magic turned from strange to kind."
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem("What is a beak?", "A beak is the hard mouth part on a bird. Birds use it to peck, pick things up, and explore."),
    QAItem("What is a utensil?", "A utensil is a tool used for eating or cooking, like a spoon or fork. It is useful, but it is not a toy for juggling."),
    QAItem("What is a mystery?", "A mystery is something that is not understood yet. People solve a mystery by looking, thinking, and asking questions."),
    QAItem("What is friendship?", "Friendship is when friends care about one another, share, and help each other. Good friends are kind when something is confusing."),
    QAItem("Why should magic be handled carefully in a fable?", "In a fable, magic often teaches a lesson. It works best when the characters are patient and respectful."),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


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
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BIRDS:
        lines.append(asp.fact("bird", bid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for uid in UTENSILS:
        lines.append(asp.fact("utensil", uid))
    for mid in MAGIC:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, B, M, U) :- setting(S), bird(B), mystery(M), utensil(U).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, bird=None, mystery=None, utensil=None, magic=None, friend=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection() -> str:
    return "(No story: the requested choices do not make a coherent little fable.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], BIRDS[params.bird], MYSTERIES[params.mystery], UTENSILS[params.utensil], MAGIC[params.magic], params.friend)
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
    StoryParams("orchard", "pip", "silver_sound", "spoon", "moon", "Mina"),
    StoryParams("garden", "lark", "missing_key", "ladle", "friendship", "Nilo"),
    StoryParams("riverbank", "rook", "glow_crumbs", "fork", "moon", "Tavi"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
