#!/usr/bin/env python3
"""
storyworlds/worlds/demon_inner_monologue_space_adventure.py
===========================================================

A tiny story world for a space-adventure tale with a demon, where the real
action happens in the ship's state and the hero's inner monologue.

Premise:
- A small crew is flying through a strange part of space.
- A demon appears in the dark ship corridor or on a moon base.
- The hero hears the demon's taunts in inner monologue and must keep calm.
- The crew uses a sensible space tool to contain the problem.
- The ending proves the ship, the creature, and the hero's feelings changed.

The world is intentionally small and constraint-checked:
- typed entities with physical meters and emotional memes
- a reasonableness gate over valid story combinations
- a Python gate mirrored by inline ASP rules
- three Q&A sets grounded in the world state, not parsed from rendered text
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
    location: str = ""
    movable: bool = True
    dangerous: bool = False
    shielded: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "pilot"}
        male = {"boy", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    kind: str
    darkness: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    type: str
    danger: str
    needs: set[str] = field(default_factory=set)
    can_be_talked_down: bool = False


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    effect: str
    fits: set[str] = field(default_factory=set)
    can_shield: bool = False
    makes_light: bool = False


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("demon_present") and not world.facts.get("contained"):
        hero = world.get("hero")
        demon = world.get("demon")
        sig = ("fear", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            hero.memes["focus"] -= 0.5
            demon.meters["threat"] += 1
            out.append("__fear__")
    return out


def _r_ship_glow(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    if ship.meters.get("power", 0.0) >= THRESHOLD:
        sig = ("glow", ship.id)
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["glow"] += 1
            out.append("__glow__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("glow", "physical", _r_ship_glow)]


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


def hazard_at_risk(place: Place, hazard: Hazard, tool: Tool) -> bool:
    return place.kind in hazard.needs and place.kind in tool.fits


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for hid, hz in HAZARDS.items():
            for tid, tool in TOOLS.items():
                if hazard_at_risk(place, hz, tool):
                    combos.append((pid, hid, tid))
    return combos


@dataclass
class StoryParams:
    place: str = "orbit_lab"
    hazard: str = "void_demon"
    tool: str = "signal_chime"
    hero: str = "Nova"
    hero_type: str = "pilot"
    ally: str = "Iris"
    ally_type: str = "engineer"
    captain: str = "Captain"
    seed: Optional[int] = None


PLACES = {
    "orbit_lab": Place(
        id="orbit_lab",
        label="the orbit lab",
        kind="corridor",
        darkness="The corridor lights were low, and the window showed a long cold sweep of stars.",
        affords={"demon", "inner_monologue", "space"},
    ),
    "moon_hangar": Place(
        id="moon_hangar",
        label="the moon hangar",
        kind="hangar",
        darkness="The hangar doors were open to a silver moon field, and the shadows looked deep.",
        affords={"demon", "inner_monologue", "space"},
    ),
    "star_cradle": Place(
        id="star_cradle",
        label="the star cradle",
        kind="bay",
        darkness="The bay hummed softly, and the stars outside seemed far too quiet.",
        affords={"demon", "inner_monologue", "space"},
    ),
}

HAZARDS = {
    "void_demon": Hazard(
        id="void_demon",
        label="a void demon",
        type="demon",
        danger="it feeds on panic",
        needs={"corridor", "hangar", "bay"},
        can_be_talked_down=True,
    ),
    "glitch_demon": Hazard(
        id="glitch_demon",
        label="a glitch demon",
        type="demon",
        danger="it crawls through screens and alarms",
        needs={"corridor", "hangar", "bay"},
        can_be_talked_down=True,
    ),
}

TOOLS = {
    "signal_chime": Tool(
        id="signal_chime",
        label="a signal chime",
        kind="tool",
        effect="it turns the ship's warning system into a clear, steady note",
        fits={"corridor", "hangar", "bay"},
        can_shield=True,
        makes_light=False,
    ),
    "star_lamp": Tool(
        id="star_lamp",
        label="a star lamp",
        kind="tool",
        effect="it makes a bright circle of safe light",
        fits={"corridor", "hangar", "bay"},
        can_shield=True,
        makes_light=True,
    ),
    "shield_blanket": Tool(
        id="shield_blanket",
        label="a shield blanket",
        kind="tool",
        effect="it can be wrapped around a console to calm it down",
        fits={"corridor", "hangar", "bay"},
        can_shield=True,
        makes_light=False,
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Luna", "Zia", "Kira", "Talia"]
BOY_NAMES = ["Jax", "Taro", "Eli", "Orin", "Rex", "Pax"]
TRAITS = ["brave", "curious", "careful", "bold", "thoughtful"]


def tell(place: Place, hazard: Hazard, tool: Tool, hero_name: str, hero_type: str,
         ally_name: str, ally_type: str, captain: str) -> World:
    world = World(place)
    world.facts["place"] = place
    world.facts["hazard_cfg"] = hazard
    world.facts["tool_cfg"] = tool
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        location=place.id,
        meters={"oxygen": 1.0, "calm": 0.0},
        memes={"fear": 0.0, "focus": 1.0, "hope": 0.0, "resolve": 0.0},
        attrs={"captain": captain},
    ))
    ally = world.add(Entity(
        id="ally",
        kind="character",
        type=ally_type,
        label=ally_name,
        role="ally",
        location=place.id,
        meters={"oxygen": 1.0},
        memes={"fear": 0.0, "hope": 0.0},
    ))
    demon = world.add(Entity(
        id="demon",
        kind="character",
        type="demon",
        label=hazard.label,
        role="hazard",
        location=place.id,
        dangerous=True,
        meters={"threat": 0.0, "shimmer": 0.0},
        memes={"taunt": 1.0},
    ))
    ship = world.add(Entity(
        id="ship",
        kind="thing",
        type="ship",
        label="the ship",
        location=place.id,
        meters={"power": 1.0, "glow": 0.0},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type=tool.kind,
        label=tool.label,
        location=place.id,
        shielded=tool.can_shield,
        meters={"charge": 1.0},
    ))
    world.facts.update(hero=hero, ally=ally, demon=demon, ship=ship, tool=tool_ent, contained=False)

    world.say(f"{hero_name} and {ally_name} floated through {place.label} with the ship humming around them.")
    world.say(place.darkness)
    world.say(f"Then {hazard.label} drifted out of the dark, and {hero_name}'s thoughts went tight and small.")
    world.say(f'Inside {hero_name}\'s head, a quiet voice said, "Don\'t look scared. Space is big. You are tiny."')
    hero.memes["fear"] += 1
    hero.memes["hope"] += 0.5
    world.para()
    world.say(f'{hero_name} breathed in slowly. "No," {hero_name} told the thought inside, "I can still choose what to do."')
    world.say(f"{ally_name} pointed to {tool.label}. {tool.effect.capitalize()}.")
    if tool.makes_light:
        ship.meters["power"] += 0.5
    else:
        ship.meters["power"] += 0.2
    demon.meters["shimmer"] += 1
    world.say(f"{captain} stayed at the console and nodded toward the tool, ready if the demon lunged.")
    if hazard.can_be_talked_down:
        world.say(f"The demon's grin wavered when the steady light and calm breathing filled the corridor.")
    world.facts["contained"] = True
    propagate(world, narrate=True)
    world.para()
    hero.memes["resolve"] += 1
    hero.meters["calm"] += 1
    demon.meters["threat"] = 0.0
    world.say(f"{hero_name} lifted {tool.label} and the dark shape shrank back like smoke in a fan.")
    world.say(f"By the end, the ship was bright again, {hazard.label} had fled, and {hero_name}'s heart felt steady enough to hear the stars.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    hazard = f["hazard_cfg"]
    tool = f["tool_cfg"]
    place = f["place"]
    return [
        f'Write a short space adventure story for a young child that includes the word "demon" and a calm inner monologue.',
        f"Tell a story where {hero.label} sees {hazard.label} in {place.label}, listens to an inner voice, and uses {tool.label} to stay brave.",
        f'Write a gentle sci-fi story about a scary demon, a brave thought inside the hero\'s head, and a safe tool that brings back the light.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    ally = f["ally"]
    demon = f["demon"]
    tool = f["tool"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about in {place.label}?",
            answer=f"It was about {hero.label} and {ally.label} on the ship, with {demon.label} in the dark corridor. The story followed {hero.label}'s thoughts and how {hero.label} stayed calm.",
        ),
        QAItem(
            question=f"What did {hero.label} tell the worried thought inside {hero.pronoun('possessive')} head?",
            answer=f"{hero.label} told the thought that {hero.label} could still choose what to do. That inner monologue helped {hero.label} keep focus instead of freezing up.",
        ),
        QAItem(
            question=f"How did {tool.label} help when the demon appeared?",
            answer=f"{tool.label} made a steady, safe difference, so the dark shape lost its edge. The light and the calm plan gave the crew a way to handle the danger together.",
        ),
        QAItem(
            question=f"What changed by the ending of the story?",
            answer=f"The ship felt bright again, the demon backed away, and {hero.label} felt steady instead of small. The ending proved that the hero's fear turned into resolve.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a demon in a fantasy or space story?",
            answer="A demon is a scary creature from old stories or fantasy. In a story like this, it can be a dangerous stranger in the dark.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice of a character thinking to themselves. It lets the reader hear worries, plans, and brave thoughts.",
        ),
        QAItem(
            question="Why can a bright light help on a spaceship?",
            answer="A bright light helps people see what is nearby and feel less lost. It can also make a scary shadow look smaller and less strange.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orbit_lab", hazard="void_demon", tool="star_lamp", hero="Nova", hero_type="pilot", ally="Iris", ally_type="engineer", captain="Captain", seed=1),
    StoryParams(place="moon_hangar", hazard="glitch_demon", tool="signal_chime", hero="Jax", hero_type="boy", ally="Mira", ally_type="girl", captain="Captain", seed=2),
    StoryParams(place="star_cradle", hazard="void_demon", tool="shield_blanket", hero="Luna", hero_type="girl", ally="Pax", ally_type="boy", captain="Captain", seed=3),
]


def explain_rejection(place: Place, hazard: Hazard, tool: Tool) -> str:
    return f"(No story: {tool.label} cannot sensibly help with {hazard.label} in {place.label}.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("kind", pid, p.kind))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for n in sorted(h.needs):
            lines.append(asp.fact("needs", hid, n))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for n in sorted(t.fits):
            lines.append(asp.fact("fits", tid, n))
        if t.can_shield:
            lines.append(asp.fact("shield", tid))
        if t.makes_light:
            lines.append(asp.fact("light", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,H,T) :- place(P), hazard(H), tool(T), kind(P,K), needs(H,K), fits(T,K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        ok = False
        print("MISMATCH between Python and ASP combo gates")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        s = generate(CURATED[0])
        if not s.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    if ok:
        print(f"OK: verify passed ({len(py)} valid combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld with a demon and inner monologue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "pilot", "engineer"])
    ap.add_argument("--ally")
    ap.add_argument("--ally-type", choices=["girl", "boy", "pilot", "engineer"])
    ap.add_argument("--captain", default="Captain")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, tool = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["pilot", "girl", "boy"])
    ally_type = args.ally_type or rng.choice(["engineer", "girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type in {"girl", "pilot"} else BOY_NAMES)
    ally = args.ally or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(place=place, hazard=hazard, tool=tool, hero=hero, hero_type=hero_type, ally=ally, ally_type=ally_type, captain=args.captain)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.hazard not in HAZARDS or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    hazard = HAZARDS[params.hazard]
    tool = TOOLS[params.tool]
    if not hazard_at_risk(place, hazard, tool):
        raise StoryError(explain_rejection(place, hazard, tool))
    world = tell(place, hazard, tool, params.hero, params.hero_type, params.ally, params.ally_type, params.captain)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, h, t in combos:
            print(f"  {p:10} {h:12} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.ally} in {p.place} ({p.hazard}, {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
