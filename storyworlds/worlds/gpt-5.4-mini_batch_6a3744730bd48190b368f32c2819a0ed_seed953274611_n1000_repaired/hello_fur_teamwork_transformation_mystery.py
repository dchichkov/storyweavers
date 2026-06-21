#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hello_fur_teamwork_transformation_mystery.py
=============================================================================

A standalone story world about a small mystery in a pet shop after closing time:
two children find a strange tuft of fur, follow clues together, and discover that
their suspicious "ghost" is really a kitten hiding in a costume. The story is
built from simulated state: clues, worry, teamwork, and a transformation that
turns a scary guess into a friendly surprise.

The world keeps the style close to mystery while staying child-facing and
concrete. It includes the seed words "hello" and "fur", and centers the features
Teamwork and Transformation.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Clue:
    id: str
    kind: str
    label: str
    reveal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class MysteryOutcome:
    id: str
    sense: int
    transformation: str
    ending: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["mystery"] < THRESHOLD:
            continue
        sig = ("spook", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in [x for x in world.entities.values() if x.role in {"detective", "helper"}]:
            kid.memes["worry"] += 1
        out.append("__mystery__")
    return out


CAUSAL_RULES = [Rule("spook", _r_spook)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def is_plausible(clue: Clue, outcome: MysteryOutcome) -> bool:
    return clue.kind in outcome.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id in SETTINGS:
        for c_id, clue in CLUES.items():
            for o_id, out in OUTCOMES.items():
                if is_plausible(clue, out):
                    combos.append((s_id, c_id, o_id))
    return combos


def story_start(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"Hello,"  # required seed word
        f" said {a.id} as the two friends stepped into {setting.place}. "
        f"{a.id} and {b.id} were looking for the source of a tiny mystery."
    )
    world.say(
        f"The place felt {setting.mood}, and something soft with {a.attrs['clue'].label_word} "
        f"on it had been left behind."
    )


def find_clue(world: World, a: Entity, b: Entity, clue: Clue) -> None:
    world.say(
        f"{a.id} spotted a little tuft of {clue.label} near the counter. "
        f"{b.id} held the flashlight lower so they could look together."
    )
    world.say(clue.reveal)


def teamwork(world: World, a: Entity, b: Entity) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"{a.id} read the marks on the floor while {b.id} checked the shelf, "
        f"and together they followed the trail instead of guessing too fast."
    )


def transform(world: World, target: Entity, outcome: MysteryOutcome) -> None:
    target.meters["mystery"] = 0
    target.tags.add("revealed")
    world.say(
        f"Then the strange shape changed in the light: the fuzzy bundle was not a ghost at all. "
        f"It was {outcome.transformation}."
    )
    world.say(outcome.ending)


def tell(setting: Setting, clue: Clue, outcome: MysteryOutcome,
         detective: str = "Mina", helper: str = "Toby",
         detective_type: str = "girl", helper_type: str = "boy") -> World:
    world = World()
    a = world.add(Entity(id=detective, kind="character", type=detective_type, role="detective"))
    b = world.add(Entity(id=helper, kind="character", type=helper_type, role="helper"))
    a.attrs["clue"] = clue
    b.attrs["clue"] = clue
    a.memes["worry"] = 0
    b.memes["worry"] = 0
    mystery = world.add(Entity(id="mystery", type="thing", label="mystery bundle"))
    mystery.meters["mystery"] = 1

    story_start(world, a, b, setting)
    world.para()
    find_clue(world, a, b, clue)
    teamwork(world, a, b)
    world.para()
    transform(world, mystery, outcome)

    world.facts.update(
        setting=setting,
        clue=clue,
        outcome=outcome,
        detective=a,
        helper=b,
        mystery=mystery,
        solved=True,
    )
    return world


SETTINGS = {
    "shop": Setting(id="shop", place="the pet shop after closing time", mood="quiet and echoey"),
    "hall": Setting(id="hall", place="the old hallway by the coat rack", mood="dim and whispery"),
    "shed": Setting(id="shed", place="the garden shed", mood="dusty and still"),
}

CLUES = {
    "fur": Clue(
        id="fur",
        kind="fur",
        label="fur",
        reveal="The fur was warm, soft, and definitely not a floating ghost beard.",
        tags={"fur", "animal"},
    ),
    "bell": Clue(
        id="bell",
        kind="bell",
        label="a tiny bell",
        reveal="A little bell chimed from inside the pile, like something small had walked by.",
        tags={"bell", "animal"},
    ),
    "pawprint": Clue(
        id="pawprint",
        kind="pawprint",
        label="a pawprint",
        reveal="A muddy pawprint pointed toward a curtain tucked in the corner.",
        tags={"pawprint", "animal"},
    ),
}

OUTCOMES = {
    "kitten": MysteryOutcome(
        id="kitten",
        sense=3,
        transformation="a kitten wearing a fluffy costume",
        ending="The kitten blinked, yawned, and rubbed its nose against their hands. The mystery had become a tiny purring friend.",
        tags={"fur", "bell", "pawprint", "animal"},
    ),
    "puppy": MysteryOutcome(
        id="puppy",
        sense=2,
        transformation="a puppy wrapped in a knotted blanket",
        ending="The puppy wagged once and sneezed. The scary shape turned into a laughing, tail-wagging surprise.",
        tags={"fur", "bell", "animal"},
    ),
    "raccoon": MysteryOutcome(
        id="raccoon",
        sense=2,
        transformation="a raccoon hiding under a scarf",
        ending="The raccoon peeked out, looked offended, and then calmly climbed onto the crate. The secret was solved at last.",
        tags={"fur", "pawprint", "animal"},
    ),
}

TRAITS = ["careful", "curious", "bold", "thoughtful"]


@dataclass
class StoryParams:
    setting: str
    clue: str
    outcome: str
    detective: str
    detective_type: str
    helper: str
    helper_type: str
    trait: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(setting="shop", clue="fur", outcome="kitten", detective="Mina", detective_type="girl", helper="Toby", helper_type="boy", trait="curious"),
    StoryParams(setting="hall", clue="pawprint", outcome="raccoon", detective="Lina", detective_type="girl", helper="Noah", helper_type="boy", trait="careful"),
    StoryParams(setting="shed", clue="bell", outcome="puppy", detective="Ava", detective_type="girl", helper="Eli", helper_type="boy", trait="thoughtful"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a young child that includes the words "hello" and "{f["clue"].label}".',
        f"Tell a gentle teamwork mystery where {f['detective'].id} and {f['helper'].id} follow a clue together and discover what the strange soft thing really is.",
        f"Write a child-friendly transformation story where a spooky guess turns into a friendly surprise in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["detective"], f["helper"]
    clue, outcome = f["clue"], f["outcome"]
    return [
        QAItem(
            question="What clue did they find?",
            answer=f"They found {clue.label}. It helped them follow the mystery instead of guessing wildly."
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"{a.id} and {b.id} worked together. One looked closely while the other held the light, and that teamwork helped them see the truth."
        ),
        QAItem(
            question="What was the strange thing really?",
            answer=f"It turned out to be {outcome.transformation}. The scary-looking shape changed into something small and friendly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue = f["clue"].kind
    items = {
        "fur": QAItem("What is fur?", "Fur is the soft hair that covers many animals. It helps keep them warm."),
        "animal": QAItem("Why do animals hide?", "Animals may hide when they are scared or want a quiet place to rest."),
        "bell": QAItem("What does a bell do?", "A bell makes a ringing sound when it moves or gets tapped."),
        "pawprint": QAItem("What is a pawprint?", "A pawprint is a mark left by an animal's foot."),
    }
    tags = set(f["outcome"].tags) | {clue}
    out: list[QAItem] = []
    for tag in ["fur", "bell", "pawprint", "animal"]:
        if tag in tags:
            out.append(items[tag])
    return out


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
    lines.append("== (3) World knowledge questions ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(clue: Clue, outcome: MysteryOutcome) -> str:
    if not is_plausible(clue, outcome):
        return f"(No story: {clue.label} does not fit that kind of transformation mystery.)"
    return "(No story: invalid combination.)"


def valid_story_params(args: argparse.Namespace, rng: random.Random) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    return [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.clue is None or c[1] == args.clue)
        and (args.outcome is None or c[2] == args.outcome)
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.outcome:
        clue, outcome = CLUES[args.clue], OUTCOMES[args.outcome]
        if not is_plausible(clue, outcome):
            raise StoryError(explain_rejection(clue, outcome))
    combos = valid_story_params(args, rng)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, outcome = rng.choice(sorted(combos))
    det_type = args.detective_type or rng.choice(["girl", "boy"])
    help_type = args.helper_type or ("boy" if det_type == "girl" else "girl")
    detective = args.detective or rng.choice(["Mina", "Lina", "Ava", "Nora", "Ivy"])
    helper = args.helper or rng.choice(["Toby", "Noah", "Eli", "Finn", "Max"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        clue=clue,
        outcome=outcome,
        detective=detective,
        detective_type=det_type,
        helper=helper,
        helper_type=help_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.outcome not in OUTCOMES:
        raise StoryError(f"Unknown outcome: {params.outcome}")
    world = tell(SETTINGS[params.setting], CLUES[params.clue], OUTCOMES[params.outcome],
                 detective=params.detective, helper=params.helper,
                 detective_type=params.detective_type, helper_type=params.helper_type)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with hello, fur, teamwork, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--detective")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


ASP_RULES = r"""
plausible(C,O) :- clue(C), outcome(O), clue_kind(C,K), outcome_tags(O,K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, clue.kind))
    for oid, out in OUTCOMES.items():
        lines.append(asp.fact("outcome", oid))
        for tag in sorted(out.tags):
            lines.append(asp.fact("outcome_tags", oid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show plausible/2."))
    return sorted(set(asp.atoms(model, "plausible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == {(c, o) for _, c, o in valid_combos()}:
        print("OK: ASP plausibility matches Python.")
    else:
        print("MISMATCH: ASP plausibility differs from Python.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show plausible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for setting, clue, outcome in valid_combos():
            print(setting, clue, outcome)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
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
            header = f"### {p.detective} & {p.helper}: {p.setting}, {p.clue}, {p.outcome}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
