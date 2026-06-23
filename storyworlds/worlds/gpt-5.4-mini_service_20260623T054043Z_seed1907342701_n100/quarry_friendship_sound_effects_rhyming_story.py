#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/quarry_friendship_sound_effects_rhyming_story.py
=============================================================================================================================

A tiny standalone storyworld for a friendship-in-a-quarry rhyming tale with sound
effects. Two children explore a quarry, make a little rhyme, hear echoing sounds,
and choose a gentler way to play together.

The world model tracks:
- physical meters: noise, dust, echo, safe_distance, collected_stones, sparkles
- emotional memes: joy, worry, togetherness, pride, apology

The premise is simple:
- friends want to make music and sound effects in a quarry
- a too-loud sound startles the moment and risks a harsh echo
- one friend warns, the other listens, and they switch to a softer sound
- the ending proves the change with a calmer quarry, a shared rhyme, and a
  visible physical image: pebbles, echoes, and smiling friends on the path

The story quality goal is a child-facing rhyming mini-story, not a log.
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Quarry:
    id: str
    label: str
    echo_factor: int
    safe_spots: list[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundEffect:
    id: str
    label: str
    sound: str
    verb: str
    effect: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    soft_sound: str
    helps: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, quarry: Quarry) -> None:
        self.quarry = quarry
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.quarry)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    q = world.quarry
    for e in world.characters():
        if e.meters["noise"] < THRESHOLD:
            continue
        sig = ("echo", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["echo"] += q.echo_factor
        e.memes["worry"] += 1
        out.append(f"The quarry answered back with a long, round echo.")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["noise"] < THRESHOLD or e.meters["safe"] < THRESHOLD:
            continue
        sig = ("settle", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["noise"] = max(0.0, e.meters["noise"] - 1)
        e.memes["joy"] += 1
        out.append("Their sound grew soft, and the quarry felt kind again.")
    return out


CAUSAL_RULES = [Rule("echo", "physical", _r_echo), Rule("settle", "social", _r_settle)]


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


def sound_at_risk(activity: SoundEffect, quarry: Quarry) -> bool:
    return activity.id in quarry.tags or activity.label in {"clap", "tap", "song", "whistle"}


def select_tool(activity: SoundEffect) -> Optional[Tool]:
    for tool in TOOLS.values():
        if activity.id in tool.helps:
            return tool
    return None


def predict_echo(world: World, actor: Entity, activity: SoundEffect) -> dict:
    sim = world.copy()
    _do_sound(sim, sim.get(actor.id), activity, narrate=False)
    return {"echo": sim.get(actor.id).meters["echo"], "worry": sim.get(actor.id).memes["worry"]}


def _do_sound(world: World, actor: Entity, activity: SoundEffect, narrate: bool = True) -> None:
    actor.meters["noise"] += 1
    actor.meters["safe"] += 0
    actor.memes["joy"] += 1
    world.say(f"{actor.id} {activity.verb}, and {activity.sound} went dancing through the air.")
    propagate(world, narrate=narrate)


def setup(world: World, a: Entity, b: Entity) -> None:
    a.memes["togetherness"] += 1
    b.memes["togetherness"] += 1
    world.say(f"On the quarry path, {a.id} and {b.id} went side by side, as bright as can be.")
    world.say("They liked to make little rhymes and sound effects in the light of day.")


def want_sound(world: World, a: Entity, b: Entity, activity: SoundEffect) -> None:
    world.say(f'"Let\'s {activity.label}!" said {a.id}, with a grin so wide.')
    world.say(f'"We can make a song," said {b.id}, "and let the echoes glide."')


def warn(world: World, b: Entity, a: Entity, activity: SoundEffect) -> None:
    pred = predict_echo(world, a, activity)
    world.facts["predicted_echo"] = pred["echo"]
    b.memes["worry"] += 1
    world.say(f'{b.id} heard the quarry call. "That sound may boom too hard," {b.id} said.')
    if pred["echo"] >= THRESHOLD:
        world.say(f'"It may bounce and bounce around our ears like rolling stones in red."')


def soften(world: World, a: Entity, b: Entity, activity: SoundEffect, tool: Tool) -> None:
    a.meters["safe"] += 1
    b.meters["safe"] += 1
    a.memes["apology"] += 1
    b.memes["joy"] += 1
    world.say(f'{a.id} nodded quick. "You\'re right," {a.id} said, "let\'s make it sweet and small."')
    world.say(f'They used {tool.phrase}, and {tool.soft_sound} answered from the wall.')


def ending(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    a.memes["togetherness"] += 1
    b.memes["togetherness"] += 1
    world.say(
        f"Then {a.id} and {b.id} clinked a tiny rhyme with {tool.label}, "
        f"and the quarry kept it gentle all around."
    )
    world.say(
        f"Pebbles sat still, the echo turned soft, and both friends walked home on happy ground."
    )


def tell(quarry: Quarry, activity: SoundEffect, tool: Tool, name_a: str, name_b: str) -> World:
    world = World(quarry)
    a = world.add(Entity(id=name_a, kind="character", type="girl"))
    b = world.add(Entity(id=name_b, kind="character", type="boy"))
    world.add(Entity(id="path", type="place", label=quarry.label))
    world.facts["activity"] = activity
    world.facts["tool"] = tool
    world.facts["a"] = a
    world.facts["b"] = b
    setup(world, a, b)
    world.para()
    want_sound(world, a, b, activity)
    warn(world, b, a, activity)
    world.para()
    soften(world, a, b, activity, tool)
    _do_sound(world, a, activity, narrate=True)
    world.para()
    ending(world, a, b, tool)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "open_quarry": Quarry(id="open_quarry", label="the quarry", echo_factor=2, safe_spots=["path", "rim"], tags={"clap", "tap", "song", "whistle"}),
    "quiet_quarry": Quarry(id="quiet_quarry", label="the quiet quarry", echo_factor=1, safe_spots=["path"], tags={"clap", "tap", "song"}),
}

ACTIONS = {
    "clap": SoundEffect(id="clap", label="clap-clap", sound="clap, clap", verb="clapped", effect="bright taps", risk="a big echo", tags={"clap"}),
    "tap": SoundEffect(id="tap", label="tap-song", sound="tap-tap", verb="tapped", effect="little beats", risk="a rough echo", tags={"tap"}),
    "hum": SoundEffect(id="hum", label="hum-song", sound="mmm-mmm", verb="hummed", effect="soft music", risk="a wandering echo", tags={"song"}),
    "whistle": SoundEffect(id="whistle", label="whistle-call", sound="tweet-tweet", verb="whistled", effect="clear notes", risk="a sharp echo", tags={"whistle"}),
}

TOOLS = {
    "sticks": Tool(id="sticks", label="wooden sticks", phrase="two wooden sticks", soft_sound="tap-tap", helps={"tap", "clap"}),
    "stones": Tool(id="stones", label="smooth stones", phrase="two smooth stones", soft_sound="tok-tok", helps={"tap", "hum"}),
    "bottle": Tool(id="bottle", label="glass bottle", phrase="a glass bottle", soft_sound="ting-ting", helps={"whistle", "clap"}),
    "shell": Tool(id="shell", label="a shell", phrase="a little shell", soft_sound="shh-shh", helps={"hum"}),
}

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for act in ACTIONS:
            for tool in TOOLS:
                if act in TOOLS[tool].helps and place in SETTINGS:
                    combos.append((place, act, tool))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    tool: str
    name_a: str
    name_b: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ruby", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Max", "Noah", "Eli", "Finn", "Leo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Quarry friendship sound-effects rhyming story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, tool = rng.choice(sorted(combos))
    a = args.name_a or rng.choice(GIRL_NAMES)
    b = args.name_b or rng.choice([n for n in BOY_NAMES if n != a])
    return StoryParams(place=place, activity=activity, tool=tool, name_a=a, name_b=b)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.activity not in ACTIONS or params.tool not in TOOLS:
        raise StoryError("Invalid quarry story params.")
    if params.activity not in TOOLS[params.tool].helps:
        raise StoryError("That tool does not fit the sound.")
    world = tell(SETTINGS[params.place], ACTIONS[params.activity], TOOLS[params.tool], params.name_a, params.name_b)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about friendship in a {f["activity"].label} at the quarry.',
        f'Write a gentle rhyme where {f["a"].id} and {f["b"].id} make sound effects in the quarry, then choose a softer way to play.',
        'Tell a child-friendly rhyming story about two friends, a quarry, and a happy change from loud sounds to soft sounds.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, act, tool = f["a"], f["b"], f["activity"], f["tool"]
    return [
        QAItem(
            question=f"What did {a.id} and {b.id} want to do at the quarry?",
            answer=f"They wanted to make a little rhyme with {act.label} sounds. They liked playing together and listening to the quarry echo.",
        ),
        QAItem(
            question=f"Why did {b.id} worry about the sound?",
            answer=f"{b.id} worried because {act.risk} could bounce around the quarry. The echo was strong enough to feel loud and sharp.",
        ),
        QAItem(
            question=f"How did the friends change their plan?",
            answer=f"They listened to each other and used {tool.phrase} instead. That made the sound softer, so they could keep playing kindly together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a quarry?", "A quarry is a place where stone is taken from the ground, and it can have hard walls that make echoes."),
        QAItem("What is an echo?", "An echo is a sound that bounces off hard things and comes back to your ears."),
        QAItem("Why can soft sounds be nice in a quarry?", "Soft sounds are gentler on your ears, and they still let you play music without making too much noise."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines += [f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,T) :- place(P), activity(A), tool(T), helps(T,A).
echo(A) :- activity(A).
soft(T) :- tool(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ACTIONS:
        lines.append(asp.fact("activity", aid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in sorted(t.helps):
            lines.append(asp.fact("helps", tid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        print("MISMATCH between ASP and Python.")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
        rc = 1
    else:
        print(f"OK: ASP matches Python ({len(py)} combos).")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


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
    StoryParams(place="open_quarry", activity="clap", tool="sticks", name_a="Mia", name_b="Ben"),
    StoryParams(place="quiet_quarry", activity="tap", tool="stones", name_a="Lily", name_b="Noah"),
    StoryParams(place="open_quarry", activity="hum", tool="shell", name_a="Ava", name_b="Eli"),
    StoryParams(place="quiet_quarry", activity="whistle", tool="bottle", name_a="Zoe", name_b="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
