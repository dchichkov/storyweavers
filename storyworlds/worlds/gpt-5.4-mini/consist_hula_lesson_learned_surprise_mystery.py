#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/consist_hula_lesson_learned_surprise_mystery.py
===============================================================================

A standalone story world for a tiny mystery: a child follows clues, a surprising
truth is revealed, and the lesson learned is that a good mystery can be solved by
looking carefully at what things consist of.

Seed words and style:
- consist
- hula
- Features: Lesson Learned, Surprise
- Style: Mystery

The world model keeps track of typed entities with physical meters and emotional
memes. The prose is driven by state changes: a clue hunt begins, suspicious
details accumulate, a surprise explanation appears, and the ending shows what
changed.
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    cover: str
    mood: str
    hidey: str


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    type: str
    surprise: str
    consists_of: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Object:
    id: str
    label: str
    phrase: str
    suspicious: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Insight:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    scout = world.get("child")
    for obj in world.entities.values():
        if obj.kind != "thing" or not obj.suspicious:
            continue
        sig = ("suspect", obj.id)
        if sig in world.fired:
            continue
        if obj.meters["seen"] >= THRESHOLD:
            world.fired.add(sig)
            scout.memes["curiosity"] += 1
            scout.memes["unease"] += 1
            out.append("__suspect__")
    return out


def _r_find_hidden(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    box = world.get("box")
    if clue.meters["examined"] < THRESHOLD:
        return out
    sig = ("hidden", box.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    box.meters["opened"] += 1
    clue.meters["revealed"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("suspicion", "social", _r_suspicion),
    Rule("hidden", "physical", _r_find_hidden),
]


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


def clue_at_risk(clue: Clue, obj: Object) -> bool:
    return clue.type in obj.label or obj.suspicious


def sensible_insights() -> list[Insight]:
    return [x for x in INSIGHTS.values() if x.sense >= SENSE_MIN]


def best_insight() -> Insight:
    return max(INSIGHTS.values(), key=lambda x: x.sense)


def mystery_strength(delay: int) -> int:
    return 1 + delay


def can_solve(insight: Insight, delay: int) -> bool:
    return insight.power >= mystery_strength(delay)


def tell_hidden_truth(world: World, child: Entity, clue: Clue, obj: Object) -> None:
    world.say(
        f"{child.id} noticed that the {obj.label} seemed odd in the quiet room. "
        f"{clue.phrase}."
    )
    world.say(
        f"{child.id} wondered what the mystery could consist of, because the clues "
        f"did not fit the first guess."
    )


def inspect(world: World, child: Entity, clue: Clue, obj: Object) -> None:
    child.memes["focus"] += 1
    clue_entity = world.get("clue")
    clue_entity.meters["examined"] += 1
    obj.meters["seen"] += 1
    world.say(
        f"{child.id} leaned closer and looked again. {clue.phrase.capitalize()} "
        f"made the room feel like a mystery."
    )
    if obj.label == "hula hoop":
        world.say(
            f"The bright ring was a hula hoop, but the way it was tied with ribbon "
            f"made it look like something else at first."
        )


def ask_about(world: World, child: Entity, parent: Entity, obj: Object) -> None:
    world.say(
        f'"{parent.id}, what does this thing consist of?" {child.id} asked. '
        f'"It looks important."'
    )
    parent.memes["attention"] += 1


def surprise_reveal(world: World, parent: Entity, clue: Clue, obj: Object) -> None:
    world.say(
        f"Then came the surprise: {obj.label} was not a secret at all. "
        f"It was {obj.phrase}, and the hidden ribbon was only part of a game."
    )
    world.say(
        f"{clue.surprise.capitalize()}, {obj.label} had been waiting on purpose."
    )


def lesson(world: World, child: Entity, parent: Entity, clue: Clue, obj: Object) -> None:
    child.memes["understanding"] += 1
    child.memes["joy"] += 1
    child.memes["unease"] = 0.0
    world.say(
        f"{child.id} smiled. The lesson learned was simple: when a mystery seems "
        f"strange, look carefully at what it consists of before jumping to a guess."
    )
    world.say(
        f"At the end, {child.id} could tell that the {obj.label} was just a playful "
        f"surprise, and the room felt calm again."
    )


def solve_fail(world: World, child: Entity, parent: Entity, clue: Clue, obj: Object) -> None:
    world.say(
        f"{parent.id} came over and gently showed {child.id} that the answer was "
        f"too tricky to guess from far away."
    )
    world.say(
        f"The clue was still confusing, and the mystery stayed unsolved for the moment."
    )


RULES = [
    Rule("inspect", "mystery", lambda world: []),
]


def tell(setting: Setting, clue: Clue, obj: Object, insight: Insight,
         child_name: str = "Mina", child_type: str = "girl",
         parent_name: str = "Mom", parent_type: str = "mother",
         delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="parent", label="the parent"))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label))
    box = world.add(Entity(id="box", type="thing", label=obj.label, attrs={"kind": obj.phrase}))
    world.facts["clue"] = clue
    world.facts["object"] = obj
    world.facts["insight"] = insight
    world.facts["delay"] = delay

    child.memes["curiosity"] = 1.0
    child.memes["unease"] = 0.0
    parent.memes["calm"] = 1.0

    world.say(
        f"One quiet afternoon, {child.id} wandered into {setting.place} where "
        f"the air felt {setting.mood}. {setting.cover}"
    )
    world.say(
        f"{child.id} found {clue.phrase}, and the little mystery seemed to hide "
        f"inside {setting.hidey}."
    )
    world.para()
    tell_hidden_truth(world, child, clue, obj)
    ask_about(world, child, parent, obj)
    inspect(world, child, clue, obj)
    world.para()

    if can_solve(insight, delay):
        surprise_reveal(world, parent, clue, obj)
        lesson(world, child, parent, clue, obj)
        clue_ent.meters["revealed"] = 1.0
    else:
        solve_fail(world, child, parent, clue, obj)

    world.facts.update(
        child=child, parent=parent, clue_ent=clue_ent, box=box,
        solved=can_solve(insight, delay), revealed=clue_ent.meters["revealed"] >= THRESHOLD
    )
    return world


SETTINGS = {
    "attic": Setting("attic", "the attic", "Dust floated in the beams, and old trunks made long shadows.", "the hush of old boxes", "a blanket pile"),
    "closet": Setting("closet", "the closet", "Coats hung like sleepy ghosts, and the shelves felt crowded.", "the hush of folded things", "a stack of scarves"),
    "garden": Setting("garden", "the garden shed", "The shed smelled like wet wood and bright paint.", "the smell of tools and stories", "a tangle of ribbon"),
}

CLUES = {
    "ribbon": Clue("ribbon", "a ribbon", "A ribbon peeked out from under the lid.", "ribbon", "it was only part of a surprise", "a ribbon and a small tag", {"mystery", "surprise"}),
    "note": Clue("note", "a note", "A note sat on the chair like a tiny secret.", "note", "it was a clue from a game", "a note with a folded corner", {"mystery"}),
    "footprints": Clue("footprints", "footprints", "Tiny footprints crossed the floor.", "footprints", "they were made during pretend play", "small prints and a trail", {"mystery"}),
}

OBJECTS = {
    "hula": Object("hula", "hula hoop", "a bright hula hoop with ribbon tied around it", suspicious=True),
    "basket": Object("basket", "picnic basket", "a picnic basket with a cloth tucked inside", suspicious=False),
    "box": Object("box", "cardboard box", "a cardboard box full of costume pieces", suspicious=True),
}

INSIGHTS = {
    "magnify": Insight("magnify", 3, 3, "looked closely and used the clues", "looked once, but that was not enough", "looked closely and solved the mystery", {"mystery"}),
    "guess": Insight("guess", 1, 1, "made a guess too quickly", "guessed too soon and got it wrong", "made a quick guess", {"mystery"}),
    "patient": Insight("patient", 2, 2, "waited and checked each clue", "waited, but still needed more clues", "waited and checked each clue", {"mystery", "lesson"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Theo", "Max", "Finn", "Eli", "Ben"]
TRAITS = ["careful", "curious", "thoughtful", "patient"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid, clue in CLUES.items():
            for oid, obj in OBJECTS.items():
                if clue_at_risk(clue, obj):
                    combos.append((sid, cid, oid))
    return combos


@dataclass
class StoryParams:
    setting: str
    clue: str
    object: str
    insight: str
    child: str
    child_type: str
    parent: str
    parent_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


KNOWLEDGE = {
    "hula": [("What is a hula hoop?", "A hula hoop is a big ring that people spin around their waist or play with in games.")],
    "mystery": [("What is a mystery?", "A mystery is something that is not clear at first, so you have to look for clues.")],
    "surprise": [("What is a surprise?", "A surprise is something unexpected that makes you say 'Oh!' when you learn it.")],
    "lesson": [("What does it mean to learn a lesson?", "It means you understand something better after what happened, and you remember it next time.")],
    "clue": [("What is a clue?", "A clue is a little hint that helps you figure something out.")],
    "consist": [("What does 'consist of' mean?", "If something consists of parts, it is made from those parts together.")],
}
KNOWLEDGE_ORDER = ["mystery", "surprise", "lesson", "clue", "hula", "consist"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story that includes the word "consist" and the word "{f["object"].label}".',
        f"Tell a short surprise mystery where {f['child'].id} asks what the {f['object'].label} consists of and learns the answer by looking closely.",
        f'Write a story in which a hula hoop is part of the mystery, and the ending teaches a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, clue, obj = f["child"], f["parent"], f["clue"], f["object"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, who finds a strange clue and tries to solve a small mystery with {parent.id}.",
        ),
        QAItem(
            question=f"What did {child.id} want to know about the mystery?",
            answer=f"{child.id} wanted to know what the {obj.label} consisted of. That question led {child.id} to look closer instead of guessing right away.",
        ),
    ]
    if f["solved"]:
        items.append(
            QAItem(
                question="What was the surprising answer?",
                answer=f"The surprise was that the {obj.label} was really a playful surprise, not something scary. The ribbon and clue were part of a game, so the mystery turned gentle instead of frightening.",
            )
        )
        items.append(
            QAItem(
                question="What lesson did {0} learn at the end?".format(child.id),
                answer=f"{child.id} learned that careful looking helps in a mystery, because clues can consist of ordinary things. That lesson learned made the ending calm and happy.",
            )
        )
    else:
        items.append(
            QAItem(
                question="Why did the mystery stay unsolved for a moment?",
                answer=f"The first guess was not enough, so the clue stayed confusing. {parent.id} had to help because the answer needed a closer look.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue"].tags) | set(world.facts["object"].__dict__.get("tags", set()))
    tags |= {"mystery", "lesson", "surprise", "consist"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            for q, a in KNOWLEDGE[key]:
                out.append(QAItem(q, a))
    return out


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "ribbon", "hula", "magnify", "Mina", "girl", "Mom", "mother", "curious", 0),
    StoryParams("closet", "note", "box", "patient", "Theo", "boy", "Dad", "father", "thoughtful", 0),
    StoryParams("garden", "footprints", "hula", "magnify", "Lily", "girl", "Mom", "mother", "careful", 1),
]


def explain_rejection(clue: Clue, obj: Object) -> str:
    if not clue_at_risk(clue, obj):
        return "(No story: the clue and object do not make a good mystery together.)"
    return "(No story: this combination is too thin to make a strong mystery.)"


def explain_insight(rid: str) -> str:
    r = INSIGHTS[rid]
    better = " / ".join(sorted(x.id for x in sensible_insights()))
    return f"(Refusing insight '{rid}': it is too weak for this storyworld. Try: {better}.)"


ASP_RULES = r"""
risk(C, O) :- clue(C), object(O), suspicious(O).
sensible(I) :- insight(I), sense(I, S), sense_min(M), S >= M.
solved :- chosen_insight(I), power(I, P), delay(D), P >= 1 + D.
surprise :- chosen_object(O), suspicious(O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.suspicious:
            lines.append(asp.fact("suspicious", oid))
    for iid, ins in INSIGHTS.items():
        lines.append(asp.fact("insight", iid))
        lines.append(asp.fact("sense", iid, ins.sense))
        lines.append(asp.fact("power", iid, ins.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("", "#show risk/2.\n#show sensible/1.\n#show solved/0."))
    sens = set(asp.atoms(model, "sensible"))
    if sens == {(i,) for i in asp_sensible()}:
        print("OK: ASP sensible gate parsed.")
    else:
        rc = 1
        print("MISMATCH in ASP sensible gate.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generate() produced empty story.")
    else:
        print("OK: generate() smoke test produced a story.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world with a surprise and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--insight", choices=INSIGHTS)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.insight and INSIGHTS[args.insight].sense < SENSE_MIN:
        raise StoryError(explain_insight(args.insight))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.object_ is None or c[2] == args.object_)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, obj = rng.choice(sorted(combos))
    insight = args.insight or rng.choice(sorted(x.id for x in sensible_insights()))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    parent = args.parent or ("Mom" if parent_type == "mother" else "Dad")
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    trait = rng.choice(TRAITS)
    return StoryParams(setting, clue, obj, insight, child, child_type, parent, parent_type, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], OBJECTS[params.object], INSIGHTS[params.insight],
                 params.child, params.child_type, params.parent, params.parent_type, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show risk/2.\n#show sensible/1.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible insights: {', '.join(asp_sensible())}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.clue} / {p.object} / {p.insight}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
