#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mussel_surprise_myth.py
========================================================

A small myth-like storyworld about a child, a tidepool, a tricky mussel, and a
surprising gift from the sea. The world is classical and state-driven: a curious
hero gathers shells, hears an old warning, opens the mussel in a careful way, and
the surprise changes the ending image.

The domain is intentionally tiny:
- a beach pool or moonlit shore
- a brave child or fisher
- a mussel that hides something unexpected
- a helper elder who knows the old rule
- a surprise reveal that shifts the mood from want to wonder

The story quality goal is mythic but child-facing: concrete details, a clear
turn, and a final image that proves the surprise changed the world.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    scene: str
    light: str
    tide: str
    mystery: str


@dataclass
class Mussel:
    id: str
    label: str
    place: str
    shell: str
    surprise: str
    hidden_kind: str
    opens: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    text: str
    reveal: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "tidepool": Setting("tidepool", "At the tidepool, moonlight silvered the rocks and the sea breathed in and out.", "moonlight", "the tide", "the old water"),
    "shore": Setting("shore", "By the shore, the waves whispered against the sand and shells gleamed like little coins.", "sunset", "the tide", "the old water"),
}

MUSSELS = {
    "blue": Mussel("blue", "mussel", "among the black rocks", "a blue-black shell", "a pearl", "pearl", tags={"mussel", "shell", "surprise"}),
    "gold": Mussel("gold", "mussel", "in a shallow crack", "a dark shell", "a tiny golden coin", "coin", tags={"mussel", "shell", "surprise"}),
    "song": Mussel("song", "mussel", "under a tide-wet stone", "a striped shell", "a whispering note", "song", tags={"mussel", "shell", "surprise"}),
}

RESPONSES = {
    "gentle_open": Response("gentle_open", 3,
                            "lifted the shell to the light, pried it open gently, and let the secret inside be seen",
                            "revealed the surprise inside the shell",
                            "lifted the shell to the light and opened it gently, revealing the surprise inside"),
    "wash_and_open": Response("wash_and_open", 2,
                              "washed the shell in the sea foam, then opened it with careful hands",
                              "washed away the grit and showed what hid within",
                              "washed the shell in the sea foam and opened it with careful hands"),
    "wait_for_tide": Response("wait_for_tide", 2,
                              "waited for the tide to turn, then opened the shell when the water lay calm",
                              "let the mystery rest until it was ready",
                              "waited for the tide to turn and opened the shell when the water lay calm"),
}

GIRL_NAMES = ["Mira", "Lina", "Sera", "Nora", "Ari", "Tala"]
BOY_NAMES = ["Orin", "Pax", "Ivo", "Niko", "Rami", "Toma"]
TRAITS = ["curious", "brave", "gentle", "patient", "bright", "careful"]
ELDERS = ["grandmother", "grandfather", "old fisher", "sea aunt"]


@dataclass
class StoryParams:
    setting: str
    mussel: str
    response: str
    hero: str
    hero_gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MUSSELS:
            for r in RESPONSES:
                if MUSSELS[m].opens and RESPONSES[r].sense >= SENSE_MIN:
                    combos.append((s, m, r))
    return combos


def reasonableness_gate(mussel: Mussel, response: Response) -> None:
    if not mussel.opens:
        raise StoryError("That shell will not open, so there can be no surprise.")
    if response.sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{response.id}': it is too weak for a mythic surprise.)")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like surprise storyworld about a mussel and a hidden gift.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mussel", choices=MUSSELS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.mussel is None or c[1] == args.mussel)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mussel, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    reasonableness_gate(MUSSELS[mussel], RESPONSES[response])
    return StoryParams(setting, mussel, response, name, gender, elder, trait)


def predict_surprise(world: World, mussel_id: str) -> dict:
    sim = world.copy()
    shell = sim.get(mussel_id)
    shell.meters["opened"] = 1.0
    shell.memes["wonder"] = 1.0
    return {"opened": shell.meters["opened"] >= THRESHOLD, "wonder": shell.memes["wonder"] >= THRESHOLD}


def tell(setting: Setting, mussel: Mussel, response: Response, hero_name: str, hero_gender: str, elder: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(hero_name, "character", hero_gender, role="hero", traits=[trait]))
    guide = world.add(Entity(elder, "character", "elder", role="guide"))
    shell = world.add(Entity("mussel", "thing", "mussel", label=mussel.label, role="secret", traits=["closed"], attrs={"surprise": mussel.surprise}))
    setting_ent = world.add(Entity("setting", "place", "place", label=setting.id))
    hero.memes["curiosity"] = 1.0
    guide.memes["calm"] = 1.0

    world.say(f"{setting.scene} A {trait} child named {hero.id} went looking for a mussel by the water.")
    world.say(f"{hero.pronoun().capitalize()} found {mussel.shell} {mussel.place}, and the old shell looked quiet as a stone.")
    world.para()
    world.say(f'The {elder} watched and said, "Some small things keep their biggest gift inside until they are ready."')
    world.say(f"{hero.id} knelt down and held the shell carefully. {hero.pronoun().capitalize()} did not crush it or rush it.")
    pred = predict_surprise(world, shell.id)
    world.facts["predicted"] = pred
    world.para()
    world.say(f"{response.text.capitalize()}.")
    shell.meters["opened"] = 1.0
    shell.memes["wonder"] = 1.0
    world.say(f"Inside the mussel was {mussel.surprise}, shining where no one expected it.")
    hero.memes["joy"] = 1.0
    hero.memes["wonder"] = 1.0
    guide.memes["joy"] = 1.0
    world.para()
    world.say(f"The {elder} smiled, and {hero.id} laughed in the moonlight like a child hearing an old sea song for the first time.")
    world.say(f"That night {hero.id} carried the little surprise home, and the shell no longer seemed ordinary at all.")
    world.facts.update(hero=hero, guide=guide, shell=shell, setting=setting, mussel=mussel, response=response, outcome="surprise")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the word "mussel" and ends in a surprise.',
        f"Tell a gentle myth about {f['hero'].id}, an old {f['guide'].id}, and a mussel that hides {f['mussel'].surprise}.",
        f'Write a sea-side surprise story in a dreamy style, with a careful child, an old warning, and a hidden gift inside a mussel.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    mussel = f["mussel"]
    response = f["response"]
    return [
        QAItem(question="What did the child find by the water?", answer=f"{hero.id} found a mussel in the {f['setting'].id}. It looked plain, but it was holding a surprise inside."),
        QAItem(question="What did the old helper say about the shell?", answer=f"The {guide.id} said some small things keep their biggest gift inside until they are ready. That warning made the opening feel careful and special."),
        QAItem(question="What was the surprise inside the mussel?", answer=f"Inside the mussel was {mussel.surprise}. The ending changed from a quiet search to a bright moment of wonder."),
        QAItem(question="How did the child open the shell?", answer=f"{hero.id} {response.qa_text}. The careful way mattered because it let the surprise stay whole."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a mussel?", answer="A mussel is a shellfish with two shells that live in water and cling to rocks or sand."),
        QAItem(question="Why should a shell be opened carefully?", answer="A shell can break if it is rushed or crushed, and then whatever is inside may be lost or damaged."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that you did not know was there before the moment you saw it."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, R) :- setting(S), mussel(M), response(R), opens(M), sense(R, X), sense_min(N), X >= N.
surprise(M) :- mussel(M), opens(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MUSSELS:
        lines.append(asp.fact("mussel", m))
        if MUSSELS[m].opens:
            lines.append(asp.fact("opens", m))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, RESPONSES[r].sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(7))
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    else:
        print("OK: gate matches and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MUSSELS[params.mussel], RESPONSES[params.response], params.hero, params.hero_gender, params.elder, params.trait)
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
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams("tidepool", "blue", "gentle_open", "Mira", "girl", "grandmother", "curious"),
            StoryParams("shore", "gold", "wash_and_open", "Orin", "boy", "old fisher", "brave"),
            StoryParams("tidepool", "song", "wait_for_tide", "Sera", "girl", "sea aunt", "patient"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx+1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
