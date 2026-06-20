#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/awning_pronoun_bravery_detective_story.py
=========================================================================

A small storyworld for a kid-sized detective tale: a lost clue hides under an
awning, a child must decide how brave to be, and a careful use of pronouns
helps the search stay clear.

The world is built around a tiny mystery:
- a detective child notices something under an awning,
- a worried helper hesitates,
- bravery changes the choice,
- the clue is recovered,
- and the ending proves what changed.

The story is not a frozen paragraph with swapped nouns. It simulates a few
stateful beats: attention, fear, courage, evidence, and a simple resolution.
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


THRESHOLD = 1.0
BRAVERY_MIN = 4.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"hidden": 0.0, "found": 0.0, "wet": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "worry": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    detail: str

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
class Clue:
    id: str
    label: str
    hiding: str
    reveal: str
    topic: str = "clue"

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
class Action:
    id: str
    verb: str
    result: str
    risk: str
    brave_gain: float
    success_need: float
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


SETTINGS = {
    "market": Setting("market", "the market street", "A striped awning shaded the little shop door."),
    "cafe": Setting("cafe", "the corner cafe", "A blue awning leaned over the window like a small roof."),
    "bookstore": Setting("bookstore", "the bookshop", "A red awning stretched above the front steps."),
}

CLUES = {
    "button": Clue("button", "a brass button", "wedged under the awning seam", "clicked free with a tiny ping", topic="button"),
    "key": Clue("key", "a silver key", "stuck in the wet gutter under the awning", "slid into the detective's palm", topic="key"),
    "note": Clue("note", "a folded note", "caught behind the awning flap", "came loose when the flap was lifted", topic="note"),
}

ACTIONS = {
    "peek": Action("peek", "peek under the awning", "looked carefully beneath the awning", "the clue was easy to miss", 1.0, 1.0, {"look"}),
    "lift": Action("lift", "lift the awning flap", "raised the flap with steady hands", "the flap might snap back", 2.0, 2.0, {"touch"}),
    "reach": Action("reach", "reach into the shadow", "stretched into the dark space", "it felt a little scary", 3.0, 3.0, {"brave"}),
}

DETECTIVES = {
    "girl": ["Mia", "Lina", "Nora", "Zoe", "Ada"],
    "boy": ["Leo", "Max", "Finn", "Eli", "Tom"],
}

HELPERS = {
    "girl": ["June", "Ivy", "Maya", "Ella"],
    "boy": ["Ben", "Noah", "Sam", "Owen"],
}

PARENTS = ["mother", "father"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    action: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CLUES:
            for aid in ACTIONS:
                combos.append((sid, cid, aid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective storyworld about an awning, a clue, and bravery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--detective")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
              and (args.clue is None or c[1] == args.clue)
              and (args.action is None or c[2] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, action = rng.choice(combos)
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or ("boy" if dg == "girl" else "girl")
    detective = args.detective or rng.choice(DETECTIVES[dg])
    helper = args.helper or rng.choice([n for n in HELPERS[hg] if n != detective])
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(setting, clue, action, detective, dg, helper, hg, parent)


def _story_view(world: World) -> tuple[Entity, Entity, Entity, Entity, Setting, Clue, Action]:
    d = world.get("detective")
    h = world.get("helper")
    p = world.get("parent")
    clue = world.get("clue")
    setting = world.facts["setting"]
    clue_cfg = world.facts["clue_cfg"]
    action = world.facts["action_cfg"]
    return d, h, p, clue, setting, clue_cfg, action


def _do_search(world: World, narrate: bool = True) -> None:
    d = world.get("detective")
    clue = world.get("clue")
    action = world.facts["action_cfg"]
    if d.memes["bravery"] < action.success_need:
        d.memes["worry"] += 1
    clue.meters["found"] += 1
    if narrate:
        world.say(f"{d.id} {action.result}.")
        world.say(f"That brave move helped the clue appear.")


def predict(world: World, action: Action) -> dict:
    sim = world.copy()
    d = sim.get("detective")
    clue = sim.get("clue")
    d.memes["bravery"] += action.brave_gain
    clue.meters["hidden"] = 0.0
    clue.meters["found"] = 1.0
    return {"found": clue.meters["found"] >= THRESHOLD}


def intro(world: World, d: Entity, h: Entity, setting: Setting) -> None:
    world.say(
        f"{d.id} was a little detective who liked quiet mysteries. "
        f"{h.id} stayed close, because {h.pronoun()} did not want to miss a thing."
    )
    world.say(
        f"One afternoon, they reached {setting.place}. {setting.detail}"
    )


def mystery(world: World, d: Entity, clue: Clue) -> None:
    d.memes["curiosity"] = d.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{d.id} noticed something odd: {clue.label} was hiding {clue.hiding}."
    )
    world.say(
        f'"That looks like a clue," {d.id} said. "A real detective should check it."'
    )


def warning(world: World, h: Entity, d: Entity, clue: Clue, action: Action) -> None:
    h.memes["worry"] += 1
    world.say(
        f"{h.id} bit {h.pronoun('possessive')} lip. "
        f'"It might be dark and slippery," {h.pronoun()} warned. '
        f'"We should be careful."'
    )
    world.facts["warning"] = f"{clue.label} could be hard to reach under the awning"


def brave_choice(world: World, d: Entity, action: Action) -> None:
    d.memes["bravery"] += action.brave_gain
    world.say(
        f"{d.id} took a breath and chose to {action.verb}."
    )


def recover(world: World, d: Entity, clue: Clue) -> None:
    clue.meters["hidden"] = 0.0
    clue.meters["found"] += 1
    d.memes["pride"] = d.memes.get("pride", 0.0) + 1
    world.say(
        f"The clue {clue.reveal}, and {d.id} held it up like proof."
    )


def resolve(world: World, d: Entity, h: Entity, p: Entity, clue: Clue) -> None:
    d.memes["bravery"] += 1
    h.memes["trust"] += 1
    world.say(
        f"{p.label_word.capitalize()} smiled when they saw the clue. "
        f'"Well done," {p.pronoun()} said. "You were brave, and you used your '
        f'words clearly."'
    )
    world.say(
        f"{h.id} relaxed at once, and {d.id} promised to keep being brave and careful."
    )


def tell(setting: Setting, clue_cfg: Clue, action: Action,
         detective: str = "Mia", detective_gender: str = "girl",
         helper: str = "Ben", helper_gender: str = "boy",
         parent: str = "mother") -> World:
    world = World()
    d = world.add(Entity("detective", kind="character", type=detective_gender, label=detective, role="detective"))
    h = world.add(Entity("helper", kind="character", type=helper_gender, label=helper, role="helper"))
    p = world.add(Entity("parent", kind="character", type=parent, label=f"the {parent}", role="parent"))
    clue = world.add(Entity("clue", type="thing", label=clue_cfg.label, role="clue"))
    clue.meters["hidden"] = 1.0
    d.memes["bravery"] = 2.0
    h.memes["worry"] = 1.0
    world.facts.update(setting=setting, clue_cfg=clue_cfg, action_cfg=action)

    intro(world, d, h, setting)
    world.para()
    mystery(world, d, clue_cfg)
    warning(world, h, d, clue_cfg, action)
    world.para()
    brave_choice(world, d, action)
    _do_search(world, narrate=True)
    recover(world, d, clue_cfg)
    world.para()
    resolve(world, d, h, p, clue_cfg)

    world.facts.update(detective=d, helper=h, parent=p, clue=clue,
                       outcome="found", brave=d.memes["bravery"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = f["detective"]
    clue = f["clue_cfg"]
    setting = f["setting"]
    return [
        f'Write a short detective story for a young child that includes the word "awning" and the word "pronoun".',
        f"Tell a gentle mystery where {d.id} finds a clue under {setting.place}, stays brave, and solves the case.",
        f"Write a story about bravery in a detective scene where a hidden {clue.label} is recovered from under an awning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    h = f["helper"]
    p = f["parent"]
    clue = f["clue_cfg"]
    setting = f["setting"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {d.id}, a little detective, and {h.id}, who helped watch the clue with {p.label_word} nearby."
        ),
        QAItem(
            question="Where was the clue hiding?",
            answer=f"The clue was hiding under the awning at {setting.place}. That shadowy spot made it feel like a real mystery."
        ),
        QAItem(
            question="What did bravery help {0} do?".format(d.id),
            answer=f"Bravery helped {d.id} {f['action_cfg'].verb} even though it felt a little scary. That is how the clue {clue.reveal}."
        ),
    ]
    items.append(
        QAItem(
            question="Why did the helper worry at first?",
            answer=f"{h.id} worried because the clue was hidden in a dark, slippery place. But after {d.id} moved bravely, the worry turned into trust."
        )
    )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an awning?",
            answer="An awning is a cover that sticks out over a door or window. It gives shade and helps keep a little rain off."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something scary or hard while staying calm. It does not mean you are never afraid."
        ),
        QAItem(
            question="What is a pronoun?",
            answer="A pronoun is a word like he, she, it, or they that takes the place of a name. It helps stories stay clear and easy to read."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:9} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("market", "key", "reach", "Mia", "girl", "Ben", "boy", "mother"),
    StoryParams("cafe", "button", "peek", "Leo", "boy", "Nora", "girl", "father"),
    StoryParams("bookstore", "note", "lift", "Ada", "girl", "Tom", "boy", "mother"),
]


def explain_rejection() -> str:
    return "(No story: this domain always has a clue to find, so the chosen options are incompatible.)"


def valid_for_asp() -> list[tuple[str, str, str]]:
    return valid_combos()


ASP_RULES = r"""
valid(S,C,A) :- setting(S), clue(C), action(A).

brave(D) :- bravery(D, B), bravery_need(A, N), chosen_action(A), B >= N.
found(C) :- chosen_clue(C), chosen_action(A), action_gain(A, G), brave(detective), G >= 1.
outcome(found) :- found(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_gain", aid, int(act.brave_gain)))
        lines.append(asp.fact("bravery_need", aid, int(act.success_need)))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        asp_set = set(asp.atoms(model, "valid"))
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    py_set = set(valid_for_asp())
    if asp_set != py_set:
        print("MISMATCH in ASP valid combos:")
        print("  only in asp:", sorted(asp_set - py_set))
        print("  only in py:", sorted(py_set - asp_set))
        return 1
    print(f"OK: ASP matches valid_combos() ({len(py_set)} combos).")

    sample = generate(CURATED[0])
    if not sample.story or "awning" not in sample.story:
        print("MISMATCH: smoke test story generation failed.")
        return 1
    print("OK: smoke test generated a story.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.clue and args.action:
        if (args.setting, args.clue, args.action) not in valid_combos():
            raise StoryError(explain_rejection())
    setting, clue, action = rng.choice(valid_combos())
    if args.setting:
        setting = args.setting
    if args.clue:
        clue = args.clue
    if args.action:
        action = args.action
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if detective_gender == "girl" else "girl")
    detective = args.detective or rng.choice(DETECTIVES[detective_gender])
    helper_pool = [n for n in HELPERS[helper_gender] if n != detective]
    helper = args.helper or rng.choice(helper_pool)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(setting, clue, action, detective, detective_gender, helper, helper_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        ACTIONS[params.action],
        params.detective,
        params.detective_gender,
        params.helper,
        params.helper_gender,
        params.parent,
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
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
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective} at {p.setting} ({p.clue}, {p.action})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
