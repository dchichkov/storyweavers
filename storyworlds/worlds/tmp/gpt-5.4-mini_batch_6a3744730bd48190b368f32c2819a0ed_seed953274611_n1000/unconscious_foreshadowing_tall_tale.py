#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/unconscious_foreshadowing_tall_tale.py
=======================================================================

A standalone story world for a tiny tall-tale domain with foreshadowing.

Seed premise
------------
A child and a grown-up cross a giant old bridge with a load of something
precious. Early signs hint that trouble is coming. When the bridge gives way,
someone ends up unconscious, and the child uses a sensible tool and a brave
idea to get help. The ending proves what changed: the danger is over, the
grown-up wakes up, and the child learns to watch for warning signs.

This world keeps the tone close to a tall tale:
- big, folksy, exaggerated images
- concrete physical state that drives the prose
- foreshadowing in the setup that pays off in the turn

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/unconscious_foreshadowing_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/unconscious_foreshadowing_tall_tale.py --qa
    python storyworlds/worlds/gpt-5.4-mini/unconscious_foreshadowing_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/unconscious_foreshadowing_tall_tale.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FORESHADOW_MIN = 2
DANGER_MIN = 1
RELIEF_GAIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"danger": 0.0, "injury": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "hope": 0.0, "courage": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Hazard:
    id: str
    label: str
    effect: str
    severity: int = 1
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    power: int
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Foreshadow:
    id: str
    clue: str
    pay: str
    tone: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
    tag: str
    apply: Callable[[World], list[str]]


def _r_unconscious(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("injury", 0.0) < THRESHOLD:
            continue
        sig = ("unconscious", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.attrs["unconscious"] = True
        e.memes["fear"] += 1
        out.append("__unconscious__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if not e.attrs.get("unconscious") and e.meters.get("injury", 0.0) < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        if world.facts.get("rescued"):
            world.fired.add(sig)
            e.memes["relief"] += RELIEF_GAIN
            out.append(f"{e.id} felt the fog lift a bit.")
    return out


CAUSAL_RULES = [
    Rule("unconscious", "physical", _r_unconscious),
    Rule("relief", "social", _r_relief),
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for hazard_id, haz in HAZARDS.items():
        for tool_id, tool in TOOLS.items():
            if haz.id in tool.helps and haz.risky:
                combos.append((hazard_id, tool_id))
    return combos


def reasonableness_gate(hazard: Hazard, tool: Tool) -> bool:
    return hazard.risky and hazard.id in tool.helps


def predict_hazard(world: World, hazard: Hazard, hero: Entity) -> dict[str, object]:
    sim = world.copy()
    _do_hazard(sim, sim.get(hero.id), hazard, narrate=False)
    return {
        "unconscious": bool(sim.get("uncle").attrs.get("unconscious")),
        "danger": sim.get("bridge").meters.get("danger", 0.0),
    }


def _do_hazard(world: World, hero: Entity, hazard: Hazard, narrate: bool = True) -> None:
    bridge = world.get("bridge")
    bridge.meters["danger"] += hazard.severity
    bridge.memes["tense"] = bridge.memes.get("tense", 0.0) + 1
    if hazard.id == "plank_snap":
        world.get("uncle").meters["injury"] += 1
    elif hazard.id == "river_splash":
        hero.meters["soaked"] = hero.meters.get("soaked", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, kid: Entity, grownup: Entity, place: str, load: str) -> None:
    world.say(
        f"{kid.id} and {grownup.id} set out across {place} with a load of {load} "
        f"balanced like a church hat on a winter mule."
    )
    world.say(
        f"The bridge was so old it leaned in the wind, and the whole valley could hear "
        f"it sing when the boards stretched."
    )


def foreshadow(world: World, clue: Foreshadow, hazard: Hazard) -> None:
    world.say(
        f"First there was {clue.clue}. It sounded like {clue.tone}, and any sensible "
        f"tall-tale traveler would have known {clue.pay}."
    )
    world.say(
        f"{hazard.label.capitalize()} was coming, though the morning was still as bright "
        f"as a new tin cup."
    )


def warn(world: World, kid: Entity, grownup: Entity, hazard: Hazard) -> None:
    pred = predict_hazard(world, hazard, kid)
    kid.memes["courage"] += 1
    if pred["danger"] >= DANGER_MIN:
        world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{kid.id} squinted at the bridge and said, "{grownup.id}, this thing is '
        f'whispering trouble. It sounds like it might let a whole boot through."'
    )


def accident(world: World, kid: Entity, grownup: Entity, hazard: Hazard) -> None:
    world.say(
        f"Then the bridge gave a mighty groan, one plank popped like a firecracker, "
        f"and {grownup.id} pitched forward."
    )
    _do_hazard(world, grownup, hazard)
    world.say(
        f"{grownup.id} hit the boards and lay unconscious as a moonbeam, while the mule "
        f"snorted and skittered sideways."
    )


def rescue(world: World, kid: Entity, grownup: Entity, tool: Tool) -> None:
    grownup.attrs["unconscious"] = False
    grownup.meters["injury"] = 0.0
    world.facts["rescued"] = True
    world.say(
        f"{kid.id} grabbed {tool.phrase} and used it with all the sense {tool.power} "
        f"men would have borrowed if they'd been standing nearby."
    )
    world.say(
        f"The tool did its work. The danger settled, {grownup.id} blinked awake, and the "
        f"bridge stopped shaking its old bones."
    )


def ending(world: World, kid: Entity, grownup: Entity, tool: Tool, hazard: Hazard) -> None:
    kid.memes["hope"] += 1
    kid.memes["relief"] += 1
    grownup.memes["relief"] += 1
    world.say(
        f"{grownup.id} sat up rubbing {grownup.pronoun('possessive')} head, and {kid.id} "
        f"told {grownup.pronoun('object')} about the warning signs they had seen."
    )
    world.say(
        f"After that, they tied the load down better, kept {tool.label} close, and crossed "
        f"the bridge one careful step at a time."
    )
    world.say(
        f"And from then on, whenever the boards hummed under their boots, {kid.id} said "
        f"that was the bridge's way of clearing its throat before a storm."
    )


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    grownup = f["grownup"]
    hazard = f["hazard"]
    tool = f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {kid.id} and {grownup.id}, who crossed a very old bridge with a load that could not be dropped."),
        ("What warning signs were there before the trouble?",
         f"The bridge groaned, the boards sang, and the whole thing seemed to be warning them before anything broke. Those clues were foreshadowing, because they hinted at the fall before it happened."),
        ("What happened after the bridge gave way?",
         f"{grownup.id} fell and was left unconscious. The injury came from the snapping plank, so the child had to act quickly."),
        ("How was the problem fixed?",
         f"{kid.id} used {tool.phrase} to help, and that gave the grown-up time to wake up and recover. The danger settled because the tool matched the kind of trouble they were facing."),
    ]
    if f.get("rescued"):
        qa.append((
            "How did the ending change the story?",
            f"The ending turned safe and steady. The grown-up woke up, the load stayed together, and the bridge crossing became a careful trip instead of a disaster."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = []
    tags = set(world.facts["hazard"].tags) | set(world.facts["tool"].tags) | set(world.facts["clue"].tags)
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story that includes the word "{f["hazard"].label}" and the word "unconscious".',
        f"Tell a folksy story where {f['kid'].id} notices warning signs before trouble on a bridge, and later helps when {f['grownup'].id} gets hurt.",
        f"Write a child-friendly tall tale with foreshadowing, a sudden spill, and a brave rescue using {f['tool'].label}.",
    ]


@dataclass
class StoryParams:
    hazard: str
    tool: str
    kid_name: str
    kid_gender: str
    grownup_name: str
    grownup_gender: str
    place: str
    load: str
    clue: str
    seed: Optional[int] = None


HAZARDS = {
    "plank_snap": Hazard(
        id="plank_snap",
        label="bridge trouble",
        effect="unconscious",
        severity=2,
        risky=True,
        tags={"bridge", "snap", "unconscious"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a long rope",
        phrase="a long rope",
        power=2,
        helps={"plank_snap"},
        tags={"rope", "rescue"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a lantern",
        power=1,
        helps={"plank_snap"},
        tags={"light", "warning"},
    ),
}

FORESHADOWS = {
    "groan": Foreshadow(
        id="groan",
        clue="the bridge gave a low groan before anyone stepped on it",
        pay="the boards were too tired to hold a heavy load",
        tone="a fiddle string pulled too tight",
        tags={"bridge", "warning"},
    ),
    "crows": Foreshadow(
        id="crows",
        clue="a flock of crows lifted off all at once",
        pay="the air itself seemed to know a tumble was coming",
        tone="a kettle lid rattling in a windstorm",
        tags={"warning", "sky"},
    ),
}

GIRL_NAMES = ["Mabel", "Dottie", "Pearl", "Ruby", "Annie"]
BOY_NAMES = ["Buck", "Eli", "Hank", "Otis", "Jeb"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.hazard not in HAZARDS:
        raise StoryError("Unknown hazard.")
    if args.tool and args.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if args.hazard and args.tool:
        if not reasonableness_gate(HAZARDS[args.hazard], TOOLS[args.tool]):
            raise StoryError("(No story: that tool does not really fit the trouble.)")
    hazard = args.hazard or "plank_snap"
    tool = args.tool or "rope"
    kid_gender = args.kid_gender or rng.choice(["girl", "boy"])
    grownup_gender = args.grownup_gender or rng.choice(["male", "female"])
    kid_name = args.kid_name or rng.choice(GIRL_NAMES if kid_gender == "girl" else BOY_NAMES)
    grownup_name = args.grownup_name or rng.choice(["Uncle Gus", "Aunt Nell", "Pa", "Ma"])
    clue = args.clue or rng.choice(list(FORESHADOWS))
    return StoryParams(
        hazard=hazard,
        tool=tool,
        kid_name=kid_name,
        kid_gender=kid_gender,
        grownup_name=grownup_name,
        grownup_gender=grownup_gender,
        place=args.place or "the old river bridge",
        load=args.load or "a sack of cornmeal",
        clue=clue,
    )


def tell(params: StoryParams) -> World:
    world = World()
    kid = world.add(Entity(id=params.kid_name, kind="character", type=params.kid_gender, role="kid"))
    grownup = world.add(Entity(id=params.grownup_name, kind="character", type=params.grownup_gender, role="grownup"))
    bridge = world.add(Entity(id="bridge", kind="thing", type="bridge", label="the bridge"))
    tool = TOOLS[params.tool]
    haz = HAZARDS[params.hazard]
    clue = FORESHADOWS[params.clue]

    world.facts.update(kid=kid, grownup=grownup, bridge=bridge, tool=tool, hazard=haz, clue=clue, rescued=False)

    introduce(world, kid, grownup, params.place, params.load)
    world.para()
    foreshadow(world, clue, haz)
    warn(world, kid, grownup, haz)
    world.para()
    accident(world, kid, grownup, haz)
    world.para()
    rescue(world, kid, grownup, tool)
    world.para()
    ending(world, kid, grownup, tool, haz)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        bits.append(f"role={e.role}" if e.role else "")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(b for b in bits if b)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hazard="plank_snap",
        tool="rope",
        kid_name="Mabel",
        kid_gender="girl",
        grownup_name="Uncle Gus",
        grownup_gender="male",
        place="the old river bridge",
        load="a sack of cornmeal",
        clue="groan",
    ),
    StoryParams(
        hazard="plank_snap",
        tool="lantern",
        kid_name="Eli",
        kid_gender="boy",
        grownup_name="Aunt Nell",
        grownup_gender="female",
        place="the high plank bridge",
        load="a basket of peaches",
        clue="crows",
    ),
]


def explain_rejection() -> str:
    return "(No story: the chosen tool is too small for the kind of bridge trouble here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny tall-tale storyworld with foreshadowing and unconscious rescue.")
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--kid-name")
    ap.add_argument("--kid-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup-name")
    ap.add_argument("--grownup-gender", choices=["female", "male"])
    ap.add_argument("--place")
    ap.add_argument("--load")
    ap.add_argument("--clue", choices=sorted(FORESHADOWS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


ASP_RULES = r"""
hazard(plank_snap).
tool(rope).
fits(plank_snap, rope).
fits(plank_snap, lantern).
valid(H, T) :- hazard(H), tool(T), fits(H, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for hid, tool in [(h, t) for h in HAZARDS for t in TOOLS if reasonableness_gate(HAZARDS[h], TOOLS[t])]:
        lines.append(asp.fact("fits", hid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:  # noqa: BLE001
        print(f"MISMATCH: generate smoke test failed: {exc}")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
