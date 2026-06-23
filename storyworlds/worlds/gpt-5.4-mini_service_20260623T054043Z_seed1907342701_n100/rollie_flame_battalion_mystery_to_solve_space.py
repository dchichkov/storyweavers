#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/rollie_flame_battalion_mystery_to_solve_space.py
=============================================================================================================================

A standalone storyworld: a small space-adventure mystery where a crew uses clues,
tools, and teamwork to solve a strange problem on a moon outpost.

Premise:
- A child crew explores a space outpost with a helper robot named Rollie.
- Something important goes missing or goes dark.
- The crew follows clues, meets the Flame Battalion, and solves the mystery.
- The ending image proves what changed: a light returns, a path clears, or a
  signal comes back online.

The world uses typed entities with physical meters and emotional memes, a causal
rule layer, a reasonableness gate, and an inline ASP twin.
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
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    helper_for: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    vibe: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    clue_noun: str
    risk: str
    reveal: str
    danger_meter: str
    solve_method: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.clues: list[str] = []

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
        clone.fired = set(self.fired)
        clone.clues = list(self.clues)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mystery_solved(world: World) -> list[str]:
    out: list[str] = []
    for key in ("clue_map", "clue_echo", "clue_track"):
        if not world.facts.get(key):
            continue
    if world.facts.get("mapped") and world.facts.get("echoed") and world.facts.get("tracked"):
        sig = ("solved", world.facts["mystery"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            mystery: Mystery = world.facts["mystery"]
            if mystery.danger_meter in world.entities:
                world.get(mystery.danger_meter).meters["mystery"] = 0.0
            world.facts["solved"] = True
            out.append("__solved__")
    return out


CAUSAL_RULES = [Rule("mystery_solved", "state", _r_mystery_solved)]


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


def mystery_at_risk(mystery: Mystery, place: Place) -> bool:
    return mystery.id in place.affords or bool(place.affords & {"signal", "echo", "track"})


def suitable_tool(mystery: Mystery, tool: Tool) -> bool:
    return mystery.solve_method in tool.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for mystery_id, mystery in MYSTERIES.items():
            for tool_id, tool in TOOLS.items():
                if mystery_at_risk(mystery, place) and suitable_tool(mystery, tool):
                    combos.append((place_id, mystery_id, tool_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "orbital_hub": Place(
        id="orbital_hub",
        label="the orbital hub",
        vibe="a bright ring of metal windows and humming panels",
        affords={"signal", "echo", "track"},
        tags={"space", "station"},
    ),
    "moon_port": Place(
        id="moon_port",
        label="the moon port",
        vibe="a dusty landing bay under a black sky",
        affords={"track", "signal"},
        tags={"space", "moon"},
    ),
    "red_canyon": Place(
        id="red_canyon",
        label="the red canyon base",
        vibe="a quiet base tucked between red rocks and silver antennas",
        affords={"echo", "track"},
        tags={"space", "canyon"},
    ),
    "comet_garden": Place(
        id="comet_garden",
        label="the comet garden",
        vibe="a glass garden that shimmered with tiny frost leaves",
        affords={"signal", "echo"},
        tags={"space", "garden"},
    ),
}

MYSTERIES = {
    "lost_beacon": Mystery(
        id="lost_beacon",
        label="the missing beacon",
        clue_noun="beacon clue",
        risk="the path lights were fading",
        reveal="the beacon had rolled behind a crate",
        danger_meter="darkness",
        solve_method="search",
        tags={"beacon", "light", "missing"},
    ),
    "silent_signal": Mystery(
        id="silent_signal",
        label="the silent signal",
        clue_noun="signal clue",
        risk="the radio kept hissing with nothing useful",
        reveal="a loose wire had slipped free",
        danger_meter="static",
        solve_method="listen",
        tags={"signal", "radio", "static"},
    ),
    "frozen_track": Mystery(
        id="frozen_track",
        label="the frozen track",
        clue_noun="track clue",
        risk="the rover tracks had vanished under dust",
        reveal="fresh dust had covered the prints",
        danger_meter="drift",
        solve_method="brush",
        tags={"track", "dust", "missing"},
    ),
    "jammed_door": Mystery(
        id="jammed_door",
        label="the jammed door",
        clue_noun="door clue",
        risk="the hatch would not open",
        reveal="a tiny pebble had wedged in the seam",
        danger_meter="stuck",
        solve_method="pry",
        tags={"door", "hatch", "stuck"},
    ),
}

TOOLS = {
    "rollie": Tool(
        id="rollie",
        label="Rollie",
        phrase="Rollie the rover",
        use_line="rolled ahead and pointed its little scanner beam",
        fixes={"search", "listen"},
        tags={"rover", "helper"},
    ),
    "flare_map": Tool(
        id="flare_map",
        label="a flare-map",
        phrase="a flare-map",
        use_line="glowed with a soft trail of marks",
        fixes={"search", "track"},
        tags={"map", "light"},
    ),
    "brush_kit": Tool(
        id="brush_kit",
        label="a brush kit",
        phrase="a brush kit",
        use_line="swept the dust away in neat little swishes",
        fixes={"brush", "search"},
        tags={"brush", "dust"},
    ),
    "pry_bar": Tool(
        id="pry_bar",
        label="a pry bar",
        phrase="a tiny pry bar",
        use_line="nudged the seam until the hatch gave a click",
        fixes={"pry", "search"},
        tags={"tool", "hatch"},
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Iris", "Lyra", "Pia", "Zia", "Kira", "Luna"]
BOY_NAMES = ["Orin", "Tate", "Milo", "Jett", "Bram", "Kai", "Ezra", "Nico"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space adventure mystery for a 3-to-5-year-old that includes '
        f'the words "rollie", "flame", and "battalion".',
        f"Tell a gentle moon-base story where {f['hero'].id} and "
        f"{f['helper'].id} use {f['tool'].phrase} to solve {f['mystery'].label}.",
        f"Write a short story set at {f['place'].label} with a mystery to solve, "
        f"a helper named Rollie, and a brave crew called the Flame Battalion.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    place: Place = f["place"]
    battalion: Entity = f["battalion"]
    qa = [
        QAItem(
            f"Who are the story's space crew at {place.label}?",
            f"The story follows {hero.id}, {helper.id}, and the Flame Battalion. "
            f"They work together at {place.label} to solve {mystery.label}.",
        ),
        QAItem(
            f"What mystery did {hero.id} notice first at {place.label}?",
            f"{hero.id} noticed {mystery.risk}. That was the clue that something "
            f"was wrong and needed a careful search.",
        ),
        QAItem(
            f"How did {helper.id} help solve {mystery.label}?",
            f"{helper.id} used {tool.phrase} and {tool.use_line}. That helped the "
            f"crew follow the clues instead of guessing.",
        ),
    ]
    if f.get("solved"):
        qa.append(QAItem(
            f"What was the answer to {mystery.label}?",
            f"The answer was that {mystery.reveal}. The Flame Battalion helped "
            f"clear the last clue, and the whole crew could relax.",
        ))
        qa.append(QAItem(
            f"Why did the Flame Battalion arrive in the story?",
            f"They came because the mystery needed a brave rescue crew to help. "
            f"Once they joined in, the final clue made sense and the danger faded.",
        ))
    else:
        qa.append(QAItem(
            f"Why did the crew need to keep looking near {place.label}?",
            f"They still had clues to match because the mystery was not fully "
            f"solved yet. The answer was still hidden somewhere in the place.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["mystery"].tags) | set(f["tool"].tags)
    tags |= {"space", "rover"}
    if f.get("solved"):
        tags |= {"helper", "light"}
    items = []
    for tag in sorted(tags):
        if tag == "space":
            items.append(QAItem(
                "What is a space adventure story?",
                "A space adventure story is a story about traveling, exploring, "
                "and solving problems in places like moons, stations, and stars.",
            ))
        elif tag == "rover":
            items.append(QAItem(
                "What is a rover?",
                "A rover is a little robot vehicle that can roll across a planet "
                "or moon and help people look around.",
            ))
        elif tag == "light":
            items.append(QAItem(
                "Why are lights important in space?",
                "Lights help people see dark corners, signs, and paths. They make "
                "exploring safer and easier.",
            ))
    return items


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


def tell(place: Place, mystery: Mystery, tool: Tool, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    battalion = world.add(Entity(id="flame_battalion", kind="character", type="group", label="the Flame Battalion", role="rescue"))
    beacon = world.add(Entity(id="beacon", type="thing", label="the beacon", meters=defaultdict(float), memes=defaultdict(float)))
    door = world.add(Entity(id="door", type="thing", label="the hatch", meters=defaultdict(float), memes=defaultdict(float)))
    rollie = world.add(Entity(id="rollie", kind="character", type="robot", label="Rollie", role="helper"))
    world.facts.update(
        hero=hero,
        helper=helper,
        battalion=battalion,
        rollie=rollie,
        place=place,
        mystery=mystery,
        tool=tool,
        beacon=beacon,
        door=door,
        mapped=False,
        echoed=False,
        tracked=False,
        solved=False,
    )
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    battalion.memes["bravery"] += 1

    world.say(
        f"At {place.label}, the crew saw {place.vibe}. "
        f"{hero.id} was the first to notice {mystery.risk}, and {helper.id} called "
        f"Rollie to roll closer."
    )
    world.say(
        f'"Flame Battalion, stand by," {battalion.label} said, and the small rescue '
        f'crew blinked its lights from the dock.'
    )
    world.para()
    if mystery.id == "lost_beacon":
        beacon.meters["darkness"] += 1
        world.clues.append("roll marks")
        world.say(
            f"{helper.id} spotted tiny roll marks near a crate. Rollie used its beam "
            f"to follow them, and the clue felt fresh and bright."
        )
        world.facts["mapped"] = True
    elif mystery.id == "silent_signal":
        world.clues.append("tiny hiss")
        world.say(
            f"Rollie listened at the radio panel and caught a tiny hiss. {helper.id} "
            f"leaned in too, and the crew knew the signal was nearby."
        )
        world.facts["echoed"] = True
    elif mystery.id == "frozen_track":
        world.clues.append("dust line")
        world.say(
            f"Rollie rolled over a dusty line on the floor. {helper.id} brushed the "
            f"gray dust away, and a clear track appeared like a thin silver line."
        )
        world.facts["tracked"] = True
    else:
        door.meters["stuck"] += 1
        world.clues.append("pebble seam")
        world.say(
            f"Rollie peered at the hatch seam while {helper.id} checked the edge. A "
            f"tiny pebble showed where the mystery was hiding."
        )
        world.facts["tracked"] = True

    world.para()
    world.say(
        f"{tool.phrase.capitalize()} {tool.use_line}, and the Flame Battalion "
        f"used the clue to finish the search."
    )
    world.facts["mapped"] = world.facts["mapped"] or ("search" in tool.fixes)
    world.facts["echoed"] = world.facts["echoed"] or ("listen" in tool.fixes)
    world.facts["tracked"] = world.facts["tracked"] or ("brush" in tool.fixes or "pry" in tool.fixes)
    propagate(world, narrate=False)
    if not world.facts["solved"]:
        world.facts["solved"] = True
        world.get("beacon").meters["glow"] += 1
        world.say(
            f"Then the last clue clicked into place: {mystery.reveal}. "
            f"The beacon came back on, and the floor shone gold under their boots."
        )
    else:
        world.say(
            f"At last, {mystery.reveal}. The answer made the whole station feel quiet "
            f"and safe again."
        )
    world.para()
    if mystery.id == "lost_beacon":
        world.say(
            f"With the beacon lit again, Rollie rolled beside {hero.id} while the Flame "
            f"Battalion watched the corridor glow."
        )
    elif mystery.id == "silent_signal":
        world.say(
            f"The radio crackled clear, and the Flame Battalion waved from beside the "
            f"bright panel while Rollie spun in a happy circle."
        )
    elif mystery.id == "frozen_track":
        world.say(
            f"The hidden tracks showed clean and straight, and Rollie traced them with a "
            f"soft blue light as the crew smiled."
        )
    else:
        world.say(
            f"The hatch slid open at last, and Rollie rolled through first while the "
            f"Flame Battalion held the door for the others."
        )
    return world


def explain_rejection(place: Place, mystery: Mystery, tool: Tool) -> str:
    if not mystery_at_risk(mystery, place):
        return "(No story: that place does not give the mystery enough room to happen.)"
    if not suitable_tool(mystery, tool):
        return "(No story: that tool does not fit this mystery.)"
    return "(No story: that combination is not workable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, tool = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    hero_type = "girl" if hero_name in GIRL_NAMES else "boy"
    helper_name = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    helper_type = "robot" if helper_name == "Rollie" else ("girl" if helper_name in GIRL_NAMES else "boy")
    return StoryParams(
        place=place,
        mystery=mystery,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    if not mystery_at_risk(mystery, place):
        raise StoryError(explain_rejection(place, mystery, tool))
    if not suitable_tool(mystery, tool):
        raise StoryError(explain_rejection(place, mystery, tool))
    world = tell(place, mystery, tool, params.hero_name, params.hero_type, params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  clues: {world.clues}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
    StoryParams(place="orbital_hub", mystery="lost_beacon", tool="rollie", hero_name="Nova", hero_type="girl", helper_name="Milo", helper_type="boy"),
    StoryParams(place="moon_port", mystery="silent_signal", tool="flare_map", hero_name="Kai", hero_type="boy", helper_name="Iris", helper_type="girl"),
    StoryParams(place="red_canyon", mystery="frozen_track", tool="brush_kit", hero_name="Lyra", hero_type="girl", helper_name="Orin", helper_type="boy"),
    StoryParams(place="comet_garden", mystery="jammed_door", tool="pry_bar", hero_name="Jett", hero_type="boy", helper_name="Luna", helper_type="girl"),
]


ASP_RULES = r"""
place(P) :- place_id(P).
mystery(M) :- mystery_id(M).
tool(T) :- tool_id(T).

good_combo(P,M,T) :- place(P), mystery(M), tool(T), place_affords(P,signal), mystery_need(M,Need), tool_fixes(T,Need).
good_combo(P,M,T) :- place(P), mystery(M), tool(T), place_affords(P,echo), mystery_need(M,Need), tool_fixes(T,Need).
good_combo(P,M,T) :- place(P), mystery(M), tool(T), place_affords(P,track), mystery_need(M,Need), tool_fixes(T,Need).

solved :- map_done, echo_done, track_done.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_id", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("place_affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_id", mid))
        lines.append(asp.fact("mystery_need", mid, m.solve_method))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        for f in sorted(t.fixes):
            lines.append(asp.fact("tool_fixes", tid, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/3."))
    return sorted(set(asp.atoms(model, "good_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = cl == py
    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if ok:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        print("OK: story generation smoke test passed.")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in ASP:", sorted(cl - py))
    print(" only in Python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, m, t in combos:
            print(f"  {p:12} {m:14} {t}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero_name}: {p.mystery} at {p.place} using {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
