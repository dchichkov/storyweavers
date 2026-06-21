#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rap_thermometer_fortress_moral_value_flashback_humor.py
=======================================================================================

A small standalone storyworld: a kid, a rap challenge, a thermometer, and a
fortress. The domain is built from an adventure-style seed with moral value,
flashback, and humor. The story engine models typed entities with physical
meters and emotional memes, uses a reasonableness gate, and exposes a declarative
ASP twin for parity checks.

Premise:
- Two children explore a make-believe fortress on a chilly day.
- One wants to win a silly rap contest; the other notices the cold.
- A thermometer becomes the key tool for checking whether the fortress is safe.
- A flashback reminds them of a better choice, and the ending proves they
  learned to care for others while keeping the adventure fun.

The story supports:
- clear beginning / tension / turn / ending
- moral value
- flashback
- humor
- child-facing prose
- grounded Q&A in world state, not by parsing rendered text
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
TEMP_SAFE_MIN = 18
TEMP_SAFE_MAX = 26


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"cold": 0.0, "warmth": 0.0, "pride": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "humor": 0.0, "moral": 0.0}

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


@dataclass
class Theme:
    id: str
    frame: str
    fortress: str
    quest: str
    ending: str


@dataclass
class Challenge:
    id: str
    label: str
    risk: str
    safe_low: int
    safe_high: int
    requires_thermometer: bool = True


@dataclass
class Prop:
    id: str
    label: str
    purpose: str
    kind: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    theme: str = "adventure"
    challenge: str = "cold_castle"
    prop: str = "thermometer"
    rap_style: str = "silly"
    hero: str = "Milo"
    hero_type: str = "boy"
    friend: str = "Nina"
    friend_type: str = "girl"
    seed: Optional[int] = None


THEMES = {
    "adventure": Theme(
        id="adventure",
        frame="a wild map and a windy hill",
        fortress="a crooked stone fortress",
        quest="reach the top chamber",
        ending="they marched out laughing, ready for the next quest",
    ),
    "castle": Theme(
        id="castle",
        frame="a pretend kingdom",
        fortress="a tall toy fortress",
        quest="find the bright banner room",
        ending="they waved from the tower and planned another brave game",
    ),
}

CHALLENGES = {
    "cold_castle": Challenge(
        id="cold_castle",
        label="a chilly fortress hall",
        risk="the room felt too cold for a long stay",
        safe_low=18,
        safe_high=26,
    ),
    "hot_kitchen": Challenge(
        id="hot_kitchen",
        label="a warm kitchen corridor",
        risk="the room felt too warm to leave shut up",
        safe_low=20,
        safe_high=24,
    ),
}

PROPS = {
    "thermometer": Prop(
        id="thermometer",
        label="thermometer",
        purpose="check the temperature",
        kind="tool",
        tags={"thermometer", "temperature"},
    ),
    "rap": Prop(
        id="rap",
        label="rap notebook",
        purpose="make silly rhymes",
        kind="tool",
        tags={"rap", "humor"},
    ),
    "lantern": Prop(
        id="lantern",
        label="lantern",
        purpose="light the dark corners",
        kind="tool",
        tags={"light"},
    ),
}


def _r_temperature(world: World) -> list[str]:
    out: list[str] = []
    fort = world.get("fortress")
    if fort.meters.get("temperature", 0.0) < THRESHOLD:
        sig = ("temp",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__temp__")
    return out


CAUSAL_RULES = [("temperature", _r_temperature)]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for tid in THEMES:
        for cid, ch in CHALLENGES.items():
            for pid, prop in PROPS.items():
                if cid == "cold_castle" and pid == "thermometer":
                    combos.append((tid, cid, pid))
                if cid == "hot_kitchen" and pid == "thermometer":
                    combos.append((tid, cid, pid))
                if prop.kind == "tool" and prop.id == "rap" and cid == "cold_castle":
                    combos.append((tid, cid, pid))
    return sorted(set(combos))


def is_reasonable(params: StoryParams) -> bool:
    return (params.theme in THEMES and params.challenge in CHALLENGES and params.prop in PROPS)


def explain_rejection(params: StoryParams) -> str:
    if params.prop != "thermometer":
        return "(No story: this world needs a thermometer to check the fortress temperature.)"
    return "(No story: the chosen combination does not make a clear adventure with a moral turn.)"


def tell(theme: Theme, challenge: Challenge, prop: Prop, hero_name: str, hero_type: str,
         friend_name: str, friend_type: str, rap_style: str) -> World:
    w = World()
    hero = w.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    friend = w.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    fort = w.add(Entity(id="fortress", kind="place", type="fortress", label=theme.fortress))
    thermo = w.add(Entity(id="thermometer", kind="thing", type="tool", label="thermometer", role="tool"))
    rap = w.add(Entity(id="rap", kind="thing", type="tool", label="rap notebook", role="tool"))
    fort.meters["temperature"] = 15.0
    fort.meters["danger"] = 0.0
    hero.memes["joy"] = 1.0
    friend.memes["worry"] = 1.0

    w.say(f"{hero_name} and {friend_name} climbed toward {theme.frame}, where {theme.fortress} waited.")
    w.say(f"They were on a quest to {theme.quest}, and {hero_name} carried a {prop.label}.")
    w.para()

    hero.memes["humor"] += 1
    w.say(f'{hero_name} grinned. "I will rap to the fortress!" {hero_name} said.')
    w.say(f'{friend_name} giggled. "Only if the fortress does not rap back!" {friend_name} said.')

    old_temp = fort.meters["temperature"]
    fort.meters["temperature"] = 15.0
    w.facts["old_temp"] = old_temp
    w.facts["new_temp"] = fort.meters["temperature"]
    w.facts["challenge"] = challenge
    w.facts["theme"] = theme
    w.facts["prop"] = prop
    w.facts["hero"] = hero
    w.facts["friend"] = friend

    w.para()
    w.say(f"Before they went inside, {friend_name} checked the {thermo.label}.")
    w.say(f"The little needle said {int(fort.meters['temperature'])} degrees, which meant {challenge.risk}.")
    if fort.meters["temperature"] < challenge.safe_low:
        friend.memes["worry"] += 1
        w.say(f'"That is too chilly," {friend_name} said. "A brave explorer should also be kind."')

    w.para()
    w.say(f"Then came a flashback: yesterday, {hero_name} had seen an old guard share a cloak with a shivering kitten.")
    hero.memes["moral"] += 1
    w.say(f"{hero_name} remembered that being bold was better when it helped someone else too.")
    w.say(f"So instead of rushing, {hero_name} used the {prop.label} to check the hall and spoke a silly rap about warm socks, careful steps, and helping friends.")
    if rap_style == "silly":
        w.say(f'"I am the scout with the stout little shout," {hero_name} rapped, "and I care if my pal is cold without doubt!"')
    else:
        w.say(f'"I keep the quest neat, and I keep my friend safe on her feet," {hero_name} rapped.')
    hero.memes["humor"] += 1
    friend.memes["joy"] += 1
    fort.meters["danger"] = 0.0
    w.say(f"{friend_name} laughed so hard that even the stones seemed friendlier.")
    w.para()
    w.say(f"They found a warm side passage, wrapped a spare cloak around the drafty doorway, and continued the adventure.")
    w.say(f"In the end, {theme.ending}.")

    w.facts["outcome"] = "safe"
    w.facts["humor_line"] = True
    w.facts["flashback"] = True
    w.facts["moral"] = True
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story that includes the words "rap", "thermometer", and "fortress".',
        f"Tell a child-friendly fortress adventure where a funny rap and a thermometer help two children make a kind choice.",
        f"Write a story with a flashback, humor, and a moral lesson set near a fortress on a chilly day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    fort = world.get("fortress")
    challenge = world.facts["challenge"]
    prop = world.facts["prop"]
    qa = [
        QAItem(
            question="What did the children use to check the fortress?",
            answer=f"They used a thermometer. It let them check the fortress before they went farther inside.",
        ),
        QAItem(
            question="Why did they slow down instead of rushing in?",
            answer=f"The thermometer showed the fortress was too cold, so they slowed down and looked for a safer path. They wanted the adventure to stay fun without making anyone shiver.",
        ),
        QAItem(
            question="What did the flashback help the hero remember?",
            answer=f"It helped {hero.id} remember that kindness matters in brave moments. The old memory of sharing a cloak led to a better choice in the present.",
        ),
        QAItem(
            question="How did the rap part help the story?",
            answer=f"The rap made the scene funny and kept the mood light. It also helped {hero.id} choose words that cared about {friend.id} instead of just showing off.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a thermometer for?",
            answer="A thermometer is a tool for checking temperature. People use it to see whether something is cold, warm, or hot.",
        ),
        QAItem(
            question="What is a fortress?",
            answer="A fortress is a strong building made for protection. In adventures, it can feel like a castle or a guarded place to explore.",
        ),
        QAItem(
            question="What is a rap?",
            answer="A rap is a kind of spoken rhyme with a beat. It can sound playful and funny when someone performs it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(theme="adventure", challenge="cold_castle", prop="thermometer", rap_style="silly", hero="Milo", hero_type="boy", friend="Nina", friend_type="girl"),
    StoryParams(theme="castle", challenge="cold_castle", prop="thermometer", rap_style="silly", hero="Ava", hero_type="girl", friend="Ben", friend_type="boy"),
]


ASP_RULES = r"""
valid(T,C,P) :- theme(T), challenge(C), prop(P), thermometer(P).
moral(T) :- theme(T), challenge(C), C = cold_castle.
flashback(T) :- theme(T), prop(thermometer), challenge(cold_castle).
humor(T) :- prop(rap).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge", cid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
        if pid == "thermometer":
            lines.append(asp.fact("thermometer", pid))
        if pid == "rap":
            lines.append(asp.fact("rap", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import sys as _sys
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: clingo gate differs from Python gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = format_qa(sample)
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with rap, thermometer, fortress, moral value, flashback, and humor.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--rap-style", choices=["silly", "steady"], dest="rap_style")
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    theme = args.theme or rng.choice(list(THEMES))
    challenge = args.challenge or rng.choice(list(CHALLENGES))
    prop = args.prop or "thermometer"
    if prop not in PROPS:
        raise StoryError("Unknown prop.")
    if prop != "thermometer":
        raise StoryError(explain_rejection(StoryParams(theme=theme, challenge=challenge, prop=prop)))
    return StoryParams(
        theme=theme,
        challenge=challenge,
        prop=prop,
        rap_style=args.rap_style or rng.choice(["silly", "steady"]),
        hero=args.hero or rng.choice(["Milo", "Ava", "Nia", "Leo"]),
        hero_type="girl" if (args.hero and args.hero in {"Ava", "Nia"}) else rng.choice(["boy", "girl"]),
        friend=args.friend or rng.choice(["Nina", "Ben", "Oren", "Luna"]),
        friend_type="girl" if (args.friend and args.friend in {"Nina", "Luna"}) else rng.choice(["boy", "girl"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES or params.challenge not in CHALLENGES or params.prop not in PROPS:
        raise StoryError("Invalid story parameters.")
    if params.prop != "thermometer":
        raise StoryError(explain_rejection(params))
    world = tell(THEMES[params.theme], CHALLENGES[params.challenge], PROPS[params.prop],
                 params.hero, params.hero_type, params.friend, params.friend_type, params.rap_style)
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
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
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

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
