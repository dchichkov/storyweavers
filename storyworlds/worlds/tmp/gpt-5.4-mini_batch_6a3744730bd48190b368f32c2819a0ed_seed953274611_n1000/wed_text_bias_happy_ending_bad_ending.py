#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wed_text_bias_happy_ending_bad_ending.py
=========================================================================

A small standalone storyworld about pirate-ship messages, a wedding plan,
and the difference between a fair reading and a biased one.

Premise:
- A harbor crew is preparing a wed ceremony on a ship.
- A text message can carry bias and cause trouble.
- The story can end happily or badly depending on whether the crew checks the
  message and corrects the unfairness.

Seed words: wed, text, bias
Style: pirate tale
Features: happy ending, bad ending
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "bride"}
        male = {"boy", "man", "father", "groom"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    setting: str
    crew: str
    captain: str
    bride: str
    groom: str
    messenger: str
    bias_word: str
    ending: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": "the windy harbor by the dock",
    "island": "the bright island cove",
    "ship": "the moonlit ship deck",
}

CREWS = {
    "pirates": "pirates",
    "sailors": "sailors",
    "buccaneers": "buccaneers",
}

MESSAGES = {
    "rumor": {
        "label": "a text rumor",
        "text": "a text rumor that claimed the wedding was a joke",
        "message": "texted",
    },
    "invite": {
        "label": "a text invite",
        "text": "a text invite with the wedding time",
        "message": "texted",
    },
    "warning": {
        "label": "a warning text",
        "text": "a warning text about the harbor wind",
        "message": "texted",
    },
}

BIAS_WORDS = {
    "mean": "mean",
    "snobbish": "snobbish",
    "unfair": "unfair",
}

ENDINGS = {"happy", "bad"}


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        if world.get("letter").meters["bias"] >= THRESHOLD and ("bias",) not in world.fired:
            world.fired.add(("bias",))
            world.get("captain").memes["worry"] += 1
            world.get("bride").memes["hurt"] += 1
            world.get("groom").memes["hurt"] += 1
            changed = True
        if world.get("deck").meters["joy"] >= THRESHOLD and ("joy",) not in world.fired:
            world.fired.add(("joy",))
            world.get("captain").memes["hope"] += 1
            changed = True


def predict_bias(world: World) -> dict:
    sim = world.copy()
    sim.get("letter").meters["bias"] += 1
    propagate(sim)
    return {
        "hurt": sim.get("bride").memes["hurt"] + sim.get("groom").memes["hurt"],
        "worry": sim.get("captain").memes["worry"],
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale about wed, text, and bias.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--crew", choices=CREWS)
    ap.add_argument("--message", choices=MESSAGES)
    ap.add_argument("--bias", choices=BIAS_WORDS)
    ap.add_argument("--ending", choices=sorted(ENDINGS))
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MESSAGES:
            for e in ENDINGS:
                combos.append((s, m, e))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MESSAGES:
        lines.append(asp.fact("message", m))
    for e in ENDINGS:
        lines.append(asp.fact("ending", e))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,E) :- setting(S), message(M), ending(E).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos disagree")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.message is None or c[1] == args.message)
              and (args.ending is None or c[2] == args.ending)]
    if not combos:
        raise StoryError("No valid story matches those options.")
    setting, message, ending = rng.choice(sorted(combos))
    crew = args.crew or rng.choice(sorted(CREWS))
    bias = args.bias or rng.choice(sorted(BIAS_WORDS))
    return StoryParams(
        setting=setting,
        crew=crew,
        captain=rng.choice(["Cap'n Mira", "Cap'n Finn", "Cap'n Rowe"]),
        bride=rng.choice(["Ava", "Mina", "Lily"]),
        groom=rng.choice(["Tom", "Ned", "Jace"]),
        messenger=message,
        bias_word=bias,
        ending=ending,
    )


def tell(params: StoryParams) -> World:
    w = World()
    deck = w.add(Entity(id="deck", kind="place", type="deck", label="the deck"))
    captain = w.add(Entity(id="captain", kind="character", type="captain", label="the captain"))
    bride = w.add(Entity(id="bride", kind="character", type="bride", label=params.bride))
    groom = w.add(Entity(id="groom", kind="character", type="groom", label=params.groom))
    letter = w.add(Entity(id="letter", kind="thing", type="message", label="the text"))
    w.facts.update(params=params, deck=deck, captain=captain, bride=bride, groom=groom, letter=letter)

    w.say(f"On {SETTINGS[params.setting]}, the {CREWS[params.crew]} were busy preparing to wed {bride.label_word} and {groom.label_word}.")
    w.say(f"Cap'n {params.captain.split()[-1]} had lanterns, ribbons, and a cake with blue frosting, and the whole deck smelled like salt and sugar.")
    w.para()
    w.say(f"Then {params.messenger} came with {MESSAGES[params.messenger]['text']}, and the words carried a {params.bias_word} bias.")
    pred = predict_bias(w)
    w.facts["predicted"] = pred
    letter.meters["bias"] += 1
    propagate(w)

    if params.ending == "happy":
        w.say(f"The captain spotted the bias in the text and frowned. 'That message is unfair,' {captain.pronoun()} said.")
        w.say(f"Together they sent a fair reply, fixed the invite, and called everyone back to the deck.")
        deck.meters["joy"] += 1
        propagate(w)
        w.para()
        w.say(f"At sunset, the crew wed the pair under a string of gold lanterns, and even the gulls seemed to cheer.")
        w.say(f"The unfair text was crumpled away, and the night ended with music, laughter, and a cake with one extra slice for the happy couple.")
    else:
        w.say(f"The captain trusted the biased text and did not check it again.")
        w.say(f"The invite went out wrong, the wrong folk stayed away, and the wedding grew cold and lonely on the wet deck.")
        w.para()
        w.say(f"By nightfall the crew still wed the pair, but the music sounded small, and the moon shone on a sad, half-empty feast.")
        w.say(f"The biased message had done its harm, and the crew learned too late that not every text tells the truth.")

    w.facts["ending"] = params.ending
    return w


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a pirate tale that includes the words wed, text, and bias, and ends with a {p.ending} ending.",
        f"Tell a short story about a pirate wedding where a text message has bias and the crew must decide what to do.",
        f"Write a child-friendly story on a ship where the characters wed someone after reading a text, and the bias in the text matters.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    ending = p.ending
    return [
        QAItem(
            question="What was the story about?",
            answer="It was about a pirate crew getting ready to wed two people on a windy ship deck, then dealing with a text message that carried bias."
        ),
        QAItem(
            question="Why did the text matter?",
            answer="The text mattered because it changed how the crew thought about the wedding. If the message was biased, it could make the invite unfair and spoil the day."
        ),
        QAItem(
            question="How did the story end?",
            answer=("It ended happily, with the crew correcting the unfair text and celebrating the wed ceremony under lantern light."
                    if ending == "happy" else
                    "It ended badly, with the crew trusting the biased text and the wedding feeling lonely and sad.")
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a text message?",
            answer="A text message is a short message sent on a phone. People use texts to share news, plans, and quick notes."
        ),
        QAItem(
            question="What is bias?",
            answer="Bias means treating one person or idea unfairly because of a one-sided opinion. A biased message does not give a fair picture."
        ),
        QAItem(
            question="What does wed mean?",
            answer="Wed means to get married. In stories, it often means two people promise to be partners."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.ending not in ENDINGS:
        raise StoryError("Invalid ending.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="harbor", crew="pirates", captain="Cap'n Mira", bride="Ava", groom="Tom", messenger="invite", bias_word="unfair", ending="happy"),
    StoryParams(setting="ship", crew="buccaneers", captain="Cap'n Finn", bride="Mina", groom="Ned", messenger="rumor", bias_word="mean", ending="bad"),
]


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
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
