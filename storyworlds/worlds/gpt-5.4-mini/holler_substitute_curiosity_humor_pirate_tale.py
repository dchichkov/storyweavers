#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/holler_substitute_curiosity_humor_pirate_tale.py
=================================================================================

A standalone storyworld for a tiny pirate-tale domain: curious children aboard a
pretend ship discover a missing calling tool, improvise a substitute, and use a
big funny holler to keep the adventure going. The domain is built around two
core features from the seed: Curiosity and Humor.

The story model keeps physical meters and emotional memes on typed entities,
drives prose from state changes, and supports a small ASP twin for parity checks.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "captain"}
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
    scene: str
    crew_name: str
    ship_name: str
    wind: str
    tail: str


@dataclass
class MissingCall:
    id: str
    label: str
    sound: str
    location: str
    use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Substitute:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class OutcomeTool:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_shine(world: World) -> list[str]:
    out: list[str] = []
    if world.get("lantern").meters["used"] >= THRESHOLD:
        if "shine" in world.fired:
            return out
        world.fired.add(("shine",))
        world.get("crew").memes["glee"] += 1
        out.append("__shine__")
    return out


CAUSAL_RULES = [Rule("shine", "social", _r_shine)]


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


def sensible_outcomes() -> list[OutcomeTool]:
    return [o for o in OUTCOMES.values() if o.sense >= 2]


def reasonableness_gate(call: MissingCall, sub: Substitute) -> bool:
    return call.label == "holler" and sub.id in {"shell_holler", "cap_holler", "drum_holler"}


def predicted_fun(world: World, call: MissingCall, sub: Substitute) -> dict:
    sim = world.copy()
    _use_substitute(sim, sim.get("kid"), call, sub, narrate=False)
    return {"ready": sim.get("lantern").meters["used"] >= THRESHOLD}


def _use_substitute(world: World, kid: Entity, call: MissingCall, sub: Substitute, narrate: bool = True) -> None:
    kid.memes["curiosity"] += 1
    world.get("lantern").meters["used"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, setting: Setting, child: Entity, mate: Entity) -> None:
    child.memes["curiosity"] += 1
    mate.memes["humor"] += 1
    world.say(
        f"On a blustery afternoon, {child.id} and {mate.id} turned {setting.place} into "
        f"{setting.scene}. {setting.tail}"
    )
    world.say(
        f'"Captain {child.id}!" {mate.id} shouted. "Our {setting.ship_name} is ready for a trip!"'
    )


def missing_call(world: World, call: MissingCall, setting: Setting) -> None:
    world.say(
        f"But the crew needed a way to holler across the deck, and the usual {call.label} "
        f"was nowhere to be found in {call.location}."
    )
    world.say(f"{call.use.capitalize()} would have helped, but the pirates had to look first.")


def curious_search(world: World, child: Entity, call: MissingCall) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id}'s eyes got bright. {child.pronoun().capitalize()} wanted to peek into every "
        f"nook and cranny until the missing {call.label} turned up."
    )


def humor_beat(world: World, mate: Entity, child: Entity) -> None:
    mate.memes["humor"] += 1
    world.say(
        f'{mate.id} grinned. "If we find a fish, can it be the substitute?" {mate.pronoun()} joked.'
    )
    world.say(f"{child.id} laughed so hard the pretend ship wobbled a little.")


def choose_substitute(world: World, child: Entity, call: MissingCall, sub: Substitute) -> None:
    child.memes["confidence"] += 1
    world.say(
        f"Then {child.id} spotted {sub.phrase}. It could make a {call.label} sound without a real cry."
    )
    world.say(f'"That will do," {child.id} said. "A clever substitute for our pirate call!"')


def make_holler(world: World, child: Entity, sub: Substitute) -> None:
    world.get("lantern").meters["used"] += 1
    world.say(f"{sub.effect.capitalize()}, and {child.id} gave a mighty holler that rolled across the deck.")
    world.say("The sound bounced off the rail, the mast, and even the bucket by the door.")


def joyful_finish(world: World, child: Entity, mate: Entity, setting: Setting, call: MissingCall, sub: Substitute) -> None:
    child.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"At last the crew sailed on with their {sub.label}, smiling at their own smart trick."
    )
    world.say(
        f"They did not need the old {call.label} after all. "
        f"{setting.wind.capitalize()}, they kept exploring and laughing like true little pirates."
    )


def tell(setting: Setting, call: MissingCall, sub: Substitute, outcome: OutcomeTool,
         child_name: str = "Mina", child_type: str = "girl",
         mate_name: str = "Jory", mate_type: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="curious"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_type, role="funny"))
    crew = world.add(Entity(id="crew", kind="character", type="crew", label="the crew"))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern"))
    world.add(crew)
    world.add(lantern)
    world.facts["setting"] = setting

    setup(world, setting, child, mate)
    world.para()
    missing_call(world, call, setting)
    curious_search(world, child, call)
    humor_beat(world, mate, child)

    world.para()
    pred = predicted_fun(world, call, sub)
    world.facts["predicted_ready"] = pred["ready"]
    if not reasonableness_gate(call, sub):
        raise StoryError("This substitute does not fit the pirate holler well enough.")

    choose_substitute(world, child, call, sub)
    make_holler(world, child, sub)
    joyful_finish(world, child, mate, setting, call, sub)

    world.facts.update(
        child=child,
        mate=mate,
        crew=crew,
        call=call,
        substitute=sub,
        outcome=outcome,
        used_substitute=True,
    )
    return world


SETTINGS = {
    "harbor": Setting(
        "harbor",
        "the little harbor",
        "a dockyard full of rope, gulls, and a sleepy little boat",
        "pirate crew",
        "skiff",
        "the sea breeze",
        "Their shoes slapped the boards, and the water winked beside them.",
    ),
    "island": Setting(
        "island",
        "the sandy island",
        "a palm-shadowed beach with a bent old sign and a wobble of crates",
        "pirate crew",
        "cove boat",
        "the warm breeze",
        "The tide ticked softly, as if it were listening too.",
    ),
    "shipdeck": Setting(
        "shipdeck",
        "the ship deck",
        "a bright deck with a striped sail, a coil of rope, and a round porthole",
        "pirate crew",
        "sailboat",
        "the wind",
        "The boards creaked like they were telling jokes.",
    ),
}

CALLS = {
    "holler": MissingCall("holler", "holler", "a great shouting holler", "the captain's chest", "call to the crew",
                          tags={"holler"}),
}

SUBSTITUTES = {
    "shell_holler": Substitute("shell_holler", "conch shell", "a big conch shell", "It went whooo, like a sea ghost"),
    "cap_holler": Substitute("cap_holler", "captain's cap", "the captain's striped cap", "It flapped and made a silly poof"),
    "drum_holler": Substitute("drum_holler", "toy drum", "a tiny toy drum", "It thumped like a marching crab"),
}

OUTCOMES = {
    "bright": OutcomeTool("bright", 3, 3, "used the substitute and made the call bright and loud",
                          "tried the substitute, but the sound was too tiny to help",
                          "used the substitute to make the pirate call"),
    "laugh": OutcomeTool("laugh", 3, 2, "used the substitute and laughed at the funny echo",
                         "tried the substitute, but the joke fell flat",
                         "used the substitute and laughed"),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Pia", "Sora", "Tia"]
BOY_NAMES = ["Jory", "Puck", "Rafe", "Tobin", "Finn", "Oren"]


@dataclass
class StoryParams:
    setting: str
    call: str
    substitute: str
    outcome: str
    child: str
    child_gender: str
    mate: str
    mate_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CALLS:
            for sub in SUBSTITUTES:
                if reasonableness_gate(CALLS[c], SUBSTITUTES[sub]):
                    combos.append((s, c, sub))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale world with curiosity and humor.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--call", choices=CALLS)
    ap.add_argument("--substitute", choices=SUBSTITUTES)
    ap.add_argument("--outcome", choices=OUTCOMES)
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
              and (args.call is None or c[1] == args.call)
              and (args.substitute is None or c[2] == args.substitute)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, call, sub = rng.choice(sorted(combos))
    outcome = args.outcome or rng.choice(sorted(OUTCOMES))
    gender = rng.choice(["girl", "boy"])
    mate_gender = "boy" if gender == "girl" else "girl"
    child = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mate = rng.choice(BOY_NAMES if mate_gender == "boy" else GIRL_NAMES)
    return StoryParams(setting, call, sub, outcome, child, gender, mate, mate_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the word "holler" and the idea of a substitute.',
        f"Tell a curious, funny story where {f['child'].id} cannot find a real holler tool, so {f['child'].id} uses a substitute instead.",
        f"Write a short pirate adventure where curiosity and humor help the crew solve a missing-tool problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mate = f["mate"]
    call = f["call"]
    sub = f["substitute"]
    setting = f["setting"]
    return [
        QAItem(
            question="What problem did the pirates have?",
            answer=f"They needed a good way to holler across the deck, but the {call.label} was missing. That made them search carefully before the adventure could go on."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"{child.id} found {sub.phrase} and used it as a substitute for the missing {call.label}. It made a loud enough pirate sound to keep the game moving."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the crew smiling and sailing on at {setting.place}. The substitute worked, so the curious search turned into a funny win."
        ),
        QAItem(
            question=f"Why did {mate.id} laugh?",
            answer=f"{mate.id} laughed because the substitute was silly and the echo sounded funny. Humor helped the crew stay happy while they solved the problem."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a holler?", "A holler is a loud shout that carries far, like calling across a deck or down a dock."),
        QAItem("What is a substitute?", "A substitute is something you use instead of the usual thing when the usual thing is missing."),
        QAItem("Why are curious pirates helpful in stories?", "Curious pirates look closely, ask questions, and find solutions instead of giving up too soon."),
        QAItem("Why does humor help?", "Humor can keep everyone calm and cheerful while they solve a problem together."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CALLS[params.call], SUBSTITUTES[params.substitute], OUTCOMES[params.outcome], params.child, params.child_gender, params.mate, params.mate_gender)
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


ASP_RULES = r"""
valid(S, C, U) :- setting(S), call(C), substitute(U), ok(C, U).
ok(holler, shell_holler).
ok(holler, cap_holler).
ok(holler, drum_holler).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CALLS:
        lines.append(asp.fact("call", c))
    for u in SUBSTITUTES:
        lines.append(asp.fact("substitute", u))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story.strip()
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("harbor", "holler", "shell_holler", "bright", "Mina", "girl", "Jory", "boy"),
    StoryParams("island", "holler", "cap_holler", "laugh", "Nora", "girl", "Puck", "boy"),
    StoryParams("shipdeck", "holler", "drum_holler", "bright", "Tobin", "boy", "Lina", "girl"),
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
