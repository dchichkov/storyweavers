#!/usr/bin/env python3
"""
storyworlds/worlds/munchkin_baby_lesson_learned_suspense_superhero_story.py
============================================================================

A small storyworld inspired by superhero tales for very young readers:
a tiny munchkin hero, a baby helper, a suspenseful problem, and a lesson
learned at the end.

Seed tale idea:
---
A tiny munchkin wanted to be a superhero right away. A baby nearby loved
to help, but the baby could not do the big rescue alone. When a stormy
night brought a stuck kitten into trouble, the munchkin rushed in too fast
and almost made the problem worse. Then the munchkin learned to slow down,
listen, and work with the baby helper. Together they used a flashlight,
a blanket, and a calm plan to save the kitten. The lesson was that a real
hero uses courage and care.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        for k in ["tired", "stuck", "safe", "shine", "helped", "fear", "joy", "brave", "conflict", "care"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "baby girl"}
        male = {"boy", "father", "dad", "man", "baby boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the neighborhood"
    indoors: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    name: str
    danger: str
    suspense: str
    fix_hint: str
    action: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    purpose: str
    helps: set[str]
    phrase: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.meters["stuck"] < THRESHOLD or ch.memes["fear"] < THRESHOLD:
            continue
        sig = ("suspense", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["conflict"] += 1
        out.append(f"The moment felt tense and quiet.")
    return out


def _r_support(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Munchkin")
    baby = world.entities.get("Baby")
    target = world.entities.get("Kitten")
    if not hero or not baby or not target:
        return out
    if hero.memes["brave"] >= THRESHOLD and baby.memes["care"] >= THRESHOLD and target.meters["safe"] >= THRESHOLD:
        sig = ("support",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append(f"Together, they turned the scary moment into a safe one.")
    return out


CAUSAL_RULES = [
    Rule("suspense", _r_suspense),
    Rule("support", _r_support),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero storyworld with a munchkin, a baby, suspense, and a lesson learned.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--challenge", choices=sorted(CHALLENGES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--baby-name")
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


@dataclass
class StoryParams:
    place: str
    challenge: str
    tool: str
    name: str
    baby_name: str
    seed: Optional[int] = None


SETTINGS = {
    "rooftop": Setting(place="the rooftop", afford={"kite", "cat"}),
    "alley": Setting(place="the alley", afford={"cat", "storm"}),
    "playroom": Setting(place="the playroom", indoors=True, afford={"toy", "cat"}),
}

CHALLENGES = {
    "kitten": Challenge(
        id="kitten",
        name="kitten",
        danger="stuck on a high ledge",
        suspense="was stuck and mewed softly from above",
        fix_hint="needed a careful rescue, not a wild leap",
        action="rescue the kitten",
        lesson="A real hero slows down and thinks before leaping.",
        tags={"cat", "care", "suspense"},
    ),
    "storm": Challenge(
        id="storm",
        name="storm",
        danger="a gusty wind and a swinging sign",
        suspense="was rattling the windows and making everyone hold still",
        fix_hint="needed a calm plan and a bright light",
        action="help the neighbors stay safe",
        lesson="Bravery means staying calm when things feel noisy and scary.",
        tags={"storm", "light", "suspense"},
    ),
    "toy": Challenge(
        id="toy",
        name="toy",
        danger="a toy robot rolling under furniture",
        suspense="was wedged in the dark and no one could reach it",
        fix_hint="needed a small tool and careful hands",
        action="free the toy robot",
        lesson="Small problems need gentle hands, not rushed moves.",
        tags={"toy", "care"},
    ),
}

TOOLS = {
    "flashlight": Tool(id="flashlight", label="flashlight", purpose="shine in the dark", helps={"kitten", "storm", "toy"}, phrase="a tiny flashlight", plural=False),
    "blanket": Tool(id="blanket", label="blanket", purpose="keep someone warm and calm", helps={"kitten", "storm"}, phrase="a soft blanket", plural=False),
    "ladder": Tool(id="ladder", label="ladder", purpose="reach high places safely", helps={"kitten"}, phrase="a little step ladder", plural=False),
    "walkie": Tool(id="walkie", label="walkie-talkie", purpose="call for help", helps={"storm", "kitten"}, phrase="a walkie-talkie", plural=False),
}

MUNCHKIN_NAMES = ["Milo", "Nia", "Pip", "Luna", "Toby", "Zara"]
BABY_NAMES = ["Bibi", "Mimi", "Kiki", "Bo", "Tiny", "Bean"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for cid, ch in CHALLENGES.items():
            if ch.id == "storm" and setting.indoors:
                continue
            for tid, tool in TOOLS.items():
                if cid in tool.helps:
                    combos.append((place, cid, tid))
    return combos


def reason_invalid(ch: Challenge, tool: Tool, setting: Setting) -> str:
    return f"(No story: {tool.label} does not help with {ch.name} in {setting.place}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.tool:
        ch, tool = CHALLENGES[args.challenge], TOOLS[args.tool]
        if args.place and args.place in SETTINGS and args.challenge == "storm" and SETTINGS[args.place].indoors:
            raise StoryError("(No story: the storm needs an outdoor or open place.)")
        if args.challenge not in tool.helps:
            raise StoryError(reason_invalid(ch, tool, SETTINGS[args.place] if args.place else next(iter(SETTINGS.values()))))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, tool = rng.choice(sorted(combos))
    munchkin = args.name or rng.choice(MUNCHKIN_NAMES)
    baby = args.baby_name or rng.choice(BABY_NAMES)
    return StoryParams(place=place, challenge=challenge, tool=tool, name=munchkin, baby_name=baby)


def _do_action(world: World, hero: Entity, challenge: Challenge, tool: Tool, narrate: bool = True) -> None:
    hero.memes["brave"] += 1
    if challenge.id == "kitten":
        world.get("Kitten").meters["safe"] += 1
    elif challenge.id == "storm":
        world.get("Kitten").meters["safe"] += 1
    else:
        world.get("Kitten").meters["safe"] += 1
    propagate(world, narrate=narrate)


def predict_outcome(world: World, challenge: Challenge, tool: Tool) -> dict:
    sim = world.copy()
    hero = sim.get("Munchkin")
    hero.meters["stuck"] += 1
    hero.memes["fear"] += 1
    _do_action(sim, hero, challenge, tool, narrate=False)
    return {"safe": sim.get("Kitten").meters["safe"] >= THRESHOLD}


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    challenge = CHALLENGES[params.challenge]
    tool = TOOLS[params.tool]
    world = World(setting)
    hero = world.add(Entity(id="Munchkin", kind="character", type="munchkin", label=params.name, traits=["little", "brave"]))
    baby = world.add(Entity(id="Baby", kind="character", type="baby", label=params.baby_name, traits=["tiny", "careful"]))
    kitten = world.add(Entity(id="Kitten", kind="character", type="kitten", label="the kitten"))
    prop = world.add(Entity(id="Tool", type="tool", label=tool.label, phrase=tool.phrase))
    prop.worn_by = hero.id
    world.weather = "stormy" if challenge.id == "storm" else ""

    hero.memes["joy"] += 1
    baby.memes["care"] += 1
    world.say(f"{hero.label} was a little munchkin who wanted to be a superhero.")
    world.say(f"{baby.label} was a baby who liked to help in small ways.")
    world.say(f"One day at {setting.place}, a {challenge.name} {challenge.suspense}.")
    world.para()
    world.say(f"{hero.label} grabbed {tool.label} and rushed in, because {hero.pronoun()} wanted to solve everything fast.")
    hero.meters["stuck"] += 1
    hero.memes["fear"] += 1
    kitten.meters["stuck"] += 1
    propagate(world)
    world.say(f"That was a little too fast, and the plan felt shaky.")
    world.para()
    world.say(f"Then the baby pointed to the {tool.label} and looked up with careful eyes.")
    world.say(f"{hero.label} took a breath, listened, and remembered that {challenge.fix_hint}.")
    hero.meters["stuck"] = 0
    hero.memes["fear"] = 0
    _do_action(world, hero, challenge, tool)
    world.say(f"{hero.label} and {baby.label} used the {tool.label} together.")
    world.say(f"They helped {challenge.action}, and the kitten was safe at last.")
    world.para()
    world.say(f"{challenge.lesson} {hero.label} smiled, because the best heroes were brave and careful at the same time.")
    world.facts.update(hero=hero, baby=baby, kitten=kitten, tool=tool, challenge=challenge, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child about a munchkin named {f["hero"].label} and a baby named {f["baby"].label}.',
        f'Tell a suspenseful but gentle story where {f["hero"].label} and {f["baby"].label} solve a {f["challenge"].name} problem together.',
        f'Write a child-friendly lesson-learned story that uses the word "{f["challenge"].name}" and ends with a safe rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, baby, ch, tool = f["hero"], f["baby"], f["challenge"], f["tool"]
    return [
        QAItem(
            question=f"Who was the little superhero in the story?",
            answer=f"The little superhero was {hero.label}, the munchkin who learned to slow down and help carefully.",
        ),
        QAItem(
            question=f"What made the story feel tense at {world.setting.place}?",
            answer=f"The story felt tense because the {ch.name} {ch.suspense}, so everyone had to pause and think.",
        ),
        QAItem(
            question=f"What did {hero.label} and {baby.label} use to help?",
            answer=f"They used {tool.phrase} together, which helped them solve the problem safely.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{ch.lesson}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a character who helps others, stays brave, and uses special skills to solve problems.",
        ),
        QAItem(
            question="Why should someone slow down before acting in a scary moment?",
            answer="Slowing down helps a person notice danger, choose a safer plan, and avoid making the problem worse.",
        ),
        QAItem(
            question="What does a flashlight do?",
            answer="A flashlight makes a beam of light so people can see in the dark.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important might happen next, so you keep wondering what will come of it.",
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="rooftop", challenge="kitten", tool="ladder", name="Milo", baby_name="Bean"),
    StoryParams(place="alley", challenge="storm", tool="flashlight", name="Nia", baby_name="Mimi"),
    StoryParams(place="playroom", challenge="toy", tool="flashlight", name="Pip", baby_name="Kiki"),
]


ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(P,C,T) :- place(P), challenge(C), tool(T), place_challenge(P,C), tool_helps(T,C).
valid_story(P,C,T,B) :- valid(P,C,T), baby(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for c in sorted(s.afford):
            lines.append(asp.fact("place_challenge", pid, c))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.helps):
            lines.append(asp.fact("tool_helps", tid, c))
    for b in BABY_NAMES:
        lines.append(asp.fact("baby", b))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_name(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    return (args.name or rng.choice(MUNCHKIN_NAMES), args.baby_name or rng.choice(BABY_NAMES))


def generate(params: StoryParams) -> StorySample:
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, challenge, tool) combos ({len(stories)} with baby variants):\n")
        for place, challenge, tool in triples:
            babies = sorted(b for (p, c, t, b) in stories if (p, c, t) == (place, challenge, tool))
            print(f"  {place:10} {challenge:10} {tool:10}  [{', '.join(babies)}]")
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
            header = f"### {p.name}: {p.challenge} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
