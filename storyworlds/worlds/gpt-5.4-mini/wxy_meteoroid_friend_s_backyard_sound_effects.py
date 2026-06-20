#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wxy_meteoroid_friend_s_backyard_sound_effects.py
=================================================================================

A standalone story world for a small slice-of-life backyard tale with sound
effects, surprise, and a bad ending.

Premise
-------
Two friends are playing in a friend's backyard when they notice a strange
sound. A surprise meteoroid lands nearby, making a loud noise and startling
them. One child tries to keep playing, but the other notices danger and calls
for help. The ending is bad in the sense that the game is ruined and something
gets damaged, but everyone gets to safety.

This world is intentionally tiny:
- one backyard setting
- two child characters
- one surprise falling object
- one small damaged thing
- one adult response that can fail if the impact is too sudden

The story is driven by world state, not a frozen paragraph template.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/wxy_meteoroid_friend_s_backyard_sound_effects.py
    python storyworlds/worlds/gpt-5.4-mini/wxy_meteoroid_friend_s_backyard_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4-mini/wxy_meteoroid_friend_s_backyard_sound_effects.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/wxy_meteoroid_friend_s_backyard_sound_effects.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
DEFAULT_SEVERITY = 2.0
ADULT_REASONS = {"careful", "steady", "watchful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Backyard:
    place: str
    fence: str
    table: str
    toy: str
    sound: str
    surprise_word: str
    ending_note: str


@dataclass
class FallingThing:
    id: str
    label: str
    sound: str
    dangerous: bool = True
    surprise: bool = True
    breaks: bool = True


@dataclass
class Response:
    id: str
    power: int
    sense: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    setting: str
    sound_effect: str
    surprise: str
    ending: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
    adult: str
    trait: str
    seed: Optional[int] = None


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def pronoun_name(name: str, gender: str, case: str = "subject") -> str:
    return {"subject": "she" if gender == "girl" else "he",
            "object": "her" if gender == "girl" else "him",
            "possessive": "her" if gender == "girl" else "his"}[case]


def summarize_sound(effect: str) -> str:
    return {
        "clink": "a soft clink",
        "boom": "a sudden boom",
        "whirr": "a strange whirr",
        "thud": "a heavy thud",
    }.get(effect, "a strange sound")


def sound_word(effect: str) -> str:
    return {
        "clink": "Clink!",
        "boom": "Boom!",
        "whirr": "Whirr!",
        "thud": "Thud!",
    }.get(effect, effect.capitalize() + "!")


def _rule_damage(world: World) -> list[str]:
    out: list[str] = []
    rock = world.entities.get("meteoroid")
    if not rock or rock.meters["falling"] < THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    yard = world.get("yard")
    yard.meters["damage"] += rock.meters["impact"]
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["surprise"] += 1
            e.memes["fear"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [_rule_damage]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_surprise(world: World) -> dict:
    sim = world.copy()
    sim.get("meteoroid").meters["falling"] = 1.0
    sim.get("meteoroid").meters["impact"] = DEFAULT_SEVERITY
    propagate(sim, narrate=False)
    return {
        "damage": sim.get("yard").meters["damage"],
        "fear": sum(e.memes["fear"] for e in sim.entities.values() if e.kind == "character"),
    }


def nice_response() -> Response:
    return RESPONSES["call_adult"]


def response_ok(resp: Response) -> bool:
    return resp.sense >= 2


def story_bad_end(severity: float) -> bool:
    return severity >= 2.0


def backyard_words() -> Backyard:
    return BACKYARDS["friend"]


def tell(backyard: Backyard, rock: FallingThing, response: Response,
         name_a: str = "Wxy", gender_a: str = "girl",
         name_b: str = "Mina", gender_b: str = "girl",
         adult: str = "parent", trait: str = "careful",
         severity: float = DEFAULT_SEVERITY) -> World:
    world = World()
    a = world.add(Entity(name_a, kind="character", type=gender_a, role="instigator", traits=["curious"]))
    b = world.add(Entity(name_b, kind="character", type=gender_b, role="cautioner", traits=[trait]))
    grown = world.add(Entity("Adult", kind="character", type=adult, role="adult", label="the grown-up"))
    yard = world.add(Entity("yard", type="place", label=backyard.place))
    meteoroid = world.add(Entity("meteoroid", type="thing", label=rock.label))
    meteoroid.meters["falling"] = 1.0
    meteoroid.meters["impact"] = float(severity)

    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"One afternoon, {a.id} and {b.id} played in {backyard.place}. "
        f"The {backyard.fence} and the {backyard.table} made it feel like a small, safe world."
    )
    world.say(
        f'They were bouncing around when {summarize_sound(backyard.sound)} came from above. '
        f'"{sound_word(backyard.sound)}"'
    )
    world.say(
        f"{a.id} looked up first. A tiny {rock.label} was dropping fast, and {b.id} blinked in surprise."
    )

    world.para()
    a.memes["curiosity"] += 1
    b.memes["warning"] += 1
    world.say(
        f'"Look!" {a.id} said. "That {rock.label} just fell into {backyard.place}!" '
        f'For a second, it felt like a surprise from the sky.'
    )
    if response_ok(response):
        world.say(
            f'{b.id} frowned and pointed at the spot. "We should call {grown.label_word if grown.label else "a grown-up"}."'
        )
    else:
        raise StoryError("The chosen response is not sensible for a backyard meteoroid surprise.")

    world.para()
    rock.meters["near"] = 1.0
    rock.meters["falling"] = 0.0
    rock.meters["impact"] = float(severity)
    if story_bad_end(severity):
        propagate(world, narrate=False)
        world.say(
            f"The {rock.label} hit with a nasty {summarize_sound('thud')}. "
            f"Bits of dirt flew up, and the little game stopped at once."
        )
        world.say(
            f"{a.id} and {b.id} backed away while {grown.id} hurried over, arms open and eyes wide."
        )
        world.say(
            f"{grown.label_word.capitalize()} checked that everyone was safe, but the best part of the day was gone. "
            f"The yard was scuffed up, and the friends felt quiet instead of playful."
        )
        world.say(
            f"After that, they sat on the porch and watched the sky. It was still pretty, but not magical anymore."
        )
    else:
        propagate(world, narrate=False)
        world.say(
            f"The {rock.label} made only a small dent, and {grown.id} got there quickly. "
            f"The surprise was over before it could turn the whole yard upside down."
        )
        world.say(f"{grown.label_word.capitalize()} helped them step back and look at the sky from a safe distance.")
        world.say(
            f"Even so, the afternoon felt changed: the toy was still there, but the easy backyard fun had paused."
        )

    world.facts.update(
        instigator=a, cautioner=b, adult=grown, yard=yard,
        backyard=backyard, rock=rock, response=response,
        outcome="bad" if story_bad_end(severity) else "soft",
        sound=backyard.sound, surprise=backyard.surprise_word,
        severity=severity, damage=world.get("yard").meters["damage"],
    )
    return world


BACKYARDS = {
    "friend": Backyard(
        place="a friend's backyard",
        fence="wooden fence",
        table="picnic table",
        toy="plastic shovel",
        sound="boom",
        surprise_word="meteoroid",
        ending_note="bad ending",
    ),
    "neighbor": Backyard(
        place="a neighbor's backyard",
        fence="green fence",
        table="small table",
        toy="red ball",
        sound="whirr",
        surprise_word="meteoroid",
        ending_note="surprise",
    ),
}

METEOROIDS = {
    "meteoroid": FallingThing("meteoroid", "meteoroid", "meteoroid", True, True, True),
}

RESPONSES = {
    "call_adult": Response("call_adult", power=3, sense=3,
                           text="called for a grown-up and pointed to the strange spot",
                           fail="tried to fix it alone, but the trouble was too sudden",
                           qa_text="called for a grown-up right away"),
}

NAMES = ["Wxy", "Mina", "Pip", "Luz", "Nico", "Tia", "Rey", "Zia"]
TRAITS = ["careful", "steady", "watchful", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(bid, "meteoroid", "call_adult") for bid in BACKYARDS]


@dataclass
class StoryParams:
    backyard: str
    sound_effect: str
    surprise: str
    ending: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "meteoroid": [("What is a meteoroid?",
                   "A meteoroid is a small rock from space. It can fall fast and make a surprise when it lands.")],
    "sound": [("What is a sound effect?",
               "A sound effect is a sound that helps tell what is happening, like a boom or a thud.")],
    "backyard": [("What is a backyard?",
                  "A backyard is the open space behind a house where kids can play outside.")],
    "surprise": [("Why can a surprise be startling?",
                  "A surprise can be startling when it happens suddenly and you do not expect it.")],
}
KNOWLEDGE_ORDER = ["meteoroid", "sound", "backyard", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that takes place in {f["backyard"].place} and includes the word "wxy".',
        f'Tell a story with the words "wxy" and "meteoroid" where a strange sound interrupts play in {f["backyard"].place}.',
        f"Write a short backyard story with a surprise falling rock, a loud sound effect, and a bad ending that still feels realistic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, adult = f["instigator"], f["cautioner"], f["adult"]
    back = f["backyard"]
    rock = f["rock"]
    out = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two friends playing in {back.place}. The grown-up is there too, but the friends are the ones at the center of the surprise."
        ),
        QAItem(
            question="What interrupted their play?",
            answer=f"A {rock.label} fell from the sky and made a loud {summarize_sound(back.sound)}. The sudden sound turned an ordinary backyard afternoon into a surprise."
        ),
        QAItem(
            question="What did the cautious friend do?",
            answer=f"{b.id} told {a.id} to call {adult.label_word if adult.label else 'a grown-up'} right away. That choice fit the danger because a falling meteoroid is not something kids can handle alone."
        ),
    ]
    if f["outcome"] == "bad":
        out.append(
            QAItem(
                question="How did the story end?",
                answer="It ended badly for the playtime: the yard got scuffed up, the game stopped, and the friends felt quiet. They were safe, but the cheerful backyard moment was gone."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    topics = {"meteoroid", "sound", "backyard", "surprise"}
    qas: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in topics:
            q, a = KNOWLEDGE[key][0]
            qas.append(QAItem(q, a))
    return qas


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(B) :- backyard(B), meteoroid(meteoroid), response(call_adult).
bad_end(S) :- severity(S), S >= 2.
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("backyard", bid) for bid in BACKYARDS]
    lines += [asp.fact("meteoroid", "meteoroid")]
    lines += [asp.fact("response", "call_adult")]
    lines += [asp.fact("severity", 2)]
    return "\n".join(lines)

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != {(b,) for b, _, _ in valid_combos()}:
        print("MISMATCH in valid combos")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(backyard=None, seed=777), _random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Backyard meteoroid story world.")
    ap.add_argument("--backyard", choices=BACKYARDS)
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
    back = args.backyard or rng.choice(list(BACKYARDS))
    return StoryParams(
        backyard=back,
        sound_effect=BACKYARDS[back].sound,
        surprise="surprise",
        ending="bad",
        instigator=rng.choice(NAMES),
        instigator_gender=rng.choice(["girl", "boy"]),
        cautioner=rng.choice([n for n in NAMES if n != ""]),
        cautioner_gender=rng.choice(["girl", "boy"]),
        adult="parent",
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        BACKYARDS[params.backyard],
        METEOROIDS["meteoroid"],
        RESPONSES["call_adult"],
        params.instigator,
        params.instigator_gender,
        params.cautioner,
        params.cautioner_gender,
        params.adult,
        params.trait,
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
    StoryParams("friend", "boom", "surprise", "bad", "Wxy", "girl", "Mina", "girl", "parent", "careful"),
    StoryParams("neighbor", "whirr", "surprise", "bad", "Wxy", "boy", "Pip", "girl", "parent", "watchful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
