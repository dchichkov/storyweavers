#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tug_dice_cuckoo_rhyme_inner_monologue_pirate.py
==============================================================================

A standalone story world for a tiny pirate tale with a tug-of-war, a dice
decision, and a cuckoo clock. The world uses typed entities with physical
meters and emotional memes, a reasonableness gate, a declarative ASP twin, and
state-driven prose with a bit of rhyme and inner monologue.

Seed words: tug, dice, cuckoo
Features: Rhyme, Inner Monologue
Style: Pirate Tale
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
SENSE_MIN = 2


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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Choice:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Setting:
    id: str
    scene: str
    dark_spot: str
    ship: str
    rhyme: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    cousin: str
    cousin_gender: str
    parent: str
    tool: str
    prize: str
    response: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_excite(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["drama"] < THRESHOLD:
            continue
        sig = ("drama", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in [x for x in list(world.entities.values()) if x.role in {"captain", "mate"}]:
            kid.memes["fear"] += 1
        out.append("")
    return out


CAUSAL_RULES = [("drama", _r_excite)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            if rule(world):
                changed = True


def hazard(tool: Choice, prize: Choice) -> bool:
    return "noise" in tool.tags and "game" in prize.tags


def sensible_responses() -> list[Choice]:
    return [c for c in RESPONSES.values() if c.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, tool in TOOLS.items():
            for pid, prize in PRIZES.items():
                if hazard(tool, prize):
                    combos.append((sid, tid, pid))
    return combos


def outcome_of(params: StoryParams) -> str:
    if not hazard(TOOLS[params.tool], PRIZES[params.prize]):
        return "invalid"
    return "contained" if RESPONSES[params.response].power >= PRIZES[params.prize].pressure else "lost"


def _do_tug(world: World, child: Entity, cousin: Entity, prize: Entity) -> None:
    child.meters["straining"] += 1
    cousin.meters["straining"] += 1
    prize.meters["tugged"] += 1
    world.get("ship").meters["rocking"] += 1
    propagate(world)


def _roll(world: World, child: Entity, cousin: Entity, tool: Choice) -> int:
    roll = world.facts["roll"]
    if roll % 2 == 0:
        child.memes["bold"] += 1
        world.say(f"{child.id} thought, \"A lucky roll will make the whole plan bright.\"")
    else:
        cousin.memes["worry"] += 1
        world.say(f"{cousin.id} thought, \"A lopsided roll can make a plan take flight.\"")
    return roll


def tell(setting: Setting, tool: Choice, prize: Choice, response: Choice,
         child_name: str, child_gender: str, cousin_name: str, cousin_gender: str,
         parent_type: str, roll: int = 2) -> World:
    world = World(setting)
    child = world.add(Entity(child_name, "character", child_gender, role="captain"))
    cousin = world.add(Entity(cousin_name, "character", cousin_gender, role="mate"))
    parent = world.add(Entity("Parent", "character", parent_type, label="the parent", role="parent"))
    ship = world.add(Entity("ship", "thing", "thing", label="the deck"))
    prize_ent = world.add(Entity("prize", "thing", "thing", label=prize.label))
    tool_ent = world.add(Entity("tool", "thing", "thing", label=tool.label))
    world.facts["roll"] = roll

    child.memes["joy"] += 1
    cousin.memes["joy"] += 1

    world.say(
        f"On {setting.id}, {child.id} and {cousin.id} were playing on {setting.scene}, "
        f"with a deck that swayed like a song."
    )
    world.say(
        f"They had {prize.phrase}, and the old {setting.rhyme} went, \"Cuckoo, cuckoo, "
        f"the clock knows what to do.\""
    )
    world.say(
        f"{child.id} wanted to use the {tool.label} for light, because the cave-like corner "
        f"looked dark as a stormy night."
    )
    world.say(
        f"In {child.id}'s head, a little thought kept spinning: \"If the dice say yes, "
        f"the dark may feel less scary. If the dice say no, I must be wary.\""
    )

    world.para()
    _roll(world, child, cousin, tool)
    if roll <= 1:
        world.say(f"The dice clattered and said no, so they left the {tool.label} alone.")
        world.say(f"They chose to tug the rope instead, and the deck sang back, light and fun.")
        world.para()
        world.say(
            f"{parent.label_word.capitalize()} smiled and handed them a lantern so they could keep watch."
        )
        world.say(
            f"{child.id} grinned at the glowing beam, and the rhyme of the sea stayed tame."
        )
        outcome = "avoided"
    else:
        world.say(f"The dice clicked yes, and {child.id} tugged the {tool.label} close.")
        _do_tug(world, child, cousin, prize_ent)
        world.say(
            f"A small spark of trouble twirled when the light met the dusty dark, and the air grew stark."
        )
        severity = 2 if roll >= 4 else 1
        prize_ent.meters["pressure"] = float(severity)
        contained = response.power >= severity
        world.para()
        if contained:
            world.say(
                f"{parent.label_word.capitalize()} came fast and {response.phrase}."
            )
            world.say(
                f"The worry washed away, and the crew could laugh the rest of the day."
            )
            world.para()
            world.say(
                f"{parent.label_word.capitalize()} showed them a lantern and a map, so the night stayed bright and snappy."
            )
            outcome = "contained"
        else:
            world.say(
                f"{parent.label_word.capitalize()} came fast, but {response.fail}."
            )
            world.say(
                f"The little mess grew into a bigger scare, and the crew had to step back and stare."
            )
            world.para()
            world.say(
                f"They left the noisy game and went ashore, while the cuckoo clock kept counting more."
            )
            outcome = "lost"

    world.facts.update(
        child=child, cousin=cousin, parent=parent, tool=tool, prize=prize,
        response=response, outcome=outcome, setting=setting
    )
    return world


SETTINGS = {
    "harbor": Setting("harbor", "the harbor deck", "the shadowy nook", "the deck", "Cuckoo, cuckoo, a pirate crew should never crook"),
    "island": Setting("island", "the island ship", "the crate under sail", "the ship", "Cuckoo, cuckoo, the tide will tell the truth"),
    "cove": Setting("cove", "the cove deck", "the captain's corner", "the deck", "Cuckoo, cuckoo, and every wave will hum"),
}

TOOLS = {
    "dice": Choice("dice", "dice", "a pair of dice", 3, 2, {"noise", "game"}),
    "tug": Choice("tug", "tug rope", "a tug rope", 2, 2, {"game"}),
    "cuckoo": Choice("cuckoo", "cuckoo lantern", "a cuckoo lantern", 3, 1, {"noise", "light"}),
}

PRIZES = {
    "map": Choice("map", "treasure map", "a treasure map", 0, 1, {"game"}),
    "rope": Choice("rope", "rope bundle", "a rope bundle", 0, 2, {"game"}),
    "shells": Choice("shells", "shell necklace", "a shell necklace", 0, 1, {"game"}),
}

RESPONSES = {
    "shield": Choice("shield", "shield the spark", "shielded the spark with a metal tray", 3, 3, {"safe"}),
    "smother": Choice("smother", "smother the spark", "smothered the spark with a thick cloth", 3, 2, {"safe"}),
    "stomp": Choice("stomp", "stomp it out", "stomped it out before it spread", 2, 2, {"safe"}),
    "water": Choice("water", "water bucket", "threw water over it", 1, 1, {"unsafe"}),
}

GIRL_NAMES = ["Mara", "Nina", "Lily", "Pia", "Tessa"]
BOY_NAMES = ["Finn", "Owen", "Eli", "Jasper", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate rhyme story world with tug, dice, and cuckoo.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--cousin")
    ap.add_argument("--cousin-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def explain_rejection(tool: Choice, prize: Choice) -> str:
    return f"(No story: {tool.label} does not make a useful hazard with {prize.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.prize and not hazard(TOOLS[args.tool], PRIZES[args.prize]):
        raise StoryError(explain_rejection(TOOLS[args.tool], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, prize = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    cousin_gender = args.cousin_gender or ("boy" if gender == "girl" else "girl")
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    cousin = args.cousin or rng.choice([n for n in (BOY_NAMES if cousin_gender == "boy" else GIRL_NAMES) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, child, gender, cousin, cousin_gender, parent, tool, prize, response)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], TOOLS[params.tool], PRIZES[params.prize], RESPONSES[params.response],
        params.child, params.child_gender, params.cousin, params.cousin_gender, params.parent,
        roll=2 if params.response != "water" else 4
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the words "tug", "dice", and "cuckoo".',
        f"Tell a rhyme-filled story where {f['child'].id} wants to use dice, but a cousin and a parent steer the crew to safety.",
        f'Write a short pirate story with an inner monologue beat and a cuckoo clock, ending with a safer choice.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, cousin, parent = f["child"], f["cousin"], f["parent"]
    tool, prize, response = f["tool"], f["prize"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {cousin.id}, with {parent.label_word} watching over the pirate game."),
        ("What did the children want to use?",
         f"{child.id} wanted to use the {tool.label} because the dark corner felt spooky."),
        ("What did the cuckoo clock add to the story?",
         f"It added a little rhythm and a reminder that time keeps moving, even during play. The cuckoo sound made the pirate scene feel playful and a bit magical."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How was the problem fixed?",
            f"{parent.label_word.capitalize()} {response.phrase}, and the scare stopped before it could spoil the game. Then the crew had a brighter, safer way to keep exploring."
        ))
    elif f["outcome"] == "lost":
        qa.append((
            "What happened when the plan went wrong?",
            f"The trouble grew bigger than the children could handle, so the game had to stop. They stepped away safely and learned to call a grown-up sooner."
        ))
    else:
        qa.append((
            "What was the safer choice?",
            f"They left the {tool.label} alone and kept tugging the rope instead. That let the pirate play continue without any spark."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is a dice game?", "A dice game is a game where you roll small cubes and hope for a lucky result."),
        ("What is a cuckoo clock?", "A cuckoo clock is a clock that makes a cuckoo sound to tell the time."),
        ("What is a tug rope?", "A tug rope is a rope you pull against someone or something in a game of strength."),
    ]
    return out


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={dict(meters)} memes={dict(memes)} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(T, P) :- tool(T), prize(P), noise(T), game(P).
valid(S, T, P) :- setting(S), tool(T), prize(P), hazard(T, P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "noise" in t.tags:
            lines.append(asp.fact("noise", tid))
        if "light" in t.tags:
            lines.append(asp.fact("light", tid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if "game" in p.tags:
            lines.append(asp.fact("game", pid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams("harbor", "Mara", "girl", "Finn", "boy", "mother", "dice", "map", "shield"),
    StoryParams("island", "Owen", "boy", "Lily", "girl", "father", "cuckoo", "rope", "smother"),
    StoryParams("cove", "Tessa", "girl", "Theo", "boy", "mother", "tug", "shells", "stomp"),
]


def generate_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, t, p in asp_valid_combos():
            print(f"  {s:8} {t:8} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.cousin}: {p.tool} near {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
