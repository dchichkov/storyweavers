#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sillydilly_kindness_foreshadowing_pirate_tale.py
=================================================================================

A small standalone storyworld for a pirate-style tale with two narrative
instruments: kindness and foreshadowing.

Premise:
- A cheerful pirate crew is searching for treasure.
- One child is tempted to grab something greedy or noisy.
- A kind helper notices a foreshadowed clue that warns trouble is coming.
- Kindness turns the moment around, and the crew ends with a bright, safe image.

This world is intentionally tiny and classical: a few typed entities, physical
meters and emotional memes, a forward causal step, and state-driven prose.
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
FORESHADOW_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
class Setting:
    id: str
    scene: str
    detail: str
    treasure: str
    dark_place: str
    ship: str
    sendoff: str


@dataclass
class Trinket:
    id: str
    label: str
    phrase: str
    tempting: str
    shimmer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    warning: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    power: int
    sense: int
    text: str
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


def _r_warn(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["foreshadow"] < FORESHADOW_MIN:
        return out
    sig = ("warn", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crew = world.get("crew")
    crew.memes["unease"] += 1
    out.append("__clue__")
    return out


def _r_kind(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").memes["kindness"] < THRESHOLD:
        return out
    sig = ("kind", "hero")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("mate").memes["trust"] += 1
    out.append("__kind__")
    return out


RULES = [Rule("warn", "social", _r_warn), Rule("kind", "social", _r_kind)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_trouble(world: World, trinket: Trinket, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("hero").meters["greedy"] += 1
    sim.get("trinket").meters["taken"] += 1
    sim.get("clue").meters["foreshadow"] += 1
    propagate(sim, narrate=False)
    return {
        "unease": sim.get("crew").memes["unease"],
        "trust": sim.get("mate").memes["trust"],
    }


def sense_check(response: Response) -> bool:
    return response.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for trinket in TRINKETS:
            for clue in CLUES:
                combos.append((setting, trinket, clue))
    return combos


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    good = ", ".join(sorted(k for k, v in RESPONSES.items() if v.sense >= 2))
    return f"(Refusing response '{rid}': it is too silly for a safe rescue; try {good}.)"


def tell(setting: Setting, trinket: Trinket, clue: Clue, response: Response,
         hero_name: str = "Mina", hero_gender: str = "girl",
         mate_name: str = "Jory", mate_gender: str = "boy") -> World:
    world = World()
    hero = world.add(Entity(hero_name, kind="character", type=hero_gender,
                            role="hero", traits=["bright"]))
    mate = world.add(Entity(mate_name, kind="character", type=mate_gender,
                            role="mate", traits=["watchful"]))
    crew = world.add(Entity("Crew", kind="character", type="crew", label="the crew"))
    world.add(Entity("ship", type="ship", label="the ship"))
    world.add(Entity("clue", type="clue", label=clue.label))
    world.add(Entity("trinket", type="thing", label=trinket.label))

    hero.memes["kindness"] = 1.0
    mate.memes["trust"] = 1.0
    world.facts["setting"] = setting

    world.say(
        f"On a bright day, {hero.id} and {mate.id} sailed on {setting.ship}. "
        f"{setting.detail} {setting.scene}."
    )
    world.say(
        f"They were hunting for {setting.treasure}, and {setting.dark_place} felt "
        f"full of mystery."
    )
    world.say(
        f"{hero.id} noticed {clue.phrase}. It was a small thing, but it felt like a "
        f"hint from the wind: {clue.warning}"
    )

    world.para()
    hero.memes["greedy"] += 1
    world.say(
        f"{hero.id} saw {trinket.phrase} and wanted to take it. It {trinket.shimmer} "
        f"and looked like easy treasure."
    )
    if predict_trouble(world, trinket, clue)["unease"] >= 1:
        world.say(
            f"{mate.id} bit {mate.pronoun('possessive')} lip. "
            f'"Careful," {mate.id} said. "That little clue means trouble could be near."'
        )

    world.para()
    if sense_check(response):
        hero.memes["kindness"] += 1
        mate.memes["trust"] += 1
        world.say(
            f"{hero.id} stopped, looked at {mate.id}, and chose kindness instead of "
            f"snatching the shiny thing."
        )
        world.say(
            f'They used {response.text}, and the crew kept going with their lanterns '
            f"steady and their hearts calm."
        )
        world.say(
            f"At the end, {setting.sendoff}, and the whisper of {clue.label} stayed "
            f"behind like a lesson from the sea."
        )
        outcome = "kind"
    else:
        hero.memes["greedy"] += 1
        world.say(
            f"{hero.id} ignored the warning and reached for it anyway. The shiny lure "
            f"made the deck slippery with worry."
        )
        world.say(
            f"But {response.text}, and the crew had to back away from the mess."
        )
        world.say(
            f"In the end, they still found their way, but they remembered the clue "
            f"and the kinder choice that had been waiting."
        )
        outcome = "warned"

    world.facts.update(
        hero=hero, mate=mate, crew=crew, trinket=trinket, clue=clue,
        response=response, setting=setting, outcome=outcome,
    )
    return world


SETTINGS = {
    "harbor": Setting(
        "harbor", "The harbor smelled of salt and ropes.", "The dock creaked softly.",
        "a tiny silver key", "the old net bundle", "the little ship",
        "At sunset, they sailed on with bright eyes."),
    "island": Setting(
        "island", "The island grass danced in the breeze.", "The palms waved overhead.",
        "a gold shell map", "the cave mouth", "the little ship",
        "By moonrise, they sailed away with cheerful waves."),
    "reef": Setting(
        "reef", "The reef glittered under blue water.", "The waves tapped the hull.",
        "a pearl button", "the broken coral arch", "the little ship",
        "By evening, they sailed home with calm smiles."),
}

TRINKETS = {
    "key": Trinket("key", "a tiny silver key", "a tiny silver key",
                   "looked too shiny to ignore", "glimmered like moonlight",
                   {"shiny"}),
    "map": Trinket("map", "a gold shell map", "a gold shell map",
                   "seemed like a secret prize", "sparkled in the sun",
                   {"shiny"}),
    "button": Trinket("button", "a pearl button", "a pearl button",
                      "looked sweet and fancy", "gleamed on the sand",
                      {"shiny"}),
}

CLUES = {
    "wind": Clue("wind", "a wind clue", "a little curl of paper on the rail",
                 "the wind kept tugging it loose", {"foreshadow"}),
    "bird": Clue("bird", "a bird clue", "a gull circling twice overhead",
                 "the gull cried three sharp times", {"foreshadow"}),
    "shell": Clue("shell", "a shell clue", "a shell with a crack like a smile",
                  "the crack pointed toward the dark place", {"foreshadow"}),
}

RESPONSES = {
    "lantern": Response("lantern", 4, 3, "lit a lantern and checked the deck together", {"safe"}),
    "rope": Response("rope", 3, 2, "tied the loose crate with a rope and steadied the path", {"safe"}),
    "helper": Response("helper", 2, 2, "called a friendly deckhand to help them sort it out", {"safe"}),
    "sillydilly": Response("sillydilly", 1, 1, "said 'sillydilly!' and made a mess of the plan", {"sillydilly"}),
}

def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.response and not sense_check(RESPONSES[args.response]):
        raise StoryError(explain_response(args.response))
    combos = valid_combos()
    setting = args.setting or rng.choice(sorted(SETTINGS))
    trinket = args.trinket or rng.choice(sorted(TRINKETS))
    clue = args.clue or rng.choice(sorted(CLUES))
    response = args.response or rng.choice(sorted(rid for rid, r in RESPONSES.items() if r.sense >= 2))
    if (setting, trinket, clue) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    hero = args.hero or rng.choice(["Mina", "Lily", "Bo", "Jory", "Nia", "Pip"])
    mate = args.mate or rng.choice(["Jory", "Milo", "Rae", "Tess", "Finn"])
    return StoryParams(setting, trinket, clue, response, hero, args.hero_gender or "girl", mate, args.mate_gender or "boy")


@dataclass
class StoryParams:
    setting: str
    trinket: str
    clue: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a small child that includes the word "sillydilly".',
        f"Tell a story where {f['hero'].id} notices {f['clue'].label} and chooses kindness instead of grabbing {f['trinket'].label}.",
        f"Write a foreshadowing pirate story with a gentle warning, a kind choice, and a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What did the clue do in the story?",
            answer=f"It hinted that trouble could be near. That is why {f['mate'].id} warned {f['hero'].id} before the shiny thing caused a problem.",
        ),
        QAItem(
            question="How did kindness change the ending?",
            answer=f"{f['hero'].id} stopped and listened instead of grabbing the shiny treasure. That kind choice kept the crew calm and let them sail on safely.",
        ),
        QAItem(
            question="Why was the word sillydilly in the story?",
            answer="It made the pirate tale feel playful and silly. The word helped keep the story light, even when the clue warned that something could go wrong.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a little clue that hints something may happen later. It helps readers notice trouble before it arrives.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, share, or listen in a gentle way. Kind actions make other people feel safe and cared for.",
        ),
        QAItem(
            question="What is a pirate tale?",
            answer="A pirate tale is a story about ships, treasure, and adventures at sea. It often includes maps, decks, lanterns, and brave crew members.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for tid in TRINKETS:
        lines.append(asp.fact("trinket", tid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
        if r.sense >= 2:
            lines.append(asp.fact("safe", rid))
    lines.append(asp.fact("sense_min", 2))
    lines.append(asp.fact("foreshadow_min", 1))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, C) :- setting(S), trinket(T), clue(C).
safe_response(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(kind) :- safe_response(R), safe(R).
outcome(warned) :- response(R), not safe(R).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show safe_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "safe_response"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    if set(asp_sensible()) == {r for r, v in RESPONSES.items() if v.sense >= 2}:
        print("OK: sensible response set matches.")
    else:
        rc = 1
        print("MISMATCH in sensible response set.")
    sample = generate(StoryParams("harbor", "key", "wind", "lantern", "Mina", "girl", "Jory", "boy"))
    if not sample.story or "sillydilly" not in sample.prompts[0]:
        rc = 1
        print("MISMATCH: smoke-test generation failed.")
    else:
        print("OK: normal generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with kindness and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--trinket", choices=TRINKETS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        TRINKETS[params.trinket],
        CLUES[params.clue],
        RESPONSES[params.response],
        params.hero, params.hero_gender, params.mate, params.mate_gender,
    )
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


CURATED = [
    StoryParams("harbor", "key", "wind", "lantern", "Mina", "girl", "Jory", "boy"),
    StoryParams("island", "map", "bird", "rope", "Pip", "boy", "Rae", "girl"),
    StoryParams("reef", "button", "shell", "helper", "Lily", "girl", "Finn", "boy"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not sense_check(RESPONSES[args.response]):
        raise StoryError(explain_response(args.response))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    trinket = args.trinket or rng.choice(sorted(TRINKETS))
    clue = args.clue or rng.choice(sorted(CLUES))
    response = args.response or rng.choice(sorted(r for r, v in RESPONSES.items() if v.sense >= 2))
    if (setting, trinket, clue) not in valid_combos():
        raise StoryError("(No valid combination matches the given options.)")
    hero = args.hero or rng.choice(["Mina", "Lily", "Bo", "Jory", "Nia", "Pip"])
    mate = args.mate or rng.choice(["Jory", "Milo", "Rae", "Tess", "Finn"])
    return StoryParams(setting, trinket, clue, response, hero, args.hero_gender or "girl", mate, args.mate_gender or "boy")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show safe_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, t, c in asp_valid_combos():
            print(f"  {s:8} {t:8} {c}")
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
