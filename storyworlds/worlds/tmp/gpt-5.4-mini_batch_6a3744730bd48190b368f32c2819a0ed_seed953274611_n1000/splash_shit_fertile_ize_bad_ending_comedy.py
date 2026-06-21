#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/splash_shit_fertile_ize_bad_ending_comedy.py
=============================================================================

A tiny storyworld built from the seed words "splash", "shit", and
"fertile-ize", with a comedic style and a bad ending.

Premise
-------
Two children are in a backyard comedy bit with a hose, a garden patch, and a
too-confident bucket. One child tries to "fertile-ize" the garden with a silly
homemade mix, the other insists on a splashy shortcut, and the whole thing turns
into a muddy, smelly mess that the adults cannot fully save.

The world is intentionally small: one domain, one hazard, one ill-advised plan,
and one bad ending. The engine still models physical meters and emotional memes,
drives prose from world state, and provides grounded QA.

Contract notes
--------------
- Imports storyworlds/results.py eagerly.
- Imports storyworlds/asp.py lazily in ASP helpers only.
- Defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main.
- Supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp.
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
class Thing:
    id: str
    label: str
    kind: str = "thing"
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Reaction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    place: str = "backyard"
    tool: str = "hose"
    fertilizer: str = "comedy_mix"
    target: str = "garden"
    reaction: str = "shovel"
    child1: str = "Mia"
    child1_gender: str = "girl"
    child2: str = "Finn"
    child2_gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
    apply: callable


def _r_stink(world: World) -> list[str]:
    out = []
    if world.get("patch").meters["shit"] >= THRESHOLD:
        if ("stink",) not in world.fired:
            world.fired.add(("stink",))
            world.get("parent").memes["alarm"] += 1
            world.get("child1").memes["guilt"] += 1
            world.get("child2").memes["guilt"] += 1
            out.append("__stink__")
    return out


def _r_mess(world: World) -> list[str]:
    out = []
    if world.get("patch").meters["splash"] >= THRESHOLD and world.get("patch").meters["shit"] >= THRESHOLD:
        if ("mess",) not in world.fired:
            world.fired.add(("mess",))
            world.get("yard").meters["mess"] += 1
            world.get("child1").memes["embarrassment"] += 1
            world.get("child2").memes["embarrassment"] += 1
            out.append("__mess__")
    return out


CAUSAL_RULES = [Rule("stink", _r_stink), Rule("mess", _r_mess)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def best_reaction() -> Reaction:
    return max(REACTIONS.values(), key=lambda r: r.sense)


def sensible_reactions() -> list[Reaction]:
    return [r for r in REACTIONS.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for tool in TOOLS:
            for fertilizer in FERTILIZERS:
                if tool == "hose" and fertilizer == "comedy_mix":
                    combos.append((place, tool, fertilizer))
                if tool == "bucket" and fertilizer == "comedy_mix":
                    combos.append((place, tool, fertilizer))
    return combos


def _rename(a: str, avoid: str = "") -> str:
    pool = [n for n in NAMES if n != avoid]
    return a if a in pool else random.choice(pool)


def predict_bad(world: World) -> dict:
    sim = world.copy()
    do_splash(sim, narrate=False)
    return {"mess": sim.get("yard").meters["mess"], "shit": sim.get("patch").meters["shit"]}


def do_fertile_ize(world: World) -> None:
    patch = world.get("patch")
    patch.meters["fertile"] += 1
    patch.meters["shit"] += 1
    world.say(
        "One kid proudly announced they were going to fertile-ize the garden "
        "with a secret comedy mix. Unfortunately, the secret mix looked and smelled "
        "like a dare."
    )


def do_splash(world: World, narrate: bool = True) -> None:
    patch = world.get("patch")
    yard = world.get("yard")
    patch.meters["splash"] += 1
    yard.meters["splash"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity, parent: Entity, place: Thing) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned {place.label} into a "
        f"pretend science show."
    )
    world.say(
        f"{a.id} carried a little bucket. {b.id} carried a hose. "
        f'Both of them grinned like the joke had already started.'
    )


def warning(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    pred = predict_bad(world)
    parent.memes["unease"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{parent.label_word.capitalize()} frowned. "If you splash that stuff on '
        f'the patch, it will turn into a disgusting joke that nobody can un-smell," '
        f"{parent.pronoun()} said."
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(f'"Watch this," {a.id} said, and everybody could tell that was a bad sign.')


def accident(world: World, a: Entity, b: Entity) -> None:
    do_fertile_ize(world)
    do_splash(world)
    world.say(
        f"The mix splashed everywhere. A blob landed on the patch, and the hose "
        f"sent it right where it should not have gone."
    )
    world.say(
        f"Then the whole yard made a sour little face. Even the wind seemed to step back."
    )


def fail_response(world: World, parent: Entity, reaction: Reaction) -> None:
    world.get("yard").meters["mess"] += 2
    body = reaction.fail
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say("The mess only got bigger, which was rude of it.")


def ending(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["sad"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"In the end, the patch was brown, muddy, and absolutely not amused. "
        f"{parent.label_word.capitalize()} had to call for a real cleanup, and the "
        f"children had to help scrape slime off the wheelbarrow."
    )
    world.say(
        f"{a.id} and {b.id} promised to keep science jokes in a notebook from now on. "
        f"The garden did not become fertile-ized; it became famous for smelling bad."
    )


def tell(params: StoryParams) -> World:
    world = World()
    a = world.add(Entity(id=params.child1, kind="character", type=params.child1_gender, role="child"))
    b = world.add(Entity(id=params.child2, kind="character", type=params.child2_gender, role="child"))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent))
    place = world.add(Thing(id="place", label=params.place))
    yard = world.add(Thing(id="yard", label="the yard"))
    patch = world.add(Thing(id="patch", label="the garden patch"))

    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1

    setup(world, a, b, parent, place)
    world.para()
    warning(world, parent, a, b)
    defy(world, a, b)
    accident(world, a, b)
    world.para()
    fail_response(world, parent, REACTIONS[params.reaction])
    ending(world, parent, a, b)

    world.facts.update(
        child1=a, child2=b, parent=parent, place=place, yard=yard, patch=patch,
        reaction=REACTIONS[params.reaction], outcome="bad"
    )
    return world


PLACES = {"backyard": "backyard", "garden": "garden", "lot": "empty lot"}
TOOLS = {"hose": "hose", "bucket": "bucket"}
FERTILIZERS = {"comedy_mix": "comedy_mix", "homebrew": "homebrew"}
NAMES = ["Mia", "Finn", "Ava", "Noah", "Zoe", "Leo", "Ivy", "Max"]

REACTIONS = {
    "shovel": Reaction(
        id="shovel",
        sense=3,
        power=1,
        text="tried to shovel the slime away, but it just flung onto the fence",
        fail="grabbed a shovel and smeared the goo into even more spots",
        qa_text="grabbed a shovel and tried to move the mess",
    ),
    "rake": Reaction(
        id="rake",
        sense=2,
        power=1,
        text="raked at the slime and made it spread into a longer line",
        fail="used a rake, which only drew the mess into a wider grin",
        qa_text="used a rake and spread the mess around",
    ),
    "water": Reaction(
        id="water",
        sense=1,
        power=0,
        text="threw water on the patch, which only made the splash muddy",
        fail="threw water on it and turned the whole thing into soup",
        qa_text="threw water on the mess",
    ),
}


KNOWLEDGE = {
    "splash": [("What does splash mean?",
                "To splash is to throw or send liquid around so it lands in messy drops.")],
    "shit": [("Why is shit a bad surprise in a garden?",
              "Because it smells terrible and makes everything dirty and hard to clean.")],
    "fertile-ize": [("What does fertile-ize mean?",
                    "It means to add something to soil so plants can grow better. In a garden, people usually use safe fertilizer, not a silly homemade mess.")],
    "garden": [("What is a garden patch?",
                "A garden patch is a small area of soil where plants can grow.")],
    "cleanup": [("Why do people clean up messes quickly?",
                 "Cleaning up quickly keeps smells, germs, and stains from spreading.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short comedic story for a young child that uses the words "splash", '
        '"shit", and "fertile-ize".',
        f"Tell a funny bad-ending story where {f['child1'].id} and {f['child2'].id} "
        f"try to fertile-ize {f['patch'].label} with a splashy mix, but it goes wrong.",
        "Write a comedy about a garden experiment that ends in a smelly disaster.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent = f["child1"], f["child2"], f["parent"]
    patch = f["patch"]
    return [
        QAItem(
            question="Who is in the story?",
            answer=f"The story is about {a.id} and {b.id}, plus {parent.label_word}. They are the ones who turn the day into a silly garden experiment."
        ),
        QAItem(
            question="What went wrong?",
            answer=f"They tried to fertile-ize {patch.label} with a splashy mix, but it turned into a bad-smelling mess instead. The splash helped spread it farther, so the joke became a disaster."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly. The garden was messy and stinky, and the children had to help clean up instead of enjoying a happy garden."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag in ["splash", "shit", "fertile-ize", "garden", "cleanup"]:
        if tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} {bits}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="backyard", tool="hose", fertilizer="comedy_mix", target="garden", reaction="shovel",
                child1="Mia", child1_gender="girl", child2="Finn", child2_gender="boy", parent="mother"),
    StoryParams(place="garden", tool="bucket", fertilizer="comedy_mix", target="garden", reaction="rake",
                child1="Leo", child1_gender="boy", child2="Ava", child2_gender="girl", parent="father"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.fertilizer is None or c[2] == args.fertilizer)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, fertilizer = rng.choice(sorted(combos))
    child1_gender = args.child1_gender or rng.choice(["girl", "boy"]) if hasattr(args, "child1_gender") else rng.choice(["girl", "boy"])
    child2_gender = "boy" if child1_gender == "girl" else "girl"
    child1 = rng.choice([n for n in NAMES if n != ""])
    child2 = rng.choice([n for n in NAMES if n != child1])
    parent = args.parent or rng.choice(["mother", "father"])
    reaction = args.reaction or rng.choice(list(REACTIONS))
    target = args.target or "garden"
    return StoryParams(place=place, tool=tool, fertilizer=fertilizer, target=target, reaction=reaction,
                       child1=child1, child1_gender=child1_gender, child2=child2, child2_gender=child2_gender,
                       parent=parent, seed=None)


def generate(params: StoryParams) -> StorySample:
    if params.tool not in TOOLS or params.fertilizer not in FERTILIZERS or params.reaction not in REACTIONS:
        raise StoryError("Invalid params.")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic bad-ending splash storyworld.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--tool", choices=list(TOOLS))
    ap.add_argument("--fertilizer", choices=list(FERTILIZERS))
    ap.add_argument("--target", choices=["garden"])
    ap.add_argument("--reaction", choices=list(REACTIONS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--child1-gender", dest="child1_gender", choices=["girl", "boy"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for f in FERTILIZERS:
        lines.append(asp.fact("fertilizer", f))
    for r in REACTIONS.values():
        lines.append(asp.fact("reaction", r.id))
        lines.append(asp.fact("sense", r.id, r.sense))
        lines.append(asp.fact("power", r.id, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- reaction(R), sense(R,S), S >= 2.
valid(P,T,F) :- place(P), tool(T), fertilizer(F), T = hose, F = comedy_mix.
valid(P,T,F) :- place(P), tool(T), fertilizer(F), T = bucket, F = comedy_mix.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    if {r.id for r in REACTIONS.values() if r.sense >= 2} != set(asp_sensible()):
        print("MISMATCH in sensible reactions.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible reactions: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
