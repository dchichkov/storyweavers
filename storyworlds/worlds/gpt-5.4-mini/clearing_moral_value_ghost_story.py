#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clearing_moral_value_ghost_story.py
===================================================================

A standalone storyworld for a small ghost-story domain: a child in a forest
clearing, a harmless spooky encounter, and a moral turn about telling the truth,
sharing, or helping someone who seems frightening.

The world keeps the classic Storyweavers shape:
- typed entities with physical meters and emotional memes
- a simple causal engine
- a reasonableness gate
- an ASP twin for parity checks
- story, prompts, story QA, and world QA
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SCARE_START = 2.0


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
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Clearing:
    id: str
    label: str
    dark_spot: str
    peace: str
    open_to_help: bool = True

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
class Ghost:
    id: str
    label: str
    sound: str
    need: str
    kind: str
    scared_by_truth: bool = True
    can_be_helped: bool = True

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
class MoralChoice:
    id: str
    prompt: str
    honest: bool
    helpful: bool
    value: str
    resolution: str
    lesson: str
    sense: int

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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    g = world.get("ghost")
    child = world.get("child")
    if g.meters["presence"] >= THRESHOLD and ("fear", "child") not in world.fired:
        world.fired.add(("fear", "child"))
        child.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_truth_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    if child.memes["honesty"] >= THRESHOLD and ghost.meters["presence"] >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.meters["unrest"] = max(0.0, ghost.meters["unrest"] - 1.0)
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("calm", "social", _r_truth_calm)]


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


def reasonableness(choice: MoralChoice, clearing: Clearing, ghost: Ghost) -> bool:
    if choice.sense < 2:
        return False
    if not clearing.open_to_help and choice.helpful:
        return False
    if ghost.kind not in {"lost", "lonely", "gentle"}:
        return False
    return True


def choose_outcome(choice: MoralChoice, ghost: Ghost) -> str:
    if choice.honest and choice.helpful:
        return "kind"
    if choice.honest:
        return "truth"
    if choice.helpful:
        return "help"
    return "fear"


def predict(world: World, choice: MoralChoice) -> dict:
    sim = world.copy()
    sim.get("child").memes["honesty"] += 1 if choice.honest else 0
    sim.get("child").memes["helpfulness"] += 1 if choice.helpful else 0
    if choice.honest and choice.helpful:
        sim.get("ghost").meters["unrest"] = max(0.0, sim.get("ghost").meters["unrest"] - 1)
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "calm": sim.get("ghost").meters["unrest"],
    }


def tell_setup(world: World, child: Entity, clearing: Clearing, ghost: Ghost) -> None:
    world.say(
        f"At the edge of the woods, {child.id} stepped into a moonlit clearing. "
        f"{clearing.peace} But near the old stone, a ghost waited with a soft, sad sound."
    )
    world.say(
        f'{ghost.label} went "brrr" in the dark, and {child.id} froze.'
    )


def tempt(world: World, child: Entity, ghost: Ghost) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} wanted to run away, but also wanted to know why the ghost sounded so lonely."
    )


def warn(world: World, child: Entity, ghost: Ghost, choice: MoralChoice) -> None:
    pred = predict(world, choice)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_calm"] = pred["calm"]
    world.say(
        f'{child.id} swallowed hard and said, "{choice.prompt}"'
    )


def act(world: World, child: Entity, ghost: Ghost, choice: MoralChoice) -> None:
    if choice.honest:
        child.memes["honesty"] += 1
    if choice.helpful:
        child.memes["helpfulness"] += 1
    if choice.value == "truth":
        world.say(
            f'{child.id} told the truth: the fallen lantern had scared {child.pronoun("object")}.'
        )
    elif choice.value == "help":
        world.say(
            f"{child.id} took a careful step closer and offered help instead of hiding."
        )
    else:
        world.say(
            f"{child.id} kept quiet and stayed stiff as a board."
        )
    propagate(world, narrate=False)


def resolve(world: World, child: Entity, ghost: Ghost, choice: MoralChoice) -> None:
    if choice.honest and choice.helpful:
        ghost.meters["unrest"] = 0.0
        child.memes["fear"] = 0.0
        child.memes["pride"] += 1
        world.say(
            f'The ghost sighed, because it had only been looking for help. '
            f'{child.id} found the lost ribbon and set it beside the little grave marker.'
        )
        world.say(
            f"The ghost drifted into a soft silver smile, and the clearing felt warm again."
        )
    elif choice.honest:
        ghost.meters["unrest"] = 0.0
        world.say(
            f"The ghost nodded at the truth, and its sad sound turned gentle."
        )
    elif choice.helpful:
        ghost.meters["unrest"] = 0.0
        world.say(
            f"The ghost took the help, and the dark place grew less spooky at once."
        )
    else:
        world.say(
            f"The ghost stayed lonely, and the clearing stayed cold until {child.id} finally called for a grown-up."
        )


def moral_turn(world: World, child: Entity, ghost: Ghost, choice: MoralChoice) -> None:
    if choice.honest and choice.helpful:
        world.say(
            f'Then {child.id} remembered a better way: tell the truth and lend a hand.'
        )
    elif choice.honest:
        world.say(f"{child.id} chose to be honest.")
    elif choice.helpful:
        world.say(f"{child.id} chose to help.")
    else:
        world.say(f"{child.id} chose fear over kindness.")


def tell(clearing: Clearing, ghost: Ghost, choice: MoralChoice, name: str = "Mia",
         gender: str = "girl", parent: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=name, kind="character", type=gender, role="child"))
    grownup = world.add(Entity(id="Parent", kind="character", type=parent, label="the parent", role="parent"))
    world.add(Entity(id="clearing", kind="thing", type="place", label=clearing.label))
    world.add(Entity(id="ghost", kind="thing", type="ghost", label=ghost.label))
    child.memes["fear"] = 0.0
    child.memes["honesty"] = 0.0
    child.memes["helpfulness"] = 0.0

    tell_setup(world, child, clearing, ghost)
    world.para()
    tempt(world, child, ghost)
    warn(world, child, ghost, choice)
    act(world, child, ghost, choice)
    world.para()
    moral_turn(world, child, ghost, choice)
    resolve(world, child, ghost, choice)
    world.say(
        f"In the end, {child.id} walked out of the clearing with a steadier heart, "
        f"knowing a kind truth was brighter than any scare."
    )
    outcome = choose_outcome(choice, ghost)
    world.facts.update(
        child=child, parent=grownup, clearing=clearing, ghost=ghost, choice=choice,
        outcome=outcome, resolved=(choice.honest or choice.helpful),
    )
    return world


CLEARINGS = {
    "moon": Clearing("moon", "a moonlit clearing", "the dark ring of trees", "silver grass"),
    "pine": Clearing("pine", "a pine clearing", "the whispering trees", "soft needles"),
    "meadow": Clearing("meadow", "a meadow clearing", "the hush near the brook", "tall grass"),
}

GHOSTS = {
    "lost": Ghost("lost", "the little ghost", "brrr", "its lost ribbon", "lost"),
    "lonely": Ghost("lonely", "the shy ghost", "ooo", "a friend", "lonely"),
    "gentle": Ghost("gentle", "the pale ghost", "hmm", "a lantern glow", "gentle"),
}

CHOICES = {
    "truth_kind": MoralChoice("truth_kind", "I can tell the truth and help you.", True, True, "kind", "helped the ghost and told the truth", "tell the truth and help", 3),
    "truth": MoralChoice("truth", "I should tell the truth.", True, False, "truth", "told the truth", "telling the truth matters", 3),
    "help": MoralChoice("help", "I can help.", False, True, "help", "offered help", "helping matters", 3),
    "hide": MoralChoice("hide", "I should hide.", False, False, "fear", "hid from the ghost", "fear wins", 2),
}

CHILD_NAMES = ["Mia", "Ava", "Noah", "Eli", "Lily", "Ben", "Zoe", "Sam"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for c in CLEARINGS:
        for g in GHOSTS:
            for ch in CHOICES.values():
                if reasonableness(ch, CLEARINGS[c], GHOSTS[g]):
                    combos.append((c, g, ch.id))
    return combos


@dataclass
@dataclass
class StoryParams:
    clearing: str
    ghost: str
    choice: str
    name: str
    gender: str
    parent: str
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
    ap = argparse.ArgumentParser(description="A ghost-story world in a clearing with a moral turn.")
    ap.add_argument("--clearing", choices=CLEARINGS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
              if (args.clearing is None or c[0] == args.clearing)
              and (args.ghost is None or c[1] == args.ghost)
              and (args.choice is None or c[2] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    clearing, ghost, choice = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(clearing, ghost, choice, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(CLEARINGS[params.clearing], GHOSTS[params.ghost], CHOICES[params.choice],
                 params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that takes place in {f["clearing"].label} and includes the word "clearing".',
        f"Tell a gentle spooky story where {f['child'].id} meets {f['ghost'].label} and learns to be honest and kind.",
        f"Write a short moral story in a clearing where a child chooses truth over fear and helps a lonely ghost.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, ghost, choice = f["child"], f["ghost"], f["choice"]
    return [
        ("Where does the story happen?",
         f"It happens in {f['clearing'].label}. The clearing makes the woods feel open, but still a little spooky at night."),
        ("What did {0} do?".format(child.id),
         f"{child.id} met {ghost.label} and chose {choice.lesson}. That choice changed the mood from scared to kinder."),
        ("How did the story end?",
         f"It ended with {child.id} walking away with a steadier heart and the clearing feeling less frightening. The moral was that honesty and kindness can calm a scary moment."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a clearing?",
         "A clearing is an open space in the woods where there are fewer trees, so moonlight can reach the ground."),
        ("Why do ghost stories feel spooky?",
         "Ghost stories feel spooky because they use dark places, strange sounds, and surprises to make you wonder what will happen next."),
        ("What is a moral in a story?",
         "A moral is the lesson a story teaches, like being honest, helpful, or brave in a good way."),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("moon", "lost", "truth_kind", "Mia", "girl", "mother"),
    StoryParams("pine", "lonely", "truth", "Noah", "boy", "father"),
    StoryParams("meadow", "gentle", "help", "Lily", "girl", "mother"),
]


ASP_RULES = r"""
valid(C, G, Ch) :- clearing(C), ghost(G), choice(Ch), reasonable(C, G, Ch).
reasonable(C, G, truth_kind) :- open_to_help(C), ghost_kind(G, lost).
reasonable(C, G, truth_kind) :- open_to_help(C), ghost_kind(G, lonely).
reasonable(C, G, truth_kind) :- open_to_help(C), ghost_kind(G, gentle).
reasonable(C, G, truth) :- open_to_help(C), ghost_kind(G, lost).
reasonable(C, G, truth) :- open_to_help(C), ghost_kind(G, lonely).
reasonable(C, G, truth) :- open_to_help(C), ghost_kind(G, gentle).
reasonable(C, G, help) :- open_to_help(C), ghost_kind(G, lost).
reasonable(C, G, help) :- open_to_help(C), ghost_kind(G, lonely).
reasonable(C, G, help) :- open_to_help(C), ghost_kind(G, gentle).
open_to_help(moon).
open_to_help(pine).
open_to_help(meadow).
ghost_kind(lost, lost).
ghost_kind(lonely, lonely).
ghost_kind(gentle, gentle).
choice(truth_kind).
choice(truth).
choice(help).
choice(hide).
clearing(moon).
clearing(pine).
clearing(meadow).
ghost(lost).
ghost(lonely).
ghost(gentle).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in CLEARINGS:
        lines.append(asp.fact("clearing", c))
        lines.append(asp.fact("open_to_help", c))
    for g, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", g))
        lines.append(asp.fact("ghost_kind", g, ghost.kind))
    for ch in CHOICES:
        lines.append(asp.fact("choice", ch))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in valid_combos().")
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def explain_rejection() -> str:
    return "(No story: that combination does not fit this ghost-story world.)"


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
