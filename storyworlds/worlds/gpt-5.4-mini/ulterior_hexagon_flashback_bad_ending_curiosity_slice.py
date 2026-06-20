#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ulterior_hexagon_flashback_bad_ending_curiosity_slice.py
========================================================================================

A small slice-of-life storyworld about a child, a curious hexagon craft, an
ulterior motive, a flashback, and a bad ending that still feels grounded in
ordinary home life.

The world is intentionally tiny: a child notices a neat hexagon object, wants
something out of curiosity, remembers an earlier moment, and makes a choice with
an ulterior motive that leads to an ending that is disappointing but readable.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when run directly.
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
    meters: dict[str, float] = field(default_factory=lambda: {"wear": 0.0, "loss": 0.0, "share": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "hope": 0.0, "regret": 0.0, "warmth": 0.0})

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
class FlashbackArtifact:
    id: str
    label: str
    phrase: str
    color: str
    shape: str
    made_of: str
    has_memory: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Motive:
    id: str
    label: str
    secret: str
    risk: str
    reveal: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class EndState:
    id: str
    mood: str
    text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_wear(world: World) -> list[str]:
    out = []
    child = world.get("child")
    art = world.get("artifact")
    if child.meters["wear"] >= THRESHOLD and ("wear", art.id) not in world.fired:
        world.fired.add(("wear", art.id))
        child.memes["regret"] += 1
        out.append("__wear__")
    return out


def _r_loss(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["loss"] >= THRESHOLD and ("loss", child.id) not in world.fired:
        world.fired.add(("loss", child.id))
        child.memes["warmth"] -= 0.5
        out.append("__loss__")
    return out


CAUSAL_RULES = [Rule("wear", _r_wear), Rule("loss", _r_loss)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    emitted: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                emitted.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in emitted:
            world.say(s)
    return emitted


def peek_flashback(world: World, artifact: FlashbackArtifact) -> str:
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD:
        return ""
    return (
        f"{child.id} remembered the first time {artifact.phrase} had been placed on "
        f"the table, when everyone laughed at how neatly its {artifact.shape} edges "
        f"fit together."
    )


def confess_ulterior(world: World, motive: Motive, child: Entity, parent: Entity) -> None:
    child.memes["curiosity"] += 1
    child.memes["hope"] += 1
    world.say(
        f"At the kitchen table, {child.id} kept looking at the hexagon and said "
        f"{child.pronoun('possessive')} wish was simple, but there was an ulterior "
        f"reason too: {motive.secret}."
    )
    flash = peek_flashback(world, world.facts["artifact_cfg"])
    if flash:
        world.say(flash)


def ask(curiosity: World, child: Entity, artifact: FlashbackArtifact, parent: Entity) -> None:
    curiosity.say(
        f"{child.id} leaned closer to {artifact.label} and asked {parent.label_word} "
        f"why the six-sided shape looked so neat on the windowsill."
    )


def refuse_and_reach(world: World, child: Entity, artifact: FlashbackArtifact, motive: Motive) -> None:
    child.memes["curiosity"] += 1
    child.meters["wear"] += 1
    world.say(
        f"{child.id} said {child.pronoun('possessive')} wish out loud, but still "
        f"reached for it because {motive.risk} felt too tempting to leave alone."
    )
    propagate(world, narrate=False)


def reveal_bad_ending(world: World, child: Entity, parent: Entity, artifact: FlashbackArtifact, motive: Motive, ending: EndState) -> None:
    child.meters["loss"] += 1
    child.memes["regret"] += 1
    world.say(
        f"When {child.id} lifted {artifact.label}, the little paper border bent and a "
        f"corner tore. {parent.label_word.capitalize()} sighed, not angry, just tired, "
        f"because the neat thing had been meant to stay on display."
    )
    world.say(
        f"{child.id} had wanted to keep it for {motive.reveal}, but now the shape was "
        f"creased and the moment felt smaller. That was the bad ending: nothing broke "
        f"loudly, yet the favorite thing was no longer special."
    )
    world.say(ending.text)


def tell(artifact: FlashbackArtifact, motive: Motive, ending: EndState,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent"))
    art = world.add(Entity(id="artifact", type="thing", label=artifact.label, attrs={"shape": artifact.shape}))
    world.facts.update(child=child, parent=parent, artifact_cfg=artifact, motive_cfg=motive, ending_cfg=ending)

    world.say(
        f"On a quiet afternoon, {child.id} sat by the window while the house smelled "
        f"like tea and toast. On the table was {artifact.phrase}, a tiny hexagon "
        f"with clean edges and a calm shine."
    )
    ask(world, child, artifact, parent)

    world.para()
    confess_ulterior(world, motive, child, parent)

    world.para()
    refuse_and_reach(world, child, art if False else artifact, motive)
    reveal_bad_ending(world, child, parent, artifact, motive, ending)
    return world


THEMES = {
    "window": FlashbackArtifact("window", "paper hexagon", "a paper hexagon on the windowsill", "yellow", "hexagon", "paper", tags={"hexagon", "flashback"}),
    "fridge": FlashbackArtifact("fridge", "sticker hexagon", "a shiny hexagon sticker on the fridge", "blue", "hexagon", "sticker", tags={"hexagon"}),
    "table": FlashbackArtifact("table", "box hexagon", "a hexagon cut-out from a cereal box", "green", "hexagon", "cardboard", tags={"hexagon", "slice"}),
}

MOTIVES = {
    "save": Motive("save", "save it", "the child wanted to save the hexagon for later", "waiting was hard", "show a friend tomorrow", tags={"ulterior", "curiosity"}),
    "hide": Motive("hide", "hide it", "the child wanted to hide it before a sibling noticed", "sharing felt scary", "keep it as a secret treasure", tags={"ulterior"}),
    "trace": Motive("trace", "trace it", "the child wanted to trace its shape for homework", "borrowed things made the heart race", "copy the shape into a notebook", tags={"curiosity", "flashback"}),
}

ENDINGS = {
    "wilt": EndState("wilt", "bad", "The afternoon stayed quiet, but the good feeling did not come back."),
    "tear": EndState("tear", "bad", "By dinner time, the torn hexagon sat in a bowl on the counter, looking smaller than before."),
    "smudge": EndState("smudge", "bad", "A thumbprint stayed on the paper, and the child kept glancing back at it with a worried face."),
}

NAMES = ["Mina", "Owen", "Tessa", "Leo", "Nina", "Arlo", "Ruby", "Iris"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    motive: str
    ending: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    return [(t, m, e) for t in THEMES for m in MOTIVES for e in ENDINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a hexagon, curiosity, a flashback, and a bad ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.theme is None or c[0] == args.theme)
              and (args.motive is None or c[1] == args.motive)
              and (args.ending is None or c[2] == args.ending)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, motive, ending = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(theme, motive, ending, name, gender, parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the word "ulterior" and a hexagon object on a quiet afternoon.',
        f"Tell a small home story where {f['child'].id} feels curious about a hexagon, remembers an earlier moment, and has an ulterior reason for touching it.",
        f"Write a gentle but disappointing story ending where curiosity leads to a bad ending around a hexagon and a family keeps the mood calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, art, motive = f["child"], f["parent"], f["artifact_cfg"], f["motive_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} notice on the table?",
            answer=f"{child.id} noticed {art.phrase}. It looked neat and flat, which made the child curious right away."
        ),
        QAItem(
            question=f"Why was there an ulterior reason to reach for it?",
            answer=f"There was an ulterior reason because {motive.secret}. That reason mattered more than just looking, so the child kept reaching."
        ),
        QAItem(
            question="What made this story a bad ending?",
            answer=f"The hexagon got bent and torn when it was lifted, so the nice feeling disappeared. It was a bad ending because the favorite thing stopped being special."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a hexagon?", "A hexagon is a shape with six sides and six corners."),
        QAItem("What does curiosity mean?", "Curiosity is the feeling that makes someone want to look, ask, and learn more."),
        QAItem("What is a flashback in a story?", "A flashback is when the story remembers something that happened earlier."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], MOTIVES[params.motive], ENDINGS[params.ending], params.name, params.gender, params.parent)
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
valid(T, M, E) :- theme(T), motive(M), ending(E).
curious_child(C) :- child(C).
flashback_scene(T) :- theme(T), has_flashback(T).
bad_ending(E) :- ending(E), has_bad_ending(E).
ulterior(M) :- motive(M), has_ulterior(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t, obj in THEMES.items():
        lines.append(asp.fact("theme", t))
        if "flashback" in obj.tags:
            lines.append(asp.fact("has_flashback", t))
    for m, obj in MOTIVES.items():
        lines.append(asp.fact("motive", m))
        if "ulterior" in obj.tags:
            lines.append(asp.fact("has_ulterior", m))
    for e, obj in ENDINGS.items():
        lines.append(asp.fact("ending", e))
        lines.append(asp.fact("has_bad_ending", e))
    lines.append(asp.fact("child", "kid"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, motive=None, ending=None, name=None, gender=None, parent=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def explain_rejection() -> str:
    return "(No story: this world always allows the hexagon/curiosity/flashback pattern.)"


CURATED = [
    StoryParams("window", "save", "tear", "Mina", "girl", "mother"),
    StoryParams("fridge", "hide", "smudge", "Owen", "boy", "father"),
    StoryParams("table", "trace", "wilt", "Tessa", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.theme}, {p.motive}, {p.ending}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
