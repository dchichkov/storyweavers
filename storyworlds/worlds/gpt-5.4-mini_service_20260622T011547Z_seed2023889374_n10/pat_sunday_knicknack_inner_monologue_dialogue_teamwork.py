#!/usr/bin/env python3
"""
storyworlds/worlds/pat_sunday_knicknack_inner_monologue_dialogue_teamwork.py
=============================================================================

A small adventure storyworld about Pat, Sunday, and a mysterious knickknack:
a tiny expedition, a puzzling object, an inner-monologue clue, dialogue, and
teamwork that turns a stuck moment into a bright ending.

The world is deliberately small and classical: one child-led adventure, one
weather/location constraint, one tricky object, one helper action, and one
clear state-driven resolution.

Seed premise:
- Include the words: pat, sunday, knicknack
- Use Inner Monologue, Dialogue, Teamwork
- Keep an adventurous, child-facing tone
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
MIND_THRESHOLD = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    echoes: bool = False
    path: str = ""
    clue: str = ""


@dataclass
class Adventure:
    id: str
    title: str
    goal: str
    hazard: str
    teamwork_step: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trinket:
    id: str
    label: str
    phrase: str
    where: str
    risky: bool = False
    can_open: bool = False
    can_fill: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)


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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    scout = world.get("pat")
    if scout.meters["stuck"] >= THRESHOLD and scout.memes["worry"] < 2:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            scout.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("pat").memes["teamwork"] < THRESHOLD:
        return out
    if world.get("trinket").meters["open"] < THRESHOLD:
        return out
    sig = ("shared_find",)
    if sig not in world.fired:
        world.fired.add(sig)
        world.get("pat").meters["found"] += 1
        world.get("sunday").meters["found"] += 1
        out.append("__shared__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("teamwork", _r_teamwork)]


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


PLACES = {
    "harbor": Place("harbor", "the harbor", dark=False, echoes=False, path="dock path", clue="a lighthouse beam"),
    "cave": Place("cave", "the cave", dark=True, echoes=True, path="stone steps", clue="a little echo"),
    "museum": Place("museum", "the old museum", dark=False, echoes=True, path="marble halls", clue="a display case"),
}

ADVENTURES = {
    "harbor": Adventure(
        id="harbor",
        title="a harbor quest",
        goal="the lantern room",
        hazard="a stuck knicknack in a locked box",
        teamwork_step="one child holds the box while the other turns the key",
        ending_image="a little lantern glowed beside the waves",
        tags={"harbor", "lantern", "teamwork"},
    ),
    "cave": Adventure(
        id="cave",
        title="a cave quest",
        goal="the glowing chamber",
        hazard="a knicknack wedged behind a narrow crack",
        teamwork_step="one child shines a light while the other reaches carefully",
        ending_image="the cave wall flashed with a bright path",
        tags={"cave", "dark", "teamwork"},
    ),
    "museum": Adventure(
        id="museum",
        title="a museum quest",
        goal="the map desk",
        hazard="a knicknack on a high shelf",
        teamwork_step="one child steadies the ladder while the other climbs",
        ending_image="the shelf stood neat and safe again",
        tags={"museum", "careful", "teamwork"},
    ),
}

TRINKETS = {
    "compass": Trinket("compass", "a brass knicknack compass", "the knicknack compass", "the old box", risky=False, can_open=True, tags={"knicknack", "compass"}),
    "musicbox": Trinket("musicbox", "a tiny knicknack music box", "the knicknack music box", "the shelf", risky=False, can_open=False, can_fill=True, tags={"knicknack", "music"}),
    "lockbox": Trinket("lockbox", "a stubborn knicknack box", "the knicknack box", "the table", risky=True, can_open=True, tags={"knicknack", "box"}),
}

TOOLS = {
    "key": Tool("key", "a bent key", "the bent key", "turns the tiny lock", power=2, sense=3, tags={"key", "open"}),
    "rope": Tool("rope", "a short rope", "the short rope", "helps lift and steady", power=1, sense=2, tags={"rope", "steady"}),
    "lamp": Tool("lamp", "a small lamp", "the small lamp", "shows hidden corners", power=1, sense=3, tags={"lamp", "light"}),
}


@dataclass
class StoryParams:
    place: str
    adventure: str
    trinket: str
    tool: str
    pat_name: str = "Pat"
    sunday_name: str = "Sunday"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, adv in ADVENTURES.items():
            for tid, tr in TRINKETS.items():
                if place.dark and tid == "musicbox":
                    continue
                combos.append((pid, aid, tid))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.adventure not in ADVENTURES:
        raise StoryError(f"Unknown adventure: {params.adventure}")
    if params.trinket not in TRINKETS:
        raise StoryError(f"Unknown trinket: {params.trinket}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if (params.place, params.adventure, params.trinket) not in valid_combos():
        raise StoryError("That adventure setup is not reasonable for this world.")


def choose_valid(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.adventure is None or c[1] == args.adventure)
              and (args.trinket is None or c[2] == args.trinket)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, adventure, trinket = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    return StoryParams(place=place, adventure=adventure, trinket=trinket, tool=tool)


def _predict(world: World, trinket_id: str, tool_id: str) -> dict:
    sim = world.copy()
    _open_trinket(sim, sim.get("pat"), sim.get("sunday"), TRINKETS[trinket_id], TOOLS[tool_id], narrate=False)
    return {"opened": sim.get("trinket").meters["open"] >= THRESHOLD, "shared": sim.get("pat").meters["found"] >= THRESHOLD}


def _open_trinket(world: World, pat: Entity, sunday: Entity, trinket: Trinket, tool: Tool, narrate: bool = True) -> None:
    world.get("trinket").meters["open"] += tool.power
    world.get("pat").memes["teamwork"] += 1
    world.get("sunday").memes["teamwork"] += 1
    if narrate:
        propagate(world, narrate=True)


def intro(world: World, place: Place, adv: Adventure) -> None:
    pat = world.get("pat")
    sunday = world.get("sunday")
    pat.memes["curiosity"] += 1
    sunday.memes["curiosity"] += 1
    world.say(
        f"On Sunday, Pat and Sunday set off on an adventure to {place.label}. "
        f"{place.clue} waited ahead, and {adv.goal} was the prize they wanted."
    )


def inner_monologue(world: World, pat: Entity, trinket: Trinket, place: Place) -> None:
    pat.memes["resolve"] += 1
    world.say(
        f"Pat looked at {trinket.phrase} and thought, "
        f"\"If I am careful, I can help us move forward.\""
    )
    if place.echoes:
        world.say(
            f"In Pat's head, the room answered back with a small echo: "
            f"\"Try together.\""
        )


def dialogue_and_turn(world: World, pat: Entity, sunday: Entity, adv: Adventure, trinket: Trinket, tool: Tool) -> None:
    if trinket.risky:
        world.say(
            f"\"It's stuck,\" Pat said. \"I don't want to force it.\""
        )
        world.say(
            f"\"Then let's use teamwork,\" Sunday said. \"You hold it steady, and I'll use {tool.label}.\""
        )
    else:
        world.say(
            f"\"I think the {trinket.label} is meant to be opened gently,\" Pat said."
        )
        world.say(
            f"\"Good,\" Sunday replied. \"We can still work as a team.\""
        )
    world.say(
        f"Together they followed {adv.teamwork_step}."
    )


def resolution(world: World, adv: Adventure, trinket: Trinket, tool: Tool) -> None:
    t = world.get("trinket")
    t.meters["open"] += tool.power
    if t.meters["open"] >= THRESHOLD:
        t.meters["found"] += 1
        world.get("pat").meters["found"] += 1
        world.get("sunday").meters["found"] += 1
        world.get("pat").memes["joy"] += 1
        world.get("sunday").memes["joy"] += 1
        world.say(
            f"{tool.label.capitalize()} did the trick, and the knicknack opened with a tiny click."
        )
        world.say(
            f"Inside was a clue for {adv.goal}, and Pat and Sunday grinned at each other."
        )
        world.say(
            f"By the end, {adv.ending_image}."
        )
    else:
        world.say(
            f"The {trinket.label} stayed closed, so they had to stop and try a different path."
        )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    adv = ADVENTURES[params.adventure]
    trinket = TRINKETS[params.trinket]
    tool = TOOLS[params.tool]

    pat = world.add(Entity(id="pat", kind="character", type="boy", role="hero", label=params.pat_name))
    sunday = world.add(Entity(id="sunday", kind="character", type="girl", role="partner", label=params.sunday_name))
    world.add(Entity(id="trinket", kind="thing", type="object", label=trinket.label, attrs={"kind": trinket.id}))
    world.facts.update(place=place, adventure=adv, trinket=trinket, tool=tool, pat=pat, sunday=sunday)

    intro(world, place, adv)
    world.para()
    inner_monologue(world, pat, trinket, place)
    dialogue_and_turn(world, pat, sunday, adv, trinket, tool)
    world.para()
    _open_trinket(world, pat, sunday, trinket, tool, narrate=True)
    resolution(world, adv, trinket, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    adv: Adventure = f["adventure"]
    trinket: Trinket = f["trinket"]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the words "pat", "sunday", and "knicknack".',
        f"Tell a child-friendly quest where Pat and Sunday travel to {place.label} and solve a problem with {trinket.phrase}.",
        f'Write a teamwork story with inner monologue and dialogue, ending when Pat and Sunday reach {adv.goal}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = f["place"]
    adv: Adventure = f["adventure"]
    trinket: Trinket = f["trinket"]
    tool: Tool = f["tool"]
    pat: Entity = f["pat"]
    sunday: Entity = f["sunday"]
    return [
        QAItem(
            question=f"Why did Pat pause before touching {trinket.phrase}?",
            answer=f"Pat paused because the knicknack looked tricky and Pat wanted to be careful. Pat could tell that a small mistake might slow the adventure, so Pat thought first and then asked for help.",
        ),
        QAItem(
            question=f"What did Sunday suggest when the {trinket.label} got stuck?",
            answer=f"Sunday suggested teamwork. Sunday said Pat should hold the object steady while Sunday used {tool.label} to help, and that gave them a safe way to keep going.",
        ),
        QAItem(
            question=f"How did Pat and Sunday reach {adv.goal}?",
            answer=f"They reached {adv.goal} by working together. Pat used careful thinking, Sunday used {tool.label}, and the two of them solved the problem side by side.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other on the same task. Each person does a part, and together they can do more than one person could alone.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your head that thinks about what to do next. It helps a character make a choice before speaking aloud.",
        ),
        QAItem(
            question="What is a dialogue?",
            answer="A dialogue is when characters talk to each other. It lets the story show how they solve a problem together.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(params: StoryParams) -> str:
    return "(No story: that combination does not fit this small adventure world.)"


CURATED = [
    StoryParams(place="harbor", adventure="harbor", trinket="lockbox", tool="key", pat_name="Pat", sunday_name="Sunday"),
    StoryParams(place="cave", adventure="cave", trinket="compass", tool="lamp", pat_name="Pat", sunday_name="Sunday"),
    StoryParams(place="museum", adventure="museum", trinket="musicbox", tool="rope", pat_name="Pat", sunday_name="Sunday"),
]


def valid_tools() -> list[str]:
    return [k for k, t in TOOLS.items() if t.sense >= 2]


def outcome_of(params: StoryParams) -> str:
    return "shared" if params.tool in valid_tools() else "stuck"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure", aid))
    for tid in TRINKETS:
        lines.append(asp.fact("trinket", tid))
    for toid, tool in TOOLS.items():
        lines.append(asp.fact("tool", toid))
        lines.append(asp.fact("sense", toid, tool.sense))
        lines.append(asp.fact("power", toid, tool.power))
        if tool.sense >= 2:
            lines.append(asp.fact("reasonable_tool", toid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,T) :- place(P), adventure(A), trinket(T).
reasonable(T) :- tool(T), sense(T,S), S >= 2.
shared(T) :- reasonable(T), power(T,P), P >= 1.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasonable_tools() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(show="#show reasonable/1."))
    return sorted(t for (t,) in asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP valid combos match Python ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
        if py - cl:
            print("  only in Python:", sorted(py - cl))

    if set(valid_tools()) == set(asp_reasonable_tools()):
        print("OK: ASP reasonable tools match Python.")
    else:
        rc = 1
        print("MISMATCH in reasonable tools.")

    smoke = generate(CURATED[0])
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: smoke story was empty.")
    else:
        print("OK: smoke test story generated.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure storyworld with Pat, Sunday, and a knicknack."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--trinket", choices=TRINKETS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.adventure is None or c[1] == args.adventure)
              and (args.trinket is None or c[2] == args.trinket)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, adventure, trinket = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(valid_tools()))
    return StoryParams(place=place, adventure=adventure, trinket=trinket, tool=tool)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.adventure not in ADVENTURES or params.trinket not in TRINKETS or params.tool not in TOOLS:
        raise StoryError("Invalid parameters.")
    if (params.place, params.adventure, params.trinket) not in valid_combos():
        raise StoryError(explain_rejection(params))
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
        print(asp_program(show="#show valid/3.\n#show reasonable/1.\n#show shared/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program(show="#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible adventure combos:")
        for item in combos:
            print("  ", item)
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
